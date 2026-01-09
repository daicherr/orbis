from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
from sqlmodel.ext.asyncio.session import AsyncSession
from contextlib import asynccontextmanager

from app.database.db_connection import engine
from app.database.init_db import seed_initial_npcs, ensure_pgvector_extension
from sqlmodel import SQLModel
from app.core.combat_engine import CombatEngine
from app.core.constitution_effects import ConstitutionEffects
from app.database.models.player import Player
from app.database.models.memory import Memory
from app.database.models.logs import GameLog
from app.database.repositories.player_repo import PlayerRepository
from app.database.repositories.npc_repo import NpcRepository
from app.database.repositories.hybrid_search import HybridSearchRepository
from app.database.repositories.gamelog_repo import GameLogRepository
from app.database.repositories.world_event_repo import WorldEventRepository
from app.database.repositories.faction_repo import FactionRepository
from app.database.repositories.economy_repo import GlobalEconomyRepository
from app.services.gemini_client import GeminiClient
from app.services.embedding_service import EmbeddingService, embedding_service
from app.services.lore_cache import lore_cache
from app.agents.narrator import Narrator
from app.agents.referee import Referee
from app.agents.director import Director
from app.agents.stylizer import Stylizer
from app.agents.scribe import Scribe
from app.agents.architect import Architect
from app.agents.villains.profiler import Profiler
from app.agents.graph_core import SimpleGameGraph, GameGraph
from app.agents.nodes.state import player_from_db, world_from_context, create_initial_state
from app.core.world_sim import WorldSimulator
from sqlalchemy import text
from app.core.simulation.daily_tick import DailyTickSimulator
from app.services.quest_service import quest_service
from app.core.chronos import world_clock

# Armazenamento simples para as instâncias dos nossos serviços
app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup na inicialização
    print("Iniciando a aplicação e os serviços...")
    
    # Sprint 14: Pré-carregar lore cache (rápido, ~10ms)
    lore_cache.load()
    
    # Garante pgvector e cria tabelas (se não existirem) com retry
    for attempt in range(10):
        try:
            await ensure_pgvector_extension()
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
            break
        except Exception as e:
            print(f"DB init tentativa {attempt+1}/10 falhou: {e}")
            await asyncio.sleep(1.5)
    
    # Popula o banco de dados com NPCs iniciais
    await seed_initial_npcs()

    # Inicializar serviços
    try:
        print("[DEBUG] Inicializando GeminiClient...")
        gemini_client = GeminiClient()
        app_state["gemini_client"] = gemini_client
        print("[DEBUG] Inicializando Narrator...")
        app_state["narrator"] = Narrator(gemini_client=gemini_client, lore_files_path="./lore_library")
        print("[DEBUG] Inicializando Referee...")
        app_state["referee"] = Referee(gemini_client=gemini_client)
        print("[DEBUG] Inicializando Stylizer...")
        app_state["stylizer"] = Stylizer(gemini_client=gemini_client)
        print("[DEBUG] Inicializando Scribe...")
        app_state["scribe"] = Scribe(gemini_client=gemini_client)
        print("[DEBUG] Inicializando Architect...")
        app_state["architect"] = Architect(gemini_client=gemini_client)
        print("[DEBUG] Inicializando Profiler...")
        app_state["profiler"] = Profiler()
        
        # Inicializar WorldSimulator (coordena Strategist, Diplomat, GossipMonger)
        # Precisaremos passar os repositórios mais tarde nas chamadas
        print("[DEBUG] Inicializando WorldSimulator...")
        app_state["world_simulator"] = WorldSimulator(gemini_client=gemini_client)
        
        # Inicializar GameGraph (LangGraph v2) como singleton
        print("[DEBUG] Inicializando GameGraph...")
        app_state["game_graph"] = GameGraph(gemini_client=gemini_client)
        
        print("Serviços de IA inicializados (incluindo WorldSimulator e GameGraph).")
    except Exception as e:
        print(f"ERRO CRÍTICO: Falha ao inicializar serviços. Detalhes: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise  # Re-raise para forçar o app a não iniciar
    
    print("[DEBUG] Lifespan startup completo, entrando em yield...")
    yield
    print("[DEBUG] Lifespan shutdown iniciado...")
    
    # Cleanup no desligamento
    print("Encerrando a aplicação...")
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

# --- CORS (permitir frontend local) ---
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- Gestão de Dependências ---

async def get_session():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session

# Alias para compatibilidade com Sprint 6
get_async_session = get_session

async def get_director(session: AsyncSession = Depends(get_session)) -> Director:
    player_repo = PlayerRepository(session)
    npc_repo = NpcRepository(session)
    
    # Initialize GameLogRepository with EmbeddingService
    embedding_service = EmbeddingService()
    gamelog_repo = GameLogRepository(session, embedding_service=embedding_service)
    
    # Initialize HybridSearchRepository (Memory)
    memory_repo = HybridSearchRepository(session)
    
    director = Director(
        narrator=app_state["narrator"],
        referee=app_state["referee"],
        combat_engine=CombatEngine(),
        player_repo=player_repo,
        npc_repo=npc_repo,
        scribe=app_state["scribe"],
        architect=app_state["architect"],
        profiler=app_state["profiler"],
        gamelog_repo=gamelog_repo,
        memory_repo=memory_repo
    )
    return director

async def get_stylizer() -> Stylizer:
    return app_state["stylizer"]

def get_hybrid_repo(session: AsyncSession) -> HybridSearchRepository:
    return HybridSearchRepository(session)

# --- Endpoints da API ---

@app.get("/")
def read_root():
    return {"message": "Welcome to Gem RPG Orbis API"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/health/db")
async def health_db():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}


@app.post("/system/warmup")
async def warmup_system():
    """
    Sprint 14: Endpoint de warmup para pré-carregar serviços pesados.
    
    Útil para:
    - Reduzir latência da primeira request
    - Pré-aquecer modelos de IA e embeddings
    - Health check mais completo
    
    Chamado pelo frontend no load inicial.
    """
    import time
    results = {}
    start_total = time.time()
    
    # 1. Lore cache
    start = time.time()
    if not lore_cache.is_loaded():
        lore_cache.load()
    results["lore_cache"] = {
        "status": "ok" if lore_cache.is_loaded() else "error",
        "time_ms": int((time.time() - start) * 1000)
    }
    
    # 2. Embedding model (mais lento)
    start = time.time()
    try:
        embedding_service.preload()
        results["embedding_model"] = {
            "status": "ok",
            "model_loaded": embedding_service.is_loaded(),
            "time_ms": int((time.time() - start) * 1000)
        }
    except Exception as e:
        results["embedding_model"] = {
            "status": "error",
            "error": str(e),
            "time_ms": int((time.time() - start) * 1000)
        }
    
    # 3. GeminiClient check
    gemini = app_state.get("gemini_client")
    results["gemini_client"] = {
        "status": "ok" if gemini else "not_initialized",
        "ai_enabled": gemini.client is not None if gemini else False
    }
    
    # 4. Database check
    start = time.time()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        results["database"] = {
            "status": "ok",
            "time_ms": int((time.time() - start) * 1000)
        }
    except Exception as e:
        results["database"] = {
            "status": "error",
            "error": str(e)
        }
    
    total_time = int((time.time() - start_total) * 1000)
    
    return {
        "status": "ok",
        "total_time_ms": total_time,
        "services": results
    }


@app.get("/system/status")
async def system_status():
    """
    Sprint 14: Status rápido do sistema (sem warmup).
    """
    return {
        "status": "ok",
        "services": {
            "lore_cache": lore_cache.is_loaded(),
            "embedding_model": embedding_service.is_loaded(),
            "gemini_client": app_state.get("gemini_client") is not None,
            "narrator": app_state.get("narrator") is not None,
            "world_simulator": app_state.get("world_simulator") is not None
        }
    }


@app.post("/player/create")
async def create_player(name: str, session: AsyncSession = Depends(get_session)) -> Player:
    player_repo = PlayerRepository(session)
    player = await player_repo.create(name=name)
    return player

# [SPRINT 5.1] GET Player by ID (para CharacterSheet)
@app.get("/player/{player_id}", response_model=Player)
async def get_player(player_id: int, session: AsyncSession = Depends(get_session)):
    """
    Retorna os dados completos de um player (usado pelo CharacterSheet UI).
    """
    player_repo = PlayerRepository(session)
    player = await player_repo.get_by_id(player_id)
    
    if not player:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    
    return player

# [NEW] GET Player Inventory
@app.get("/player/{player_id}/inventory")
async def get_player_inventory(player_id: int, session: AsyncSession = Depends(get_session)):
    """
    Retorna o inventário do jogador.
    """
    player_repo = PlayerRepository(session)
    player = await player_repo.get_by_id(player_id)
    
    if not player:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    
    return player.inventory

# [NEW] GET All Players (para seleção de personagens)
@app.get("/player/list/all", response_model=list[Player])
async def list_all_players(session: AsyncSession = Depends(get_session)):
    """
    Lista todos os personagens criados.
    """
    player_repo = PlayerRepository(session)
    players = await player_repo.get_all()
    return players

# [NEW] DELETE Player (para deletar personagem)
@app.delete("/player/{player_id}")
async def delete_player(player_id: int, session: AsyncSession = Depends(get_session)):
    """
    Deleta um personagem permanentemente.
    """
    player_repo = PlayerRepository(session)
    player = await player_repo.get_by_id(player_id)
    
    if not player:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    
    await player_repo.delete(player_id)
    return {"success": True, "message": f"Personagem '{player.name}' deletado"}

# [NEW] GET Player History - Lista histórico de turnos
@app.get("/player/{player_id}/history")
async def get_player_history(
    player_id: int, 
    limit: int = 5, 
    session: AsyncSession = Depends(get_session)
):
    """
    Retorna o histórico de turnos do jogador (para verificar persistência).
    """
    from app.database.repositories.gamelog_repo import GameLogRepository
    from app.services.embedding_service import EmbeddingService
    
    gamelog_repo = GameLogRepository(session, embedding_service=EmbeddingService())
    logs = await gamelog_repo.get_recent_turns(player_id, limit=limit)
    
    return [
        {
            "id": log.id,
            "turn_number": log.turn_number,
            "player_input": log.player_input[:100] + "..." if len(log.player_input) > 100 else log.player_input,
            "scene_description": log.scene_description,
            "action_result": log.action_result,
            "location": log.location,
            "npcs_present": log.npcs_present,
            "world_time": log.world_time,
            "created_at": str(log.created_at) if log.created_at else None,
        }
        for log in logs
    ]

@app.post("/game/turn")
async def game_turn(player_id: int, player_input: str, director: Director = Depends(get_director)):
    # `Director` é injetado por dependência e construído on-demand.
    # Se serviços base não estiverem prontos, a dependência levantará erro.
    result = await director.process_player_turn(player_id=player_id, player_input=player_input)
    
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result.get("error"))
        
    return result


# ============================================================
# V2 - LangGraph Endpoints
# ============================================================

@app.post("/v2/game/turn")
async def game_turn_v2(
    player_id: int,
    player_input: str,
    session_id: str = "default",
    session: AsyncSession = Depends(get_session)
):
    """
    V2: Processa um turno usando a arquitetura LangGraph.
    
    Flow: Planner → Executor → Validator (loop) → Narrator
    
    Args:
        player_id: ID do jogador
        player_input: Ação do jogador em linguagem natural
        session_id: ID da sessão para persistência de estado
    
    Returns:
        Dict com narrativa, estado do jogador e metadados
    """
    # Obter repositórios
    player_repo = PlayerRepository(session)
    npc_repo = NpcRepository(session)
    gamelog_repo = GameLogRepository(session)
    
    # Carregar jogador
    player = await player_repo.get_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    await session.refresh(player)
    
    # Construir contextos
    player_context = player_from_db(player)
    
    # Buscar NPCs na localização
    current_location = player.current_location or "Floresta Assombrada"
    npcs_in_scene = await npc_repo.get_by_location(current_location)
    
    # Obter turno atual
    recent_logs = await gamelog_repo.get_recent_turns(player_id, limit=1)
    turn_number = (recent_logs[0].turn_number + 1) if recent_logs else 1
    
    # Construir world context - passando NPCs do banco diretamente
    world_context = world_from_context(
        location=current_location,
        npcs=npcs_in_scene,  # Objetos NPC do banco
        time_of_day=world_clock.get_time_of_day(),
        weather="clear"
    )
    
    # Obter gemini client
    gemini_client = app_state.get("gemini_client")
    if not gemini_client:
        raise HTTPException(status_code=503, detail="Gemini client not initialized")
    
    # Criar grafo e executar turno
    try:
        graph = SimpleGameGraph(gemini_client=gemini_client)
        
        result = await graph.run_turn(
            session_id=session_id,
            player_id=player_id,
            user_input=player_input,
            player_context=player_context,
            world_context=world_context,
            turn_number=turn_number
        )
        
        # Salvar no game log
        game_log = GameLog(
            player_id=player_id,
            turn_number=turn_number,
            player_input=player_input,
            scene_description=result.get("narration", ""),
            action_taken=result.get("action_summary", "unknown"),
            action_successful=result.get("success", False),
            location=current_location,
            npcs_present=[npc.name for npc in npcs_in_scene],
            world_time=world_clock.get_current_time_str()
        )
        session.add(game_log)
        await session.commit()
        
        return {
            "success": True,
            "turn_number": turn_number,
            "narrative": result.get("narration", ""),
            "action": result.get("action_result", {}),
            "action_summary": result.get("action_summary", ""),
            "player_state": {
                "hp": player.current_hp,
                "yuan_qi": player.yuan_qi,
                "gold": player.gold,
                "location": current_location
            },
            "validation_attempts": result.get("validation_attempts", 0),
            "graph_version": "v2-langgraph"
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Graph execution error: {str(e)}")


@app.post("/v2/game/turn/persistent")
async def game_turn_v2_persistent(
    player_id: int,
    player_input: str,
    session_id: str = "default",
    session: AsyncSession = Depends(get_session)
):
    """
    V2 Persistente: Turno com checkpoints PostgreSQL.
    
    Habilita time-travel: undo/redo de turnos.
    Usa GameGraph com AsyncPostgresSaver.
    """
    player_repo = PlayerRepository(session)
    npc_repo = NpcRepository(session)
    gamelog_repo = GameLogRepository(session)
    
    player = await player_repo.get_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    await session.refresh(player)
    
    player_context = player_from_db(player)
    current_location = player.current_location or "Floresta Assombrada"
    npcs_in_scene = await npc_repo.get_by_location(current_location)
    
    recent_logs = await gamelog_repo.get_recent_turns(player_id, limit=1)
    turn_number = (recent_logs[0].turn_number + 1) if recent_logs else 1
    
    world_context = world_from_context(
        location=current_location,
        npcs=npcs_in_scene,
        time_of_day=world_clock.get_time_of_day(),
        weather="clear"
    )
    
    game_graph = app_state.get("game_graph")
    if not game_graph:
        raise HTTPException(status_code=503, detail="GameGraph not initialized")
    
    try:
        result = await game_graph.run_turn(
            session_id=session_id,
            player_id=player_id,
            user_input=player_input,
            player_context=player_context,
            world_context=world_context,
            turn_number=turn_number
        )
        
        # Salvar no game log
        game_log = GameLog(
            player_id=player_id,
            turn_number=turn_number,
            player_input=player_input,
            scene_description=result.get("narration", ""),
            action_taken=result.get("action_summary", "unknown"),
            action_successful=result.get("success", False),
            location=current_location,
            npcs_present=[npc.name for npc in npcs_in_scene],
            world_time=world_clock.get_current_time_str()
        )
        session.add(game_log)
        await session.commit()
        
        return {
            "success": True,
            "turn_number": turn_number,
            "narrative": result.get("narration", ""),
            "action": result.get("action_result", {}),
            "action_summary": result.get("action_summary", ""),
            "player_state": {
                "hp": player.current_hp,
                "yuan_qi": player.yuan_qi,
                "gold": player.gold,
                "location": current_location
            },
            "validation_attempts": result.get("validation_attempts", 0),
            "graph_version": "v2-langgraph-persistent",
            "session_id": session_id
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Graph execution error: {str(e)}")


@app.post("/v2/game/turn/stream")
async def game_turn_stream_v2(
    player_id: int,
    player_input: str,
    session_id: str = "default"
):
    """
    V2 Streaming: Turno com Server-Sent Events.
    
    Retorna eventos SSE conforme o grafo executa:
    - event: planner - Ação planejada
    - event: executor - Resultado da execução
    - event: validator - Status da validação
    - event: narrator_chunk - Chunks da narrativa (efeito de digitação)
    - event: done - Turno completo
    - event: error - Se houver erro
    
    Exemplo de consumo JavaScript:
    ```javascript
    const evtSource = new EventSource('/v2/game/turn/stream?player_id=1&player_input=...');
    evtSource.addEventListener('narrator_chunk', (e) => {
        const data = JSON.parse(e.data);
        appendToNarrative(data.text);
    });
    ```
    """
    import json
    
    # Usar sessão interna para evitar problemas com lifecycle do request
    async with AsyncSession(engine) as session:
        player_repo = PlayerRepository(session)
        npc_repo = NpcRepository(session)
        gamelog_repo = GameLogRepository(session)
        
        player = await player_repo.get_by_id(player_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        await session.refresh(player)
        
        player_context = player_from_db(player)
        current_location = player.current_location or "Floresta Assombrada"
        npcs_in_scene = await npc_repo.get_by_location(current_location)
        
        recent_logs = await gamelog_repo.get_recent_turns(player_id, limit=1)
        turn_number = (recent_logs[0].turn_number + 1) if recent_logs else 1
        
        world_context = world_from_context(
            location=current_location,
            npcs=npcs_in_scene,
            time_of_day=world_clock.get_time_of_day(),
            weather="clear"
        )
        
        # Capturar NPC names para log (antes de fechar session)
        npc_names = [npc.name for npc in npcs_in_scene]
    
    game_graph = app_state.get("game_graph")
    if not game_graph:
        raise HTTPException(status_code=503, detail="GameGraph not initialized")
    
    async def event_generator():
        """Gera eventos SSE."""
        full_narration = ""
        
        async for event in game_graph.stream_turn(
            session_id=session_id,
            player_id=player_id,
            user_input=player_input,
            player_context=player_context,
            world_context=world_context,
            turn_number=turn_number
        ):
            event_type = event.get("event", "message")
            event_data = event.get("data", "{}")
            
            # Acumular narrativa para salvar no log
            if event_type == "narrator_chunk":
                data = json.loads(event_data)
                full_narration += data.get("text", "")
            
            # Formato SSE: event: <type>\ndata: <json>\n\n
            yield f"event: {event_type}\ndata: {event_data}\n\n"
        
        # Salvar no game log após streaming completo (nova sessão)
        try:
            async with AsyncSession(engine) as log_session:
                game_log = GameLog(
                    player_id=player_id,
                    turn_number=turn_number,
                    player_input=player_input,
                    scene_description=full_narration,
                    action_taken="stream",
                    action_successful=True,
                    location=current_location,
                    npcs_present=npc_names,
                    world_time=world_clock.get_current_time_str()
                )
                log_session.add(game_log)
                await log_session.commit()
        except Exception as e:
            print(f"[SSE] Erro ao salvar log: {e}")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/v2/game/undo")
async def game_undo_v2(
    session_id: str = "default"
):
    """
    V2: Desfaz o último turno (time travel).
    
    Restaura o checkpoint anterior da sessão.
    """
    game_graph = app_state.get("game_graph")
    if not game_graph:
        raise HTTPException(status_code=503, detail="GameGraph not initialized")
    
    try:
        result = await game_graph.undo_turn(session_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Undo failed"))
        
        return {
            "success": True,
            "message": "Turno desfeito com sucesso",
            "checkpoint_id": result.get("checkpoint_id"),
            "restored_state": result.get("state", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Undo error: {str(e)}")


@app.get("/v2/game/checkpoints/{session_id}")
async def get_checkpoints_v2(session_id: str):
    """
    V2: Lista todos os checkpoints de uma sessão.
    
    Útil para implementar histórico de turnos.
    """
    game_graph = app_state.get("game_graph")
    if not game_graph:
        raise HTTPException(status_code=503, detail="GameGraph not initialized")
    
    try:
        checkpoints = await game_graph.get_checkpoints(session_id)
        
        return {
            "session_id": session_id,
            "checkpoints": checkpoints,
            "count": len(checkpoints)
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching checkpoints: {str(e)}")


@app.post("/game/turn/stream")
async def game_turn_stream(
    player_id: int, 
    player_input: str, 
    session: AsyncSession = Depends(get_session)
):
    """
    Sprint 13: Endpoint de streaming SSE para resposta narrativa.
    
    Retorna Server-Sent Events com chunks da narrativa conforme são gerados.
    Isso reduz a latência percebida pelo usuário.
    
    Eventos SSE:
    - event: scene_chunk - Chunks da narrativa
    - event: metadata - Informações do turno (player_state, npcs, etc)
    - event: done - Sinaliza fim do streaming
    """
    import json
    
    # Obter serviços necessários
    narrator = app_state.get("narrator")
    referee = app_state.get("referee")
    
    if not narrator:
        raise HTTPException(status_code=503, detail="Narrator not initialized")
    
    # Obter player e contexto
    player_repo = PlayerRepository(session)
    npc_repo = NpcRepository(session)
    gamelog_repo = GameLogRepository(session)
    
    player = await player_repo.get_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    await session.refresh(player)
    
    current_location = player.current_location or "Floresta Assombrada"
    npcs_in_scene = await npc_repo.get_by_location(current_location)
    
    # Buscar narração anterior para contexto
    previous_narration = ""
    is_first_scene = False
    recent_turns = await gamelog_repo.get_recent_turns(player_id, limit=1)
    if recent_turns:
        previous_narration = recent_turns[-1].scene_description
    else:
        is_first_scene = True
    
    # Preparar memórias
    memory_repo = HybridSearchRepository(session)
    
    async def event_generator():
        """Gera eventos SSE com a narrativa em streaming."""
        try:
            # Primeiro, envia metadados do turno
            metadata = {
                "player_state": {
                    "id": player.id,
                    "name": player.name,
                    "current_location": current_location,
                    "current_hp": player.current_hp,
                    "max_hp": player.max_hp,
                },
                "npcs_in_scene": [
                    {"id": npc.id, "name": npc.name, "emotional_state": npc.emotional_state}
                    for npc in npcs_in_scene
                ],
                "world_time": world_clock.get_current_datetime().isoformat()
            }
            yield f"event: metadata\ndata: {json.dumps(metadata)}\n\n"
            
            # Stream da narrativa
            full_scene = ""
            async for chunk in narrator.generate_scene_stream(
                player=player,
                location=current_location,
                npcs_in_scene=npcs_in_scene,
                player_last_action=player_input,
                previous_narration=previous_narration,
                memory_repo=memory_repo,
                is_first_scene=is_first_scene
            ):
                full_scene += chunk
                # Envia cada chunk como evento SSE
                yield f"event: scene_chunk\ndata: {json.dumps({'text': chunk})}\n\n"
            
            # Salvar no game log (após terminar streaming)
            try:
                turn_number = len(recent_turns) + 1 if recent_turns else 1
                await gamelog_repo.create_log(
                    player_id=player_id,
                    turn_number=turn_number,
                    player_input=player_input,
                    scene_description=full_scene,
                    action_result="",
                    location=current_location,
                    npcs_present=[npc.name for npc in npcs_in_scene],
                    world_time=world_clock.get_current_datetime().isoformat()
                )
            except Exception as e:
                print(f"[WARN] Erro ao salvar log: {e}")
            
            # Sinaliza fim do streaming
            yield f"event: done\ndata: {json.dumps({'success': True})}\n\n"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Desabilita buffering do nginx
        }
    )


# --- NPC Endpoints ---
@app.get("/npc/list/all")
async def list_all_npcs(session: AsyncSession = Depends(get_session)):
    """Retorna todos os NPCs do banco de dados."""
    npc_repo = NpcRepository(session)
    npcs = await npc_repo.get_all()
    return [
        {
            "id": npc.id,
            "name": npc.name,
            "rank": npc.rank,
            "current_hp": npc.current_hp,
            "max_hp": npc.max_hp,
            "current_location": npc.current_location,
            "emotional_state": npc.emotional_state,
            "personality_traits": npc.personality_traits,
        }
        for npc in npcs
    ]

@app.post("/npc/{npc_id}/observe")
async def observe_npc(
    npc_id: int, 
    session: AsyncSession = Depends(get_session),
    stylizer: Stylizer = Depends(get_stylizer)
):
    npc_repo = NpcRepository(session)
    npc = await npc_repo.get_by_id(npc_id)
    if not npc:
        raise HTTPException(status_code=404, detail="NPC not found")
        
    description = stylizer.generate_npc_description(npc)
    return {"description": description}

@app.post("/npc/{npc_id}/memory")
async def add_npc_memory(
    npc_id: int,
    content: str,
    session: AsyncSession = Depends(get_session),
):
    repo = HybridSearchRepository(session)
    mem = await repo.add_memory(npc_id=npc_id, content=content, embedding_dim=128)
    return {"id": mem.id, "npc_id": mem.npc_id, "content": mem.content}

@app.get("/npc/{npc_id}/memories")
async def search_npc_memories(
    npc_id: int,
    q: str,
    limit: int = 5,
    session: AsyncSession = Depends(get_session),
):
    repo = HybridSearchRepository(session)
    results = await repo.find_relevant_memories(npc_id=npc_id, query_text=q, limit=limit)
    return {"npc_id": npc_id, "query": q, "results": results}

@app.post("/simulation/tick")
async def simulation_tick(session: AsyncSession = Depends(get_session)):
    """
    Roda uma simulação completa do mundo:
    - Strategist move vilões hostis
    - Diplomat gerencia relações de facção
    - GossipMonger espalha rumores
    - DailyTickSimulator atualiza economia, facções e ecologia
    """
    from app.database.repositories.faction_repo import FactionRepository
    from app.database.repositories.economy_repo import GlobalEconomyRepository
    
    try:
        npc_repo = NpcRepository(session)
        player_repo = PlayerRepository(session)
        faction_repo = FactionRepository(session)
        economy_repo = GlobalEconomyRepository(session)
        event_repo = WorldEventRepository(session)
        
        results = {
            "world_sim": None,
            "daily_sim": None
        }
        
        # WorldSimulator (Strategist, Diplomat, GossipMonger)
        world_sim = app_state.get("world_simulator")
        if world_sim:
            try:
                await world_sim.run_simulation_tick(npc_repo, player_repo)
                results["world_sim"] = "executed"
            except Exception as e:
                results["world_sim"] = f"error: {str(e)}"
        else:
            results["world_sim"] = "not_initialized"
        
        # DailyTickSimulator completo (Economia, Facções, Ecologia, Linhagem)
        daily_sim = DailyTickSimulator(
            npc_repo=npc_repo,
            faction_repo=faction_repo,
            economy_repo=economy_repo,
            world_event_repo=event_repo
        )
        
        report = await daily_sim.run_daily_simulation(current_turn=world_clock.get_current_turn())
        results["daily_sim"] = {
            "turn": report.get("turn"),
            "total_events": len(report.get("events", [])),
            "faction_events": len(report.get("faction_events", [])),
            "economy_changes": len(report.get("economy_changes", []))
        }
        
        return {
            "status": "ok", 
            "message": "World simulation executed (villains, diplomacy, rumors, economy, factions)",
            "results": results
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/world/time")
async def get_world_time():
    """
    Retorna o tempo atual do mundo (Chronos)
    """
    from app.core.chronos import world_clock
    dt = world_clock.get_current_datetime()
    time_of_day = world_clock.get_time_of_day()
    season = world_clock.get_season()
    
    return {
        "datetime": dt.isoformat(),  # Adicionado para compatibilidade com testes
        "day": dt.day,
        "month": dt.month,
        "year": dt.year,
        "hour": dt.hour,
        "minute": dt.minute,
        "time_of_day": time_of_day,
        "season": season,
        "timestamp": dt.isoformat()
    }


@app.get("/world/factions")
async def get_world_factions(session: AsyncSession = Depends(get_session)):
    """Retorna todas as facções do mundo."""
    try:
        from app.database.repositories.faction_repo import FactionRepository
        faction_repo = FactionRepository(session)
        factions = await faction_repo.get_all()
        return [
            {
                "name": f.name,
                "territory": f.territory,
                "power": f.power,
                "wealth": f.wealth,
                "influence": f.influence,
                "relations": f.relations
            }
            for f in factions
        ]
    except Exception as e:
        print(f"[ERROR] /world/factions: {e}")
        # Retorna lista vazia se não há facções ou erro
        return []


@app.get("/world/economy")
async def get_world_economy(session: AsyncSession = Depends(get_session)):
    """Retorna estado da economia global."""
    try:
        from app.database.repositories.economy_repo import GlobalEconomyRepository
        repo = GlobalEconomyRepository(session)
        economy = await repo.get_latest()
        if not economy:
            return {"prices": {}, "trends": {}, "supply": {}, "demand": {}}
        return {
            "prices": economy.prices,
            "trends": economy.trends,
            "supply": economy.supply,
            "demand": economy.demand
        }
    except Exception as e:
        print(f"[ERROR] /world/economy: {e}")
        return {"prices": {}, "trends": {}, "supply": {}, "demand": {}}


@app.get("/locations/all")
async def get_all_locations():
    """Retorna todas as locations dinâmicas registradas."""
    try:
        from app.core.location_manager import location_manager
        locations = location_manager.get_all_locations()
        return [
            {
                "id": loc.id,
                "name": loc.name,
                "description": loc.description,
                "location_type": loc.location_type,
                "danger_level": loc.danger_level,
                "resources": loc.resources
            }
            for loc in locations
        ]
    except Exception as e:
        print(f"[ERROR] /locations/all: {e}")
        return []


# --- Character Creation Endpoints (Session Zero) ---

from pydantic import BaseModel
from typing import List, Optional

class SessionZeroRequest(BaseModel):
    name: str
    constitution: str
    origin_location: str

class SessionZeroResponse(BaseModel):
    questions: List[str]

class CreateCharacterRequest(BaseModel):
    name: str
    appearance: Optional[str] = None
    constitution: str
    origin_location: str
    session_zero_answers: List[str]

@app.post("/character/session-zero", response_model=SessionZeroResponse)
async def generate_session_zero_questions(
    request: SessionZeroRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Gera 3-5 perguntas personalizadas baseadas no nome, constituição e origem do personagem.
    O Architect usa Gemini para criar perguntas contextuais.
    """
    architect = app_state.get("architect")
    if not architect:
        raise HTTPException(status_code=500, detail="Architect service not available")
    
    # PERGUNTAS OBRIGATÓRIAS - Definem contexto inicial e primeira cena
    # Estas perguntas são SEMPRE feitas, não são geradas por IA
    mandatory_questions = [
        "Descreva o momento exato onde sua jornada começa. O que está acontecendo ao seu redor agora?",
        "Onde é seu refúgio? Descreva o lugar que você considera 'lar' ou onde se sente seguro.",
        "Quem é a pessoa mais importante na sua vida neste momento? Descreva ela brevemente."
    ]
    
    # Prompt para Gemini gerar 2 perguntas ADICIONAIS personalizadas
    prompt = f"""
Você é o Mestre de um RPG de cultivação chamado Códice Triluna.
Um novo jogador está criando seu personagem:
- Nome: {request.name}
- Constituição: {request.constitution}
- Local de Origem: {request.origin_location}

Gere EXATAMENTE 2 perguntas adicionais profundas e pessoais para entender a motivação desse personagem.
As perguntas devem ser específicas ao contexto (constituição e origem).
NÃO pergunte sobre local de início, lar ou pessoa importante (já foram perguntados).

Foque em:
- Motivações e objetivos
- Medos e conflitos internos
- Eventos traumáticos do passado

Formato: Retorne apenas as 2 perguntas, uma por linha, sem numeração.
"""
    
    try:
        # Usar Gemini para gerar perguntas adicionais
        response = await architect.gemini_client.generate_content_async(
            prompt=prompt,
            model_type="flash"
        )
        
        # Parse das perguntas geradas
        ai_questions = [q.strip() for q in response.strip().split('\n') if q.strip()][:2]
        
        # Combinar: 3 obrigatórias + 2 geradas = 5 perguntas
        all_questions = mandatory_questions + ai_questions
        
        return SessionZeroResponse(questions=all_questions)
    
    except Exception as e:
        # Fallback: só perguntas obrigatórias + 2 genéricas
        return SessionZeroResponse(questions=mandatory_questions + [
            "Qual é o seu maior objetivo na cultivação?",
            "O que você mais teme perder?"
        ])

@app.post("/player/create-full", response_model=Player)
async def create_player_full(
    request: CreateCharacterRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Cria um player completo com todos os dados do Character Creation Wizard:
    - Nome, aparência, constituição, origem, e backstory gerada pelo Session Zero
    - Agora também cria: home_location, first_scene_context, important_npc
    """
    from app.core.location_manager import LocationManager
    
    architect = app_state.get("architect")
    if not architect:
        raise HTTPException(status_code=500, detail="Architect service not available")
    
    # Extrair respostas das perguntas obrigatórias (primeiras 3)
    answers = request.session_zero_answers
    first_scene_context = answers[0] if len(answers) > 0 else None  # "Onde sua jornada começa"
    home_description = answers[1] if len(answers) > 1 else None      # "Seu lar/refúgio"
    important_npc_desc = answers[2] if len(answers) > 2 else None    # "Pessoa importante"
    
    # Gerar backstory narrativa baseada nas respostas
    backstory_prompt = f"""
Você é o Mestre de um RPG de cultivação chamado Códice Triluna.
Um novo personagem foi criado com os seguintes detalhes:

Nome: {request.name}
Aparência: {request.appearance or 'Não especificada'}
Constituição: {request.constitution}
Local de Origem: {request.origin_location}

CONTEXTO INICIAL (onde a jornada começa):
{first_scene_context or 'Não especificado'}

LAR/REFÚGIO:
{home_description or 'Não especificado'}

PESSOA IMPORTANTE:
{important_npc_desc or 'Não especificado'}

Respostas adicionais do Session Zero:
{chr(10).join(f'- {ans}' for ans in answers[3:]) if len(answers) > 3 else 'Nenhuma'}

Crie um parágrafo narrativo (4-6 linhas) descrevendo a história de fundo desse personagem.
O texto deve ser literário, no estilo de xianxia/wuxia, e mencionar:
- Sua origem, constituição e lar
- A pessoa importante em sua vida
- Como ele chegou ao momento atual (contexto inicial)

Escreva em português brasileiro, tom épico mas pessoal.
"""
    
    try:
        backstory = await architect.gemini_client.generate_content_async(
            prompt=backstory_prompt,
            model_type="flash"
        )
    except Exception as e:
        backstory = f"{request.name}, nascido em {request.origin_location}, carrega a marca de uma {request.constitution}. Sua jornada de cultivação está apenas começando, mas o destino já traçou seu caminho entre os mortais e imortais."
    
    # Extrair nome do NPC importante (se houver)
    important_npc_name = None
    if important_npc_desc:
        # Tentar extrair um nome da descrição
        try:
            npc_prompt = f"""
Extraia APENAS o nome da pessoa descrita abaixo. 
Se não houver nome claro, crie um nome apropriado para um NPC de xianxia.
Retorne APENAS o nome, nada mais.

Descrição: {important_npc_desc}
"""
            important_npc_name = await architect.gemini_client.generate_content_async(
                prompt=npc_prompt,
                model_type="flash"
            )
            important_npc_name = important_npc_name.strip()[:50]  # Limitar tamanho
        except:
            important_npc_name = None
    
    # [SPRINT 16] Analisar backstory para determinar estado inicial correto
    should_have_skills = False
    initial_location = request.origin_location
    
    # Análise inteligente do contexto
    if first_scene_context:
        context_lower = first_scene_context.lower()
        # Se menciona treinamento, mestre, cultivação anterior, etc.
        if any(word in context_lower for word in ['treinou', 'mestre', 'cultivou', 'técnica', 'discípulo']):
            should_have_skills = True
        # Se menciona ser criança, iniciante, nunca cultivou, etc.
        if any(word in context_lower for word in ['criança', 'nunca cultivou', 'iniciante', 'comprado', 'escravo', 'servente']):
            should_have_skills = False
            
        # Detectar localização específica mencionada
        if 'mansão' in context_lower or 'residência' in context_lower or 'casa' in context_lower:
            # Será ajustada depois ao criar a home_location
            pass
    
    # Criar player no banco de dados SEM SKILLS se não fizer sentido
    player_repo = PlayerRepository(session)
    player = await player_repo.create(
        name=request.name,
        appearance=request.appearance,
        constitution_type=request.constitution,
        origin_location=initial_location,
        backstory=backstory.strip(),
        constitution=request.constitution,
        # Novos campos
        first_scene_context=first_scene_context,
        important_npc_name=important_npc_name
    )
    
    # [SPRINT 16] REMOVER auto-skills se não fizer sentido narrativamente
    if not should_have_skills:
        player.learned_skills = []  # Começar SEM SKILLS
    
    # [SPRINT 5] Aplicar efeitos de constituição nos stats base
    ConstitutionEffects.apply_constitution_effects(player)
    await session.commit()
    await session.refresh(player)
    
    # Criar DynamicLocation para a casa do player (se descreveu)
    if home_description:
        location_manager = LocationManager(session, architect.gemini_client)
        try:
            home_loc = await location_manager.create_location_from_session_zero(
                player=player,
                home_description=home_description
            )
            # [SPRINT 16] Ajustar current_location para home se contexto indicar
            if first_scene_context and any(word in first_scene_context.lower() for word in ['casa', 'lar', 'quarto', 'residência']):
                player.current_location = player.home_location
            # home_location e home_location_id já são setados pelo método
            await session.refresh(player)
        except Exception as e:
            # Se falhar ao criar casa, usar origin_location como fallback
            player.home_location = request.origin_location
            await session.commit()
            await session.refresh(player)
    else:
        # Sem descrição de casa, usar origin como home
        player.home_location = request.origin_location
        await session.commit()
        await session.refresh(player)
    
    # [SPRINT 16] Criar o NPC importante na mesma localização do player
    if important_npc_name and important_npc_desc:
        try:
            # Criar NPC na localização atual do player
            from app.database.models.npc import NPC
            npc_data = {
                "name": important_npc_name,
                "rank": 1,  # Mesmo rank inicial
                "personality_traits": ["amigável", "importante"],
                "emotional_state": "neutral",
                "current_location": player.current_location,
            }
            
            # Inserir diretamente no banco
            important_npc = NPC(**npc_data)
            session.add(important_npc)
            await session.commit()
            print(f"[CHARACTER CREATION] NPC importante '{important_npc_name}' criado em {player.current_location}")
        except Exception as e:
            print(f"[CHARACTER CREATION] Erro ao criar NPC importante: {e}")
    
    await session.commit()
    await session.refresh(player)
    
    # [SPRINT 18] GERAR PRIMEIRA CENA AUTOMÁTICA (Turn 0)
    first_scene_narration = ""
    if first_scene_context:
        try:
            # Buscar NPCs na localização inicial
            npc_repository = NpcRepository(session)
            npcs_at_location = await npc_repository.get_by_location(player.current_location)
            npc_names = [npc.name for npc in npcs_at_location]
            
            # Obter Narrator do app_state
            narrator = app_state.get("narrator")
            if not narrator:
                raise Exception("Narrator não inicializado")
            
            # Gerar narração usando o método correto do Narrator
            first_scene_narration = await narrator.generate_scene_description_async(
                player=player,
                location=player.current_location,
                npcs_in_scene=npcs_at_location,
                player_last_action="",
                previous_narration="",
                memory_repo=None,
                is_first_scene=True
            )
            
            # Registrar Turn 0 no GameLog
            npc_names = [npc.name for npc in npcs_at_location]
            from app.core.chronos import world_clock
            current_time = world_clock.get_current_datetime().isoformat()
            
            turn_0 = GameLog(
                player_id=player.id,
                turn_number=0,
                player_input="[CRIAÇÃO DE PERSONAGEM]",
                scene_description=first_scene_narration if first_scene_narration else f"Você desperta em {player.current_location}.",
                action_result=f"Personagem criado. Skills: {should_have_skills}. NPC Importante: {important_npc_name if important_npc_name else 'Nenhum'}",
                location=player.current_location,
                npcs_present=npc_names,
                world_time=current_time
            )
            session.add(turn_0)
            await session.commit()
            print(f"[SPRINT 18] Turn 0 gerado para {player.name}")
            
        except Exception as e:
            print(f"[SPRINT 18] Erro ao gerar primeira cena: {e}")
            first_scene_narration = f"Você desperta em {player.current_location}. Sua jornada começa agora..."
    
    # [SPRINT 16] Retornar feedback de skills (ou falta delas)
    return {
        **player.model_dump(),
        "creation_feedback": {
            "has_initial_skills": should_have_skills,
            "skills_explanation": "Você ainda não possui técnicas de cultivo. Precisará treinar ou ter uma epifania para aprendê-las." if not should_have_skills else f"Você possui as seguintes técnicas: {', '.join(player.learned_skills)}",
            "important_npc_created": important_npc_name if important_npc_name else None,
            "starting_location": player.current_location,
            "first_scene": first_scene_narration
        }
    }

# =====================================================
# [SPRINT 5] SHOP & ECONOMY ENDPOINTS
# =====================================================

from app.services.shop_manager import shop_manager
from pydantic import BaseModel

class GetPriceRequest(BaseModel):
    item_id: str
    item_category: str  # "pills", "materials", "services", etc.
    item_tier: int  # 1-9
    location: str = "neutral"
    modifiers: list[str] = []

class BuyItemRequest(BaseModel):
    player_id: int
    item_id: str
    item_category: str
    item_tier: int
    location: str = "neutral"
    modifiers: list[str] = []

class SellItemRequest(BaseModel):
    player_id: int
    item_id: str
    buy_price: float
    condition: float = 1.0  # 0.0 a 1.0

@app.post("/shop/price")
async def get_item_price(request: GetPriceRequest):
    """
    Retorna o preço de um item baseado em categoria, tier, localização e modificadores.
    """
    price_data = shop_manager.get_price(
        item_id=request.item_id,
        item_category=request.item_category,
        item_tier=request.item_tier,
        location=request.location,
        modifiers=request.modifiers
    )
    
    return {
        "success": True,
        "data": price_data,
        "formatted": shop_manager.format_price(price_data["final_price"])
    }

@app.post("/shop/buy")
async def buy_item(
    request: BuyItemRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Compra um item. Deduz ouro do jogador e adiciona item ao inventário.
    """
    player_repo = PlayerRepository(session)
    player = await player_repo.get_by_id(request.player_id)
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Calcular preço
    price_data = shop_manager.get_price(
        item_id=request.item_id,
        item_category=request.item_category,
        item_tier=request.item_tier,
        location=request.location,
        modifiers=request.modifiers
    )
    
    final_price = price_data["final_price"]
    
    # Verificar fundos
    if not shop_manager.can_afford(player.gold, final_price):
        raise HTTPException(
            status_code=400, 
            detail=f"Fundos insuficientes. Necessário: {final_price} gold, disponível: {player.gold} gold"
        )
    
    # Deduzir ouro
    player.gold -= final_price
    
    # Adicionar item ao inventário
    new_item = {
        "item_id": request.item_id,
        "category": request.item_category,
        "tier": request.item_tier,
        "quantity": 1,
        "buy_price": final_price
    }
    
    # Copiar lista para forçar SQLAlchemy a detectar a mudança
    updated_inventory = list(player.inventory) if player.inventory else []
    updated_inventory.append(new_item)
    player.inventory = updated_inventory
    
    await player_repo.update(player)
    
    return {
        "success": True,
        "message": f"Item '{request.item_id}' comprado por {shop_manager.format_price(final_price)}",
        "remaining_gold": player.gold,
        "item": new_item
    }

@app.post("/shop/sell")
async def sell_item(
    request: SellItemRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Vende um item do inventário. Adiciona ouro ao jogador e remove item.
    """
    player_repo = PlayerRepository(session)
    player = await player_repo.get_by_id(request.player_id)
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Buscar item no inventário
    item_index = None
    for i, inv_item in enumerate(player.inventory):
        if inv_item.get("item_id") == request.item_id:
            item_index = i
            break
    
    if item_index is None:
        raise HTTPException(status_code=404, detail=f"Item '{request.item_id}' not found in inventory")
    
    # Calcular preço de venda
    sell_price = shop_manager.calculate_sell_price(request.buy_price, request.condition)
    
    # Adicionar ouro
    player.gold += sell_price
    
    # Remover item do inventário
    removed_item = player.inventory.pop(item_index)
    
    await session.commit()
    await session.refresh(player)
    
    return {
        "success": True,
        "message": f"Item '{request.item_id}' vendido por {shop_manager.format_price(sell_price)}",
        "gold_earned": sell_price,
        "total_gold": player.gold,
        "removed_item": removed_item
    }

# ========== SPRINT 6: QUEST ENDPOINTS ==========

@app.post("/quest/generate")
async def generate_quest(
    player_id: int, 
    use_ai: bool = True,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Gera uma nova quest para o player.
    
    Args:
        player_id: ID do jogador
        use_ai: Se True, usa IA para gerar quest contextual. Se False, usa templates.
    """
    player_repo = PlayerRepository(session)
    player = await player_repo.get_by_id(player_id)
    
    if not player:
        raise HTTPException(status_code=404, detail="Player não encontrado")
    
    quest = None
    
    if use_ai:
        # Sprint 12: Geração via IA
        try:
            # Buscar contexto recente
            gamelog_repo = GameLogRepository(session, embedding_service=EmbeddingService())
            recent_logs = await gamelog_repo.get_recent_turns(player_id, limit=5)
            recent_events = [log.action_result for log in recent_logs if log.action_result]
            
            # Buscar NPCs próximos
            npc_repo = NpcRepository(session)
            nearby_npcs_objs = await npc_repo.get_by_location(player.current_location)
            nearby_npcs = [npc.name for npc in nearby_npcs_objs if npc.emotional_state != "hostile"]
            
            quest = await quest_service.generate_quest_ai(
                player=player,
                recent_events=recent_events,
                nearby_npcs=nearby_npcs,
                world_context=f"O jogador está em {player.current_location}."
            )
        except Exception as e:
            print(f"[QUEST] Erro na geração AI: {e}")
            quest = None
    
    # Fallback para template
    if not quest:
        quest = quest_service.generate_quest(player)
    
    if not quest:
        raise HTTPException(status_code=400, detail="Não há quests disponíveis para seu tier/localização")
    
    quest_service.add_quest_to_player(player_id, quest)
    
    return {
        "success": True,
        "quest": quest,
        "message": f"🎯 Nova missão desbloqueada: {quest['title']}",
        "generated_by_ai": quest.get("generated_by_ai", False)
    }

@app.get("/quest/active/{player_id}")
async def get_active_quests(player_id: int):
    """Retorna todas as quests ativas de um player."""
    active_quests = quest_service.get_active_quests(player_id)
    
    # Verificar deadlines automaticamente
    quest_service.check_deadlines(player_id)
    
    return {
        "quests": active_quests,
        "count": len(active_quests)
    }

@app.get("/game/log/{player_id}")
async def get_game_log(player_id: int, limit: int = 10):
    """Retorna o histórico de turnos do jogador."""
    try:
        async with AsyncSession(engine) as session:
            from sqlmodel import select
            from app.database.models import GameLog
            
            statement = select(GameLog).where(
                GameLog.player_id == player_id
            ).order_by(GameLog.turn_number.desc()).limit(limit)
            
            results = await session.execute(statement)
            logs = results.scalars().all()
            
            return {
                "logs": [
                    {
                        "turn_number": log.turn_number,
                        "player_input": log.player_input,
                        "scene_description": log.scene_description,
                        "action_result": log.action_result,
                        "location": log.location,
                        "npcs_present": log.npcs_present,
                        "world_time": log.world_time,
                        "created_at": log.created_at.isoformat() if log.created_at else None
                    }
                    for log in logs
                ],
                "count": len(logs)
            }
    except Exception as e:
        print(f"[GAME LOG] Erro ao buscar histórico: {e}")
        return {"logs": [], "count": 0}

@app.post("/quest/complete")
async def complete_quest(
    player_id: int,
    quest_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Completa uma quest e aplica recompensas."""
    player_repo = PlayerRepository(session)
    player = await player_repo.get_by_id(player_id)
    
    if not player:
        raise HTTPException(status_code=404, detail="Player não encontrado")
    
    active_quests = quest_service.get_active_quests(player_id)
    quest = next((q for q in active_quests if q["id"] == quest_id), None)
    
    if not quest:
        raise HTTPException(status_code=404, detail="Quest não encontrada")
    
    if quest["status"] != "completed":
        raise HTTPException(status_code=400, detail="Quest ainda não foi concluída")
    
    quest_service.complete_quest(player, quest)
    
    await session.commit()
    await session.refresh(player)
    
    return {
        "success": True,
        "message": f"✨ Quest '{quest['title']}' finalizada!",
        "rewards": {
            "xp": quest["reward_xp"],
            "gold": quest["reward_gold"],
            "items": quest.get("reward_items", [])
        },
        "player_xp": player.xp,
        "player_gold": player.gold
    }

@app.get("/game/current-turn")
async def get_current_turn():
    """Retorna o turno atual do mundo."""
    return {
        "current_turn": world_clock.get_current_turn(),
        "current_date": world_clock.get_current_date()
    }

# ========== WORLD EVENTS & INVESTIGATION ==========

from app.database.repositories.world_event_repo import WorldEventRepository

class InvestigateRequest(BaseModel):
    player_id: int
    event_id: int

class CreateWorldEventRequest(BaseModel):
    event_type: str  # destruction, npc_death, faction_war, calamity
    description: str
    location_affected: Optional[str] = None
    caused_by_player_id: Optional[int] = None
    author_alias: Optional[str] = None
    investigation_difficulty: int = 5
    clues: List[str] = []

@app.get("/world/events")
async def get_world_events(
    location: Optional[str] = None,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Retorna eventos globais ativos.
    Se location for passado, retorna só eventos daquele local.
    """
    event_repo = WorldEventRepository(session)
    
    if location:
        events = await event_repo.get_events_for_location(location)
    else:
        events = await event_repo.get_active_events()
    
    # Retornar apenas informação pública
    return {
        "events": [
            {
                "id": e.id,
                "type": e.event_type,
                "public_description": e.public_description,
                "location": e.location_affected,
                "author_alias": e.author_alias,
                "difficulty": e.investigation_difficulty,
                "turn_occurred": e.turn_occurred
            }
            for e in events
        ]
    }

@app.post("/world/investigate")
async def investigate_event(
    request: InvestigateRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Player investiga um evento para descobrir pistas e possivelmente o autor.
    Dificuldade vs Rank do player determina sucesso.
    """
    player_repo = PlayerRepository(session)
    player = await player_repo.get_by_id(request.player_id)
    
    if not player:
        raise HTTPException(status_code=404, detail="Player não encontrado")
    
    event_repo = WorldEventRepository(session)
    result = await event_repo.investigate_event(
        event_id=request.event_id,
        investigator_rank=player.rank
    )
    
    return result

@app.post("/world/create-event")
async def create_world_event(
    request: CreateWorldEventRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Cria um novo evento global (usado pelo sistema quando player causa destruição).
    """
    event_repo = WorldEventRepository(session)
    
    event = await event_repo.create_event(
        event_type=request.event_type,
        description=request.description,
        turn_occurred=world_clock.get_current_turn(),
        location_affected=request.location_affected,
        caused_by_player_id=request.caused_by_player_id,
        author_alias=request.author_alias,
        investigation_difficulty=request.investigation_difficulty,
        clues=request.clues,
        public_description=request.description  # Por padrão, público = descrição
    )
    
    return {
        "success": True,
        "event_id": event.id,
        "message": f"Evento '{request.event_type}' criado em {request.location_affected or 'mundo'}"
    }

@app.get("/world/events-by-player/{player_id}")
async def get_events_caused_by_player(
    player_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Retorna eventos causados por um player específico.
    Usado para ver o "legado" de destruição de um personagem.
    """
    event_repo = WorldEventRepository(session)
    events = await event_repo.get_events_by_player(player_id)
    
    return {
        "player_id": player_id,
        "events_caused": len(events),
        "events": [
            {
                "id": e.id,
                "type": e.event_type,
                "description": e.description,
                "location": e.location_affected,
                "turn": e.turn_occurred
            }
            for e in events
        ]
    }


# =====================================================
# ECONOMY ENDPOINTS
# =====================================================

@app.get("/economy/report")
async def get_economy_report(session: AsyncSession = Depends(get_async_session)):
    """
    Retorna relatório completo da economia mundial.
    Mostra preços atuais, tendências e recursos.
    """
    from app.database.repositories.economy_repo import GlobalEconomyRepository
    from app.core.simulation.economy import EconomySimulator
    
    economy_repo = GlobalEconomyRepository(session)
    economy_sim = EconomySimulator(economy_repo=economy_repo)
    
    report = await economy_sim.get_market_report()
    
    return {
        "status": "ok",
        "trending_up": report.get("trending_up", []),
        "trending_down": report.get("trending_down", []),
        "stable": report.get("stable", []),
        "prices": report.get("prices", {})
    }


@app.get("/economy/price/{resource_name}")
async def get_resource_price(
    resource_name: str,
    location: str = None,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Retorna o preço atual de um recurso.
    Opcionalmente aplica modificador regional.
    """
    from app.database.repositories.economy_repo import GlobalEconomyRepository
    from app.core.simulation.economy import EconomySimulator
    
    economy_repo = GlobalEconomyRepository(session)
    economy_sim = EconomySimulator(economy_repo=economy_repo)
    
    base_price = await economy_sim.get_current_price(resource_name)
    
    if location:
        final_price = await economy_sim.apply_regional_modifier(
            location=location,
            resource_name=resource_name,
            base_price=base_price
        )
    else:
        final_price = base_price
    
    multiplier = await economy_sim.get_price_multiplier(resource_name)
    
    return {
        "resource": resource_name,
        "location": location,
        "current_price": round(final_price, 2),
        "price_multiplier": round(multiplier, 2)
    }


@app.post("/economy/initialize")
async def initialize_economy(session: AsyncSession = Depends(get_async_session)):
    """
    Inicializa a economia com itens padrão.
    Chamado uma vez na configuração inicial.
    """
    from app.database.repositories.economy_repo import GlobalEconomyRepository
    
    economy_repo = GlobalEconomyRepository(session)
    created_items = await economy_repo.initialize_default_economy()
    
    return {
        "status": "ok",
        "message": f"Economia inicializada com {len(created_items)} itens",
        "items_created": [item.resource_name for item in created_items]
    }


# =====================================================
# FACTION ENDPOINTS
# =====================================================

@app.get("/factions")
async def get_all_factions(session: AsyncSession = Depends(get_async_session)):
    """
    Retorna todas as facções do jogo.
    """
    from app.database.repositories.faction_repo import FactionRepository
    
    faction_repo = FactionRepository(session)
    factions = await faction_repo.get_all()
    
    return {
        "status": "ok",
        "factions": [
            {
                "id": f.id,
                "name": f.name,
                "power_level": f.power_level,
                "resources": f.resources,
                "relations": f.relations
            }
            for f in factions
        ]
    }


@app.get("/factions/{faction_name}")
async def get_faction_details(
    faction_name: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Retorna detalhes de uma facção específica.
    """
    from app.database.repositories.faction_repo import FactionRepository
    
    faction_repo = FactionRepository(session)
    faction = await faction_repo.get_by_name(faction_name)
    
    if not faction:
        raise HTTPException(status_code=404, detail=f"Facção '{faction_name}' não encontrada")
    
    allies = await faction_repo.get_allies(faction_name)
    enemies = await faction_repo.get_enemies(faction_name)
    
    return {
        "id": faction.id,
        "name": faction.name,
        "power_level": faction.power_level,
        "resources": faction.resources,
        "relations": faction.relations,
        "allies": allies,
        "enemies": enemies
    }


@app.post("/factions/initialize")
async def initialize_factions(session: AsyncSession = Depends(get_async_session)):
    """
    Inicializa as facções padrão do jogo.
    Chamado uma vez na configuração inicial.
    """
    from app.database.repositories.faction_repo import FactionRepository
    
    faction_repo = FactionRepository(session)
    created_factions = await faction_repo.initialize_default_factions()
    
    return {
        "status": "ok",
        "message": f"Facções inicializadas: {len(created_factions)} criadas",
        "factions_created": [f.name for f in created_factions]
    }


@app.get("/factions/territory/{location}")
async def get_territory_owner(
    location: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Retorna qual facção controla um território.
    """
    from app.core.simulation.faction_simulator import FactionSimulator
    
    faction_sim = FactionSimulator()
    owner = faction_sim.get_territory_owner(location)
    
    return {
        "location": location,
        "owner": owner,
        "is_neutral": owner == "Neutral"
    }


# =====================================================
# ECOLOGY ENDPOINTS
# =====================================================

@app.get("/ecology/report")
async def get_ecology_report():
    """
    Retorna relatório de ecologia (populações de monstros).
    """
    from app.core.simulation.ecology import EcologySimulator
    
    ecology_sim = EcologySimulator()
    report = ecology_sim.get_ecology_report()
    
    return {
        "status": "ok",
        "total_monsters": report["total_monsters"],
        "most_populated": report["most_populated"],
        "least_populated": report["least_populated"],
        "high_pressure_regions": report["high_pressure_regions"],
        "regions": report["regions"]
    }


@app.get("/ecology/encounter/{location}")
async def get_random_encounter(location: str):
    """
    Retorna um monstro aleatório para encontro baseado na localização.
    """
    from app.core.simulation.ecology import EcologySimulator
    
    ecology_sim = EcologySimulator()
    monster = ecology_sim.get_random_encounter(location)
    population = ecology_sim.get_monster_population(location)
    
    return {
        "location": location,
        "encounter": monster,
        "local_monsters": population
    }
