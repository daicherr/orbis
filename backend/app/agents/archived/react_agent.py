"""
ReAct Agent Framework - Reasoning + Acting
GEM RPG ORBIS - Arquitetura Cognitiva

Framework para agentes que usam o padrão ReAct:
Thought → Action → Observation → Repeat

Cada agente pode ter seu próprio conjunto de ferramentas (tools)
e usa o modelo Gemini para raciocínio.

Referência: "ReAct: Synergizing Reasoning and Acting in Language Models"
https://arxiv.org/abs/2210.03629
"""

from typing import Dict, List, Any, Optional, Callable, Awaitable, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import json
import re
import traceback
from datetime import datetime


class AgentState(str, Enum):
    """Estados possíveis do agente durante execução."""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    OBSERVING = "observing"
    COMPLETED = "completed"
    ERROR = "error"
    MAX_ITERATIONS = "max_iterations"


class ToolResultType(str, Enum):
    """Tipos de resultado de uma ferramenta."""
    SUCCESS = "success"
    ERROR = "error"
    NOT_FOUND = "not_found"
    INVALID_ARGS = "invalid_args"


@dataclass
class Tool:
    """
    Definição de uma ferramenta que o agente pode usar.
    
    Attributes:
        name: Nome único da ferramenta (snake_case)
        description: Descrição do que a ferramenta faz
        parameters: Schema dos parâmetros (JSON Schema simplificado)
        handler: Função async que executa a ferramenta
        requires_confirmation: Se True, pede confirmação antes de executar
    """
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable[..., Awaitable[Any]]
    requires_confirmation: bool = False
    
    def to_prompt_string(self) -> str:
        """Gera descrição da ferramenta para o prompt."""
        params_str = json.dumps(self.parameters, indent=2, ensure_ascii=False)
        return f"""- **{self.name}**: {self.description}
  Parâmetros: {params_str}"""


@dataclass
class ToolResult:
    """Resultado da execução de uma ferramenta."""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    
    def to_observation_string(self) -> str:
        """Converte para string de observação para o agente."""
        if self.success:
            if isinstance(self.result, dict):
                result_str = json.dumps(self.result, indent=2, ensure_ascii=False)
            elif isinstance(self.result, list):
                result_str = json.dumps(self.result, indent=2, ensure_ascii=False)
            else:
                result_str = str(self.result)
            return f"✓ {self.tool_name}: {result_str}"
        else:
            return f"✗ {self.tool_name} FALHOU: {self.error}"


@dataclass
class ThoughtStep:
    """Um passo de pensamento do agente."""
    step_number: int
    thought: str
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_string(self) -> str:
        """Converte para string formatada."""
        parts = [f"[Passo {self.step_number}]"]
        parts.append(f"Pensamento: {self.thought}")
        
        if self.action:
            parts.append(f"Ação: {self.action}")
            if self.action_input:
                input_str = json.dumps(self.action_input, ensure_ascii=False)
                parts.append(f"Input: {input_str}")
        
        if self.observation:
            parts.append(f"Observação: {self.observation}")
        
        return "\n".join(parts)


@dataclass
class AgentTrace:
    """Trace completo da execução de um agente."""
    agent_name: str
    task: str
    steps: List[ThoughtStep] = field(default_factory=list)
    final_answer: Optional[str] = None
    state: AgentState = AgentState.IDLE
    total_time_ms: float = 0.0
    token_count: int = 0
    error: Optional[str] = None
    
    def add_step(self, step: ThoughtStep):
        """Adiciona um passo ao trace."""
        self.steps.append(step)
    
    def get_last_step(self) -> Optional[ThoughtStep]:
        """Retorna o último passo."""
        return self.steps[-1] if self.steps else None
    
    def to_summary_string(self) -> str:
        """Retorna resumo da execução."""
        return (
            f"Agent: {self.agent_name}\n"
            f"Task: {self.task}\n"
            f"Steps: {len(self.steps)}\n"
            f"State: {self.state}\n"
            f"Time: {self.total_time_ms:.2f}ms\n"
            f"Answer: {self.final_answer[:100] if self.final_answer else 'None'}..."
        )


class ReActAgent(ABC):
    """
    Agente base que implementa o padrão ReAct.
    
    Subclasses devem implementar:
    - _build_system_prompt(): Prompt de sistema específico
    - _get_tools(): Lista de ferramentas disponíveis
    
    O agente executa o loop:
    1. Recebe tarefa
    2. Pensa sobre o que fazer
    3. Escolhe uma ação (ferramenta) ou resposta final
    4. Executa a ação e observa resultado
    5. Repete até completar ou atingir max_iterations
    """
    
    def __init__(
        self,
        name: str,
        gemini_client: Any,  # GeminiClient
        max_iterations: int = 10,
        verbose: bool = False
    ):
        self.name = name
        self.gemini_client = gemini_client
        self.max_iterations = max_iterations
        self.verbose = verbose
        
        # Cache de ferramentas
        self._tools: Dict[str, Tool] = {}
        self._tools_initialized = False
    
    @abstractmethod
    def _build_system_prompt(self) -> str:
        """
        Constrói o prompt de sistema específico para este agente.
        Deve incluir contexto, regras e formato esperado.
        """
        pass
    
    @abstractmethod
    def _get_tools(self) -> List[Tool]:
        """
        Retorna a lista de ferramentas disponíveis para este agente.
        """
        pass
    
    def _ensure_tools_initialized(self):
        """Garante que as ferramentas foram inicializadas."""
        if not self._tools_initialized:
            tools = self._get_tools()
            self._tools = {tool.name: tool for tool in tools}
            self._tools_initialized = True
    
    def _build_tools_prompt(self) -> str:
        """Gera a seção do prompt que descreve as ferramentas disponíveis."""
        self._ensure_tools_initialized()
        
        if not self._tools:
            return "Você não tem ferramentas disponíveis. Responda diretamente."
        
        tools_desc = "\n".join(tool.to_prompt_string() for tool in self._tools.values())
        
        return f"""
## FERRAMENTAS DISPONÍVEIS

{tools_desc}

## FORMATO DE RESPOSTA

Você DEVE responder EXATAMENTE neste formato:

**Para usar uma ferramenta:**
```
Pensamento: [seu raciocínio sobre o que fazer]
Ação: [nome_da_ferramenta]
Input: {{"param1": "valor1", "param2": "valor2"}}
```

**Para dar a resposta final:**
```
Pensamento: [seu raciocínio final]
Resposta Final: [sua resposta completa]
```

REGRAS:
- Use EXATAMENTE os nomes das ferramentas como listados
- O Input DEVE ser um JSON válido
- Não invente ferramentas que não existem
- Quando tiver informação suficiente, dê a Resposta Final
"""
    
    def _parse_agent_response(self, response: str) -> Dict[str, Any]:
        """
        Parseia a resposta do agente para extrair pensamento, ação e input.
        
        Returns:
            Dict com keys: thought, action, action_input, final_answer
        """
        result = {
            "thought": None,
            "action": None,
            "action_input": None,
            "final_answer": None,
            "raw": response
        }
        
        # Extrair Pensamento
        thought_match = re.search(
            r'Pensamento:\s*(.+?)(?=(?:Ação:|Resposta Final:|Input:|$))',
            response,
            re.DOTALL | re.IGNORECASE
        )
        if thought_match:
            result["thought"] = thought_match.group(1).strip()
        
        # Verificar se é resposta final
        final_match = re.search(
            r'Resposta Final:\s*(.+?)$',
            response,
            re.DOTALL | re.IGNORECASE
        )
        if final_match:
            result["final_answer"] = final_match.group(1).strip()
            return result
        
        # Extrair Ação
        action_match = re.search(
            r'Ação:\s*(\w+)',
            response,
            re.IGNORECASE
        )
        if action_match:
            result["action"] = action_match.group(1).strip()
        
        # Extrair Input (JSON)
        input_match = re.search(
            r'Input:\s*(\{.+?\})',
            response,
            re.DOTALL | re.IGNORECASE
        )
        if input_match:
            try:
                result["action_input"] = json.loads(input_match.group(1))
            except json.JSONDecodeError:
                # Tentar limpar e parsear novamente
                cleaned = input_match.group(1).replace("'", '"')
                try:
                    result["action_input"] = json.loads(cleaned)
                except:
                    result["action_input"] = {"_raw": input_match.group(1)}
        
        return result
    
    async def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> ToolResult:
        """Executa uma ferramenta e retorna o resultado."""
        start_time = datetime.utcnow()
        
        if tool_name not in self._tools:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"Ferramenta '{tool_name}' não encontrada. Ferramentas disponíveis: {list(self._tools.keys())}"
            )
        
        tool = self._tools[tool_name]
        
        try:
            result = await tool.handler(**tool_input)
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ToolResult(
                tool_name=tool_name,
                success=True,
                result=result,
                execution_time_ms=execution_time
            )
        except TypeError as e:
            # Provavelmente parâmetros errados
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"Parâmetros inválidos: {str(e)}. Esperado: {tool.parameters}"
            )
        except Exception as e:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"Erro ao executar: {str(e)}"
            )
    
    async def run(
        self, 
        task: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> AgentTrace:
        """
        Executa o agente para completar uma tarefa.
        
        Args:
            task: A tarefa a ser realizada
            context: Contexto adicional para o agente
            
        Returns:
            AgentTrace com todo o histórico de execução
        """
        self._ensure_tools_initialized()
        start_time = datetime.utcnow()
        
        trace = AgentTrace(
            agent_name=self.name,
            task=task,
            state=AgentState.THINKING
        )
        
        # Construir prompt inicial
        system_prompt = self._build_system_prompt()
        tools_prompt = self._build_tools_prompt()
        
        context_str = ""
        if context:
            context_str = f"\n## CONTEXTO\n{json.dumps(context, indent=2, ensure_ascii=False)}\n"
        
        # Histórico de conversação para o modelo
        messages = [
            {
                "role": "system",
                "content": f"{system_prompt}\n{tools_prompt}{context_str}"
            },
            {
                "role": "user",
                "content": f"Tarefa: {task}"
            }
        ]
        
        # Loop principal do ReAct
        for iteration in range(1, self.max_iterations + 1):
            if self.verbose:
                print(f"\n[{self.name}] Iteração {iteration}/{self.max_iterations}")
            
            trace.state = AgentState.THINKING
            
            # Gerar resposta do agente
            try:
                response = await self._call_model(messages)
                trace.token_count += len(response.split())  # Estimativa simples
            except Exception as e:
                trace.state = AgentState.ERROR
                trace.error = f"Erro ao chamar modelo: {str(e)}"
                break
            
            # Parsear resposta
            parsed = self._parse_agent_response(response)
            
            step = ThoughtStep(
                step_number=iteration,
                thought=parsed.get("thought", ""),
                action=parsed.get("action"),
                action_input=parsed.get("action_input")
            )
            
            if self.verbose:
                print(f"  Pensamento: {step.thought[:100]}...")
            
            # Verificar se é resposta final
            if parsed.get("final_answer"):
                step.observation = "Tarefa concluída"
                trace.add_step(step)
                trace.final_answer = parsed["final_answer"]
                trace.state = AgentState.COMPLETED
                
                if self.verbose:
                    print(f"  ✓ Resposta final obtida")
                break
            
            # Executar ação se especificada
            if parsed.get("action"):
                trace.state = AgentState.ACTING
                
                if self.verbose:
                    print(f"  Ação: {parsed['action']}")
                
                tool_result = await self._execute_tool(
                    parsed["action"],
                    parsed.get("action_input", {})
                )
                
                trace.state = AgentState.OBSERVING
                step.observation = tool_result.to_observation_string()
                
                if self.verbose:
                    print(f"  Observação: {step.observation[:100]}...")
                
                # Adicionar observação ao histórico de mensagens
                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user",
                    "content": f"Observação: {step.observation}"
                })
            else:
                # Sem ação e sem resposta final - pedir para continuar
                step.observation = "Nenhuma ação especificada. Continue o raciocínio ou forneça uma Resposta Final."
                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user",
                    "content": step.observation
                })
            
            trace.add_step(step)
        else:
            # Atingiu max_iterations sem resposta final
            trace.state = AgentState.MAX_ITERATIONS
            trace.error = f"Atingiu máximo de {self.max_iterations} iterações sem resposta final"
            
            # Tentar extrair resposta do último passo
            if trace.steps:
                last_thought = trace.steps[-1].thought
                trace.final_answer = f"[Incompleto após {self.max_iterations} iterações] {last_thought}"
        
        # Calcular tempo total
        trace.total_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return trace
    
    async def _call_model(self, messages: List[Dict[str, str]]) -> str:
        """
        Chama o modelo Gemini com as mensagens.
        Subclasses podem sobrescrever para usar diferentes configs.
        """
        # Converter formato de mensagens para o Gemini
        # O Gemini usa um formato diferente, então precisamos adaptar
        
        # Combinar system prompt com primeira mensagem
        full_prompt = ""
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                full_prompt += f"{content}\n\n"
            elif role == "user":
                full_prompt += f"Usuário: {content}\n\n"
            elif role == "assistant":
                full_prompt += f"Assistente: {content}\n\n"
        
        full_prompt += "Assistente:"
        
        # Chamar Gemini
        response = self.gemini_client.generate_text(full_prompt, task="default")
        
        return response


class SimpleReActAgent(ReActAgent):
    """
    Agente ReAct simples para testes e demonstração.
    Pode ser instanciado diretamente com prompt e ferramentas personalizados.
    """
    
    def __init__(
        self,
        name: str,
        gemini_client: Any,
        system_prompt: str,
        tools: List[Tool],
        max_iterations: int = 10,
        verbose: bool = False
    ):
        super().__init__(name, gemini_client, max_iterations, verbose)
        self._custom_system_prompt = system_prompt
        self._custom_tools = tools
    
    def _build_system_prompt(self) -> str:
        return self._custom_system_prompt
    
    def _get_tools(self) -> List[Tool]:
        return self._custom_tools


# ==================== FERRAMENTAS UTILITÁRIAS ====================

def create_tool(
    name: str,
    description: str,
    parameters: Dict[str, Any],
    handler: Callable[..., Awaitable[Any]],
    requires_confirmation: bool = False
) -> Tool:
    """Factory function para criar ferramentas de forma mais simples."""
    return Tool(
        name=name,
        description=description,
        parameters=parameters,
        handler=handler,
        requires_confirmation=requires_confirmation
    )


async def dummy_tool_handler(**kwargs) -> str:
    """Handler dummy para testes."""
    return f"Ferramenta executada com sucesso. Parâmetros: {kwargs}"


# Ferramentas de exemplo
EXAMPLE_TOOLS = [
    Tool(
        name="search_knowledge",
        description="Busca informações na base de conhecimento do mundo",
        parameters={
            "query": {"type": "string", "description": "O que buscar"},
            "category": {"type": "string", "description": "Categoria: lore, mechanics, npcs, locations"}
        },
        handler=dummy_tool_handler
    ),
    Tool(
        name="check_player_stats",
        description="Verifica os stats atuais do jogador",
        parameters={
            "player_id": {"type": "integer", "description": "ID do jogador"}
        },
        handler=dummy_tool_handler
    ),
    Tool(
        name="roll_dice",
        description="Rola dados para determinar resultado de ações",
        parameters={
            "dice": {"type": "string", "description": "Formato XdY (ex: 2d6, 1d20)"},
            "modifier": {"type": "integer", "description": "Modificador a adicionar"}
        },
        handler=dummy_tool_handler
    ),
]
