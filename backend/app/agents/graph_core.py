"""
Graph Core - StateGraph Principal do Jogo
GEM RPG ORBIS - LangGraph Architecture

Este é o CORE do sistema - o grafo de estados que orquestra
todo o fluxo do jogo.

Fluxo:
    ┌─────────────────────────────────────────────────────┐
    │                                                     │
    │   ┌──────────┐    ┌──────────┐    ┌───────────┐    │
    │   │ PLANNER  │───▶│ EXECUTOR │───▶│ VALIDATOR │    │
    │   └──────────┘    └──────────┘    └───────────┘    │
    │        ▲                               │           │
    │        │                               │           │
    │        └───────── (RETRY) ◀────────────┤           │
    │                                        │           │
    │                                   (SUCCESS)        │
    │                                        ▼           │
    │                                 ┌───────────┐      │
    │                                 │ NARRATOR  │      │
    │                                 └───────────┘      │
    │                                        │           │
    │                                        ▼           │
    │                                      END           │
    └─────────────────────────────────────────────────────┘

Features:
- PostgresSaver para checkpoints (time travel!)
- Nós como funções Python puras
- Routing condicional no Validator
"""

from typing import Dict, Any, Optional, Literal
from datetime import datetime
import asyncio
import sys

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# Importar AsyncPostgresSaver apenas se não for Windows
# Windows usa ProactorEventLoop que não é compatível com psycopg async
if sys.platform != "win32":
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    USE_POSTGRES_SAVER = True
else:
    USE_POSTGRES_SAVER = False

from app.agents.nodes.state import (
    AgentState,
    create_initial_state,
    PlayerContext,
    WorldContext,
    player_from_db,
    world_from_context
)
from app.agents.nodes.planner import planner_node
from app.agents.nodes.executor import executor_node
from app.agents.nodes.validator import validator_node, should_retry
from app.agents.nodes.narrator import narrator_node

from app.config import settings


# ==================== GRAPH BUILDER ====================

class GameGraph:
    """
    Gerenciador do grafo de jogo LangGraph.
    
    Encapsula:
    - Construção do StateGraph
    - Configuração do PostgresSaver
    - Execução de turnos
    - Time travel (undo/redo)
    """
    
    def __init__(self, gemini_client, db_connection_string: Optional[str] = None):
        """
        Inicializa o GameGraph.
        
        Args:
            gemini_client: Cliente Gemini para chamadas LLM
            db_connection_string: String de conexão PostgreSQL para checkpointer
        """
        self.gemini_client = gemini_client
        self.db_connection_string = db_connection_string or settings.async_database_url
        
        # Construir o grafo
        self._graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Constrói o StateGraph com nós e arestas."""
        
        # Criar builder do grafo
        builder = StateGraph(AgentState)
        
        # ========== ADICIONAR NÓS ==========
        
        # Wrapper para passar dependências aos nós
        async def planner_wrapper(state: AgentState) -> Dict[str, Any]:
            return await planner_node(state, self.gemini_client)
        
        async def executor_wrapper(state: AgentState) -> Dict[str, Any]:
            return await executor_node(state)
        
        async def validator_wrapper(state: AgentState) -> Dict[str, Any]:
            return await validator_node(state)
        
        async def narrator_wrapper(state: AgentState) -> Dict[str, Any]:
            return await narrator_node(state, self.gemini_client)
        
        # Adicionar nós ao grafo
        builder.add_node("planner", planner_wrapper)
        builder.add_node("executor", executor_wrapper)
        builder.add_node("validator", validator_wrapper)
        builder.add_node("narrator", narrator_wrapper)
        
        # ========== ADICIONAR ARESTAS ==========
        
        # START -> planner
        builder.add_edge(START, "planner")
        
        # planner -> executor
        builder.add_edge("planner", "executor")
        
        # executor -> validator
        builder.add_edge("executor", "validator")
        
        # validator -> (condicional) planner OU narrator
        builder.add_conditional_edges(
            "validator",
            should_retry,
            {
                "planner": "planner",
                "narrator": "narrator"
            }
        )
        
        # narrator -> END
        builder.add_edge("narrator", END)
        
        return builder
    
    async def run_turn(
        self,
        session_id: str,
        player_id: int,
        user_input: str,
        player_context: PlayerContext,
        world_context: WorldContext,
        turn_number: int = 1
    ) -> Dict[str, Any]:
        """
        Executa um turno completo do jogo.
        
        Args:
            session_id: ID único da sessão (para checkpoints)
            player_id: ID do jogador
            user_input: Input do usuário
            player_context: Contexto do jogador
            world_context: Contexto do mundo
            turn_number: Número do turno
            
        Returns:
            Estado final com narração e resultados
        """
        print(f"\n{'='*60}")
        print(f"[GAME GRAPH] Turno {turn_number} - Sessão {session_id}")
        print(f"[GAME GRAPH] Input: '{user_input[:50]}...'")
        print(f"{'='*60}\n")
        
        # Criar estado inicial
        initial_state = create_initial_state(
            session_id=session_id,
            player_id=player_id,
            user_input=user_input,
            player_context=player_context,
            world_context=world_context,
            turn_number=turn_number
        )
        
        # Configurar thread para checkpoint
        config = {
            "configurable": {
                "thread_id": session_id
            }
        }
        
        # Executar grafo com checkpointer apropriado
        return await self._run_with_checkpointer(initial_state, config, session_id, turn_number)
    
    async def _run_with_checkpointer(
        self,
        initial_state: AgentState,
        config: Dict[str, Any],
        session_id: str,
        turn_number: int
    ) -> Dict[str, Any]:
        """Executa o grafo com o checkpointer apropriado para a plataforma."""
        
        if USE_POSTGRES_SAVER:
            # Linux/Mac: usar PostgresSaver
            async with AsyncPostgresSaver.from_conn_string(self.db_connection_string) as checkpointer:
                await checkpointer.setup()
                return await self._execute_graph(
                    self._graph.compile(checkpointer=checkpointer),
                    initial_state, config, session_id, turn_number
                )
        else:
            # Windows: usar MemorySaver (checkpoints não persistem entre reinícios)
            if not hasattr(self, '_memory_saver'):
                self._memory_saver = MemorySaver()
            
            return await self._execute_graph(
                self._graph.compile(checkpointer=self._memory_saver),
                initial_state, config, session_id, turn_number
            )
    
    async def _execute_graph(
        self,
        compiled_graph,
        initial_state: AgentState,
        config: Dict[str, Any],
        session_id: str,
        turn_number: int
    ) -> Dict[str, Any]:
        """Executa o grafo compilado."""
        try:
            final_state = await compiled_graph.ainvoke(initial_state, config)
            
            # Usar repr() para evitar problemas de encoding no Windows
            narration_preview = final_state.get('narration', '')[:100].encode('ascii', 'replace').decode()
            print(f"\n[GAME GRAPH] Turno completo!")
            print(f"[GAME GRAPH] Narrativa: {narration_preview}...")
            
            return {
                "success": True,
                "session_id": session_id,
                "turn_number": turn_number,
                "narration": final_state.get("narration", ""),
                "action_summary": final_state.get("action_summary", ""),
                "action_result": final_state.get("action_result", {}),
                "validation": final_state.get("validation", {}),
                "validation_attempts": final_state.get("validation_attempts", 0),
                "messages": final_state.get("messages", []),
                "error": final_state.get("error")
            }
            
        except Exception as e:
            err_msg = str(e).encode('ascii', 'replace').decode()
            print(f"[GAME GRAPH] ERRO: {err_msg}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "session_id": session_id,
                "turn_number": turn_number,
                "error": str(e),
                "narration": "Algo deu errado no processamento da sua ação...",
                "action_summary": "Erro interno"
            }
    
    async def stream_turn(
        self,
        session_id: str,
        player_id: int,
        user_input: str,
        player_context: PlayerContext,
        world_context: WorldContext,
        turn_number: int = 1
    ):
        """
        Stream de um turno com eventos SSE.
        
        Yields eventos conforme cada nó do grafo executa:
        - planner: Quando a ação é planejada
        - executor: Quando a ação é executada
        - validator: Quando a validação ocorre
        - narrator: Chunks da narrativa conforme são gerados
        - done: Fim do turno
        
        Args:
            session_id: ID da sessão
            player_id: ID do jogador
            user_input: Input do usuário
            player_context: Contexto do jogador
            world_context: Contexto do mundo
            turn_number: Número do turno
            
        Yields:
            Dict com event type e data
        """
        import json
        
        initial_state = create_initial_state(
            session_id=session_id,
            player_id=player_id,
            user_input=user_input,
            player_context=player_context,
            world_context=world_context,
            turn_number=turn_number
        )
        
        config = {
            "configurable": {
                "thread_id": session_id
            }
        }
        
        # Compilar grafo
        if USE_POSTGRES_SAVER:
            async with AsyncPostgresSaver.from_conn_string(self.db_connection_string) as checkpointer:
                await checkpointer.setup()
                compiled_graph = self._graph.compile(checkpointer=checkpointer)
                
                async for event in self._stream_graph(compiled_graph, initial_state, config, session_id, turn_number):
                    yield event
        else:
            if not hasattr(self, '_memory_saver'):
                self._memory_saver = MemorySaver()
            
            compiled_graph = self._graph.compile(checkpointer=self._memory_saver)
            
            async for event in self._stream_graph(compiled_graph, initial_state, config, session_id, turn_number):
                yield event
    
    async def _stream_graph(
        self,
        compiled_graph,
        initial_state: AgentState,
        config: Dict[str, Any],
        session_id: str,
        turn_number: int
    ):
        """Stream interno do grafo."""
        import json
        
        try:
            last_state = None
            
            # astream_events fornece eventos granulares de cada nó
            async for event in compiled_graph.astream(initial_state, config, stream_mode="updates"):
                # event é um dict com o nome do nó e suas atualizações
                for node_name, updates in event.items():
                    # Yield evento SSE
                    if node_name == "planner":
                        planned = updates.get("planned_action", {})
                        yield {
                            "event": "planner",
                            "data": json.dumps({
                                "intent": planned.get("intent", "unknown") if planned else "unknown",
                                "target": planned.get("target_name") if planned else None
                            })
                        }
                    
                    elif node_name == "executor":
                        result = updates.get("action_result", {})
                        yield {
                            "event": "executor",
                            "data": json.dumps({
                                "success": result.get("success", False) if result else False,
                                "summary": updates.get("action_summary", "")
                            })
                        }
                    
                    elif node_name == "validator":
                        validation = updates.get("validation", {})
                        yield {
                            "event": "validator",
                            "data": json.dumps({
                                "status": validation.get("status", "unknown") if validation else "unknown",
                                "attempts": updates.get("validation_attempts", 0)
                            })
                        }
                    
                    elif node_name == "narrator":
                        narration = updates.get("narration", "")
                        # Stream a narrativa em chunks para efeito de digitação
                        if narration:
                            chunk_size = 50  # caracteres por chunk
                            for i in range(0, len(narration), chunk_size):
                                chunk = narration[i:i+chunk_size]
                                yield {
                                    "event": "narrator_chunk",
                                    "data": json.dumps({"text": chunk})
                                }
                    
                    last_state = updates
            
            # Evento final
            yield {
                "event": "done",
                "data": json.dumps({
                    "session_id": session_id,
                    "turn_number": turn_number,
                    "success": True
                })
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
    
    async def get_checkpoints(self, session_id: str) -> list:
        """
        Obtém todos os checkpoints de uma sessão.
        Útil para implementar undo/redo.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Lista de checkpoints
        """
        config = {"configurable": {"thread_id": session_id}}
        checkpoints = []
        
        if USE_POSTGRES_SAVER:
            async with AsyncPostgresSaver.from_conn_string(self.db_connection_string) as checkpointer:
                async for checkpoint in checkpointer.alist(config):
                    checkpoints.append({
                        "id": checkpoint.config.get("configurable", {}).get("checkpoint_id"),
                        "timestamp": checkpoint.metadata.get("created_at"),
                        "turn": checkpoint.metadata.get("turn_number"),
                        "step": checkpoint.metadata.get("step")
                    })
        else:
            # Windows: MemorySaver
            if hasattr(self, '_memory_saver'):
                # MemorySaver.list is sync, so we iterate
                for checkpoint in self._memory_saver.list(config):
                    checkpoints.append({
                        "id": checkpoint.config.get("configurable", {}).get("checkpoint_id"),
                        "timestamp": checkpoint.metadata.get("created_at"),
                        "turn": checkpoint.metadata.get("turn_number"),
                        "step": checkpoint.metadata.get("step")
                    })
        
        return checkpoints
    
    async def restore_checkpoint(
        self,
        session_id: str,
        checkpoint_id: str
    ) -> Dict[str, Any]:
        """
        Restaura um checkpoint específico (time travel).
        
        Args:
            session_id: ID da sessão
            checkpoint_id: ID do checkpoint a restaurar
            
        Returns:
            Estado restaurado
        """
        config = {
            "configurable": {
                "thread_id": session_id,
                "checkpoint_id": checkpoint_id
            }
        }
        
        try:
            if USE_POSTGRES_SAVER:
                async with AsyncPostgresSaver.from_conn_string(self.db_connection_string) as checkpointer:
                    checkpoint_tuple = await checkpointer.aget_tuple(config)
                    
                    if checkpoint_tuple:
                        state = checkpoint_tuple.checkpoint.get("channel_values", {})
                        return {
                            "success": True,
                            "checkpoint_id": checkpoint_id,
                            "narration": state.get("narration", ""),
                            "turn_number": state.get("turn_number", 0)
                        }
            else:
                # Windows: MemorySaver
                if hasattr(self, '_memory_saver'):
                    checkpoint_tuple = self._memory_saver.get_tuple(config)
                    if checkpoint_tuple:
                        state = checkpoint_tuple.checkpoint.get("channel_values", {})
                        return {
                            "success": True,
                            "checkpoint_id": checkpoint_id,
                            "narration": state.get("narration", ""),
                            "turn_number": state.get("turn_number", 0)
                        }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao restaurar checkpoint: {str(e)}"
            }
        
        return {
            "success": False,
            "error": f"Checkpoint {checkpoint_id} não encontrado"
        }
    
    async def undo_turn(self, session_id: str) -> Dict[str, Any]:
        """
        Desfaz o último turno (volta ao checkpoint anterior).
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Estado do turno anterior
        """
        checkpoints = await self.get_checkpoints(session_id)
        
        if len(checkpoints) < 2:
            return {
                "success": False,
                "error": "Não há turno anterior para desfazer"
            }
        
        # Pegar penúltimo checkpoint
        previous_checkpoint = checkpoints[-2]
        
        return await self.restore_checkpoint(
            session_id,
            previous_checkpoint["id"]
        )


# ==================== FACTORY FUNCTION ====================

def create_game_graph(gemini_client, db_connection_string: Optional[str] = None) -> GameGraph:
    """
    Factory function para criar GameGraph.
    
    Args:
        gemini_client: Cliente Gemini
        db_connection_string: String de conexão PostgreSQL
        
    Returns:
        GameGraph configurado
    """
    return GameGraph(gemini_client, db_connection_string)


# ==================== SIMPLE GRAPH (SEM CHECKPOINTER) ====================

class SimpleGameGraph:
    """
    Versão simplificada do GameGraph sem checkpointer.
    Útil para testes ou quando não precisa de persistência.
    """
    
    def __init__(self, gemini_client):
        self.gemini_client = gemini_client
        self._graph = self._build_graph()
        self._compiled_graph = None
    
    def _build_graph(self) -> StateGraph:
        """Constrói o grafo."""
        builder = StateGraph(AgentState)
        
        async def planner_wrapper(state: AgentState) -> Dict[str, Any]:
            return await planner_node(state, self.gemini_client)
        
        async def executor_wrapper(state: AgentState) -> Dict[str, Any]:
            return await executor_node(state)
        
        async def validator_wrapper(state: AgentState) -> Dict[str, Any]:
            return await validator_node(state)
        
        async def narrator_wrapper(state: AgentState) -> Dict[str, Any]:
            return await narrator_node(state, self.gemini_client)
        
        builder.add_node("planner", planner_wrapper)
        builder.add_node("executor", executor_wrapper)
        builder.add_node("validator", validator_wrapper)
        builder.add_node("narrator", narrator_wrapper)
        
        builder.add_edge(START, "planner")
        builder.add_edge("planner", "executor")
        builder.add_edge("executor", "validator")
        builder.add_conditional_edges(
            "validator",
            should_retry,
            {"planner": "planner", "narrator": "narrator"}
        )
        builder.add_edge("narrator", END)
        
        return builder
    
    def compile(self) -> Any:
        """Compila sem checkpointer."""
        if self._compiled_graph is None:
            self._compiled_graph = self._graph.compile()
        return self._compiled_graph
    
    async def run_turn(
        self,
        user_input: str,
        player_context: PlayerContext,
        world_context: WorldContext,
        session_id: str = "test",
        player_id: int = 1,
        turn_number: int = 1
    ) -> Dict[str, Any]:
        """Executa um turno sem persistência."""
        
        initial_state = create_initial_state(
            session_id=session_id,
            player_id=player_id,
            user_input=user_input,
            player_context=player_context,
            world_context=world_context,
            turn_number=turn_number
        )
        
        graph = self.compile()
        
        final_state = await graph.ainvoke(initial_state)
        
        return {
            "success": True,
            "narration": final_state.get("narration", ""),
            "action_summary": final_state.get("action_summary", ""),
            "action_result": final_state.get("action_result", {}),
            "validation_attempts": final_state.get("validation_attempts", 0)
        }
