"""
AgentState - Estado Central do Grafo
GEM RPG ORBIS - LangGraph Architecture

Este é o CONTRATO entre todos os nós do grafo.
Cada nó lê partes do estado e escreve atualizações.

Princípios:
- Imutável onde possível (novos valores, não mutação)
- Tipagem forte para evitar bugs
- Serializable para PostgresSaver
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal, Annotated
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import operator


# ==================== ENUMS ====================

class ActionIntent(str, Enum):
    """Intenções de ação do jogador."""
    ATTACK = "attack"
    DEFEND = "defend"
    FLEE = "flee"
    USE_SKILL = "use_skill"
    TALK = "talk"
    PERSUADE = "persuade"
    INTIMIDATE = "intimidate"
    TRADE = "trade"
    MOVE = "move"
    EXPLORE = "explore"
    SEARCH = "search"
    OBSERVE = "observe"
    REST = "rest"
    MEDITATE = "meditate"
    CULTIVATE = "cultivate"
    TRAIN = "train"
    USE_ITEM = "use_item"
    EQUIP = "equip"
    PICK_UP = "pick_up"
    DROP = "drop"
    WAIT = "wait"
    UNKNOWN = "unknown"


class ValidationStatus(str, Enum):
    """Status da validação."""
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    NEEDS_RETRY = "needs_retry"


class NodeType(str, Enum):
    """Tipos de nó no grafo."""
    PLANNER = "planner"
    EXECUTOR = "executor"
    VALIDATOR = "validator"
    NARRATOR = "narrator"
    END = "end"


# ==================== DATA CLASSES ====================

@dataclass
class Message:
    """Mensagem no histórico de conversação."""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class PlayerContext:
    """Contexto do jogador atual."""
    id: int
    name: str
    cultivation_rank: int = 1
    current_hp: int = 100
    max_hp: int = 100
    current_location: str = "Initial Village"
    yuan_qi: int = 100
    max_yuan_qi: int = 100
    shadow_chi: int = 50
    max_shadow_chi: int = 50
    gold: int = 0
    inventory: List[Dict[str, Any]] = field(default_factory=list)
    learned_skills: List[str] = field(default_factory=list)
    constitution_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NPCContext:
    """Contexto de um NPC na cena."""
    id: int
    name: str
    rank: int = 1
    current_hp: int = 100
    max_hp: int = 100
    emotional_state: str = "neutral"
    species: str = "human"
    can_speak: bool = True
    personality_traits: List[str] = field(default_factory=list)
    is_hostile: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WorldContext:
    """Contexto do mundo."""
    current_location: str = "Initial Village"
    time_of_day: str = "morning"  # morning, afternoon, evening, night
    date_string: str = ""
    weather: str = "clear"
    qi_density: float = 1.0
    danger_level: int = 1
    npcs_in_scene: List[NPCContext] = field(default_factory=list)
    available_exits: List[str] = field(default_factory=list)
    active_events: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_location": self.current_location,
            "time_of_day": self.time_of_day,
            "date_string": self.date_string,
            "weather": self.weather,
            "qi_density": self.qi_density,
            "danger_level": self.danger_level,
            "npcs_in_scene": [npc.to_dict() for npc in self.npcs_in_scene],
            "available_exits": self.available_exits,
            "active_events": self.active_events
        }


@dataclass
class PlannedAction:
    """Ação planejada pelo Planner."""
    intent: ActionIntent
    target_name: Optional[str] = None
    skill_name: Optional[str] = None
    destination: Optional[str] = None
    spoken_words: Optional[str] = None
    item_name: Optional[str] = None
    reasoning: str = ""
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent.value if isinstance(self.intent, ActionIntent) else self.intent,
            "target_name": self.target_name,
            "skill_name": self.skill_name,
            "destination": self.destination,
            "spoken_words": self.spoken_words,
            "item_name": self.item_name,
            "reasoning": self.reasoning,
            "confidence": self.confidence
        }


@dataclass
class ActionResult:
    """Resultado da execução de uma ação."""
    success: bool
    message: str
    damage_dealt: int = 0
    damage_received: int = 0
    resources_changed: Dict[str, int] = field(default_factory=dict)
    items_gained: List[Dict[str, Any]] = field(default_factory=list)
    items_lost: List[str] = field(default_factory=list)
    xp_gained: int = 0
    gold_changed: int = 0
    location_changed: bool = False
    new_location: Optional[str] = None
    npc_killed: Optional[str] = None
    player_died: bool = False
    special_events: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationResult:
    """Resultado da validação."""
    status: ValidationStatus
    is_valid: bool
    error_message: Optional[str] = None
    retry_reason: Optional[str] = None
    suggested_alternative: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "is_valid": self.is_valid,
            "error_message": self.error_message,
            "retry_reason": self.retry_reason,
            "suggested_alternative": self.suggested_alternative
        }


# ==================== AGENT STATE (TypedDict) ====================

class AgentState(TypedDict, total=False):
    """
    Estado central do agente LangGraph.
    
    Este é o contrato entre todos os nós do grafo.
    Usa TypedDict para compatibilidade com LangGraph.
    
    Campos com Annotated[..., operator.add] acumulam valores.
    Campos normais são sobrescritos.
    """
    
    # === Identificação da Sessão ===
    session_id: str
    player_id: int
    turn_number: int
    
    # === Input do Usuário ===
    user_input: str
    
    # === Histórico de Mensagens (acumula) ===
    messages: Annotated[List[Dict[str, Any]], operator.add]
    
    # === Contextos ===
    player: Dict[str, Any]  # PlayerContext serializado
    world: Dict[str, Any]   # WorldContext serializado
    
    # === Pipeline do Turno ===
    planned_action: Optional[Dict[str, Any]]  # PlannedAction serializado
    action_result: Optional[Dict[str, Any]]   # ActionResult serializado
    validation: Optional[Dict[str, Any]]      # ValidationResult serializado
    
    # === Controle de Fluxo ===
    validation_attempts: int
    max_validation_attempts: int
    current_node: str
    next_node: str
    
    # === Output Final ===
    narration: str
    action_summary: str
    
    # === Metadata ===
    error: Optional[str]
    timestamp: str


# ==================== FACTORY FUNCTIONS ====================

def create_initial_state(
    session_id: str,
    player_id: int,
    user_input: str,
    player_context: PlayerContext,
    world_context: WorldContext,
    turn_number: int = 1
) -> AgentState:
    """
    Cria um estado inicial para um novo turno.
    
    Args:
        session_id: ID único da sessão
        player_id: ID do jogador
        user_input: Input do usuário
        player_context: Contexto do jogador
        world_context: Contexto do mundo
        turn_number: Número do turno atual
        
    Returns:
        AgentState inicializado
    """
    return AgentState(
        session_id=session_id,
        player_id=player_id,
        turn_number=turn_number,
        user_input=user_input,
        messages=[{
            "role": "user",
            "content": user_input,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"turn": turn_number}
        }],
        player=player_context.to_dict(),
        world=world_context.to_dict(),
        planned_action=None,
        action_result=None,
        validation=None,
        validation_attempts=0,
        max_validation_attempts=3,
        current_node="start",
        next_node="planner",
        narration="",
        action_summary="",
        error=None,
        timestamp=datetime.utcnow().isoformat()
    )


def player_from_db(player_db) -> PlayerContext:
    """Converte modelo do banco para PlayerContext."""
    return PlayerContext(
        id=player_db.id,
        name=player_db.name,
        cultivation_rank=getattr(player_db, 'cultivation_rank', 1),
        current_hp=getattr(player_db, 'current_hp', 100),
        max_hp=getattr(player_db, 'max_hp', 100),
        current_location=getattr(player_db, 'current_location', 'Initial Village'),
        yuan_qi=getattr(player_db, 'yuan_qi', 100),
        max_yuan_qi=getattr(player_db, 'max_yuan_qi', 100),
        shadow_chi=getattr(player_db, 'shadow_chi', 50),
        max_shadow_chi=getattr(player_db, 'max_shadow_chi', 50),
        gold=getattr(player_db, 'gold', 0),
        inventory=player_db.inventory if player_db.inventory else [],
        learned_skills=player_db.learned_skills if player_db.learned_skills else [],
        constitution_type=getattr(player_db, 'constitution_type', None)
    )


def npc_from_db(npc_db) -> NPCContext:
    """Converte modelo do banco para NPCContext."""
    return NPCContext(
        id=npc_db.id,
        name=npc_db.name,
        rank=getattr(npc_db, 'rank', 1),
        current_hp=getattr(npc_db, 'current_hp', 100),
        max_hp=getattr(npc_db, 'max_hp', 100),
        emotional_state=getattr(npc_db, 'emotional_state', 'neutral'),
        species=getattr(npc_db, 'species', 'human'),
        can_speak=getattr(npc_db, 'can_speak', True),
        personality_traits=npc_db.personality_traits if npc_db.personality_traits else [],
        is_hostile=getattr(npc_db, 'emotional_state', '') == 'hostile'
    )


def world_from_context(
    location: str,
    npcs: List,
    time_of_day: str = "morning",
    date_string: str = "",
    weather: str = "clear"
) -> WorldContext:
    """Cria WorldContext a partir de dados do jogo."""
    return WorldContext(
        current_location=location,
        time_of_day=time_of_day,
        date_string=date_string,
        weather=weather,
        npcs_in_scene=[npc_from_db(npc) for npc in npcs]
    )
