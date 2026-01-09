"""
SessionContext - Estado Completo da Sessão de Jogo
GEM RPG ORBIS - Arquitetura Cognitiva

Este módulo mantém o estado completo de uma sessão de jogo, incluindo:
- Histórico dos últimos N turnos
- Entidades presentes na cena
- Arco narrativo e tensão
- Hooks narrativos pendentes
- Threads de plot ativas

O SessionContext é o "cérebro" que conecta todos os componentes,
permitindo que a IA mantenha consistência entre turnos.
"""

from __future__ import annotations
import uuid
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from app.database.models.player import Player
    from app.database.models.npc import NPC

logger = logging.getLogger(__name__)

__all__ = [
    "SessionContext",
    "TurnSummary",
    "PlotThread",
    "NarrativeHook",
    "TimeContext",
    "Entity",
    "EntityType",
    "HookType",
    "ThreadStatus",
    "NarrativeBeat",
]


class EntityType(str, Enum):
    """Tipos de entidades no mundo do jogo."""
    PLAYER = "player"
    NPC_FRIENDLY = "npc_friendly"
    NPC_HOSTILE = "npc_hostile"
    NPC_NEUTRAL = "npc_neutral"
    BEAST = "beast"
    SPIRIT = "spirit"
    OBJECT = "object"


class HookType(str, Enum):
    """Tipos de hooks narrativos que podem ser plantados."""
    FORESHADOWING = "foreshadowing"  # Prenúncio de evento futuro
    CHEKHOV_GUN = "chekhov_gun"      # Item/detalhe que será importante depois
    CHARACTER_THREAD = "character"    # Desenvolvimento de personagem pendente
    MYSTERY = "mystery"               # Mistério a ser resolvido
    THREAT = "threat"                 # Ameaça futura
    PROMISE = "promise"               # Promessa feita (pelo player ou NPC)
    DEBT = "debt"                     # Dívida (favor, dinheiro, vida)


class ThreadStatus(str, Enum):
    """Status de uma thread de plot."""
    ACTIVE = "active"           # Em andamento
    PAUSED = "paused"           # Pausada (player foi fazer outra coisa)
    CLIMAX = "climax"           # Chegando ao clímax
    RESOLVED = "resolved"       # Resolvida
    ABANDONED = "abandoned"     # Abandonada pelo player


class NarrativeBeat(str, Enum):
    """Beats do arco narrativo (estrutura de 5 atos)."""
    SETUP = "setup"             # Introdução, mundo normal
    RISING_ACTION = "rising"    # Conflito crescendo
    CLIMAX = "climax"           # Ponto mais alto de tensão
    FALLING_ACTION = "falling"  # Consequências
    RESOLUTION = "resolution"   # Novo equilíbrio


@dataclass
class Entity:
    """
    Representação simplificada de uma entidade presente na cena.
    Usada para contexto rápido sem carregar objetos completos do DB.
    """
    id: int
    name: str
    entity_type: EntityType
    species: str = "human"           # human, beast, spirit, demon, etc
    gender: str = "unknown"          # male, female, unknown
    can_speak: bool = True           # Pode falar?
    emotional_state: str = "neutral" # Estado emocional atual
    rank: int = 1                    # Nível de poder
    current_hp_percent: float = 1.0  # HP como porcentagem (0.0-1.0)
    disposition_to_player: str = "neutral"  # friendly, hostile, neutral
    notable_traits: List[str] = field(default_factory=list)
    
    @classmethod
    def from_npc(cls, npc: "NPC") -> "Entity":
        """Cria Entity a partir de um modelo NPC."""
        entity_type = EntityType.NPC_HOSTILE if npc.emotional_state == "hostile" else (
            EntityType.NPC_FRIENDLY if npc.emotional_state == "friendly" else EntityType.NPC_NEUTRAL
        )
        
        # Determinar espécie baseado no nome (heurística até ter campo species)
        species = getattr(npc, 'species', None)
        if not species:
            name_lower = npc.name.lower()
            if any(beast in name_lower for beast in ['javali', 'lobo', 'urso', 'serpente', 'tigre', 'águia', 'raposa']):
                species = "beast"
                entity_type = EntityType.BEAST
            elif any(spirit in name_lower for spirit in ['espírito', 'fantasma', 'wraith', 'soul']):
                species = "spirit"
                entity_type = EntityType.SPIRIT
            else:
                species = "human"
        
        # Determinar se pode falar
        can_speak = getattr(npc, 'can_speak', None)
        if can_speak is None:
            can_speak = species == "human"  # Só humanos falam por padrão
        
        # Determinar gênero
        gender = getattr(npc, 'gender', 'unknown')
        
        hp_percent = npc.current_hp / npc.max_hp if npc.max_hp > 0 else 1.0
        
        return cls(
            id=npc.id,
            name=npc.name,
            entity_type=entity_type,
            species=species,
            gender=gender,
            can_speak=can_speak,
            emotional_state=npc.emotional_state,
            rank=npc.rank,
            current_hp_percent=hp_percent,
            disposition_to_player=npc.emotional_state,
            notable_traits=npc.personality_traits[:3] if npc.personality_traits else []
        )
    
    @classmethod
    def from_player(cls, player: "Player") -> "Entity":
        """Cria Entity a partir de um modelo Player."""
        hp_percent = player.current_hp / player.max_hp if player.max_hp > 0 else 1.0
        
        return cls(
            id=player.id,
            name=player.name,
            entity_type=EntityType.PLAYER,
            species="human",
            gender="unknown",  # Player define
            can_speak=True,
            emotional_state="determined",
            rank=player.cultivation_tier,
            current_hp_percent=hp_percent,
            disposition_to_player="self",
            notable_traits=[]
        )


@dataclass
class TimeContext:
    """
    Contexto temporal da sessão.
    Sincronizado com Chronos mas mantém snapshot local.
    """
    current_datetime: datetime
    time_of_day: str      # dawn, morning, noon, afternoon, dusk, evening, night, midnight
    season: str           # Spring, Summer, Autumn, Winter
    turn_number: int
    days_elapsed: int     # Dias desde início do jogo
    
    @classmethod
    def from_chronos(cls, chronos) -> "TimeContext":
        """Cria TimeContext a partir do Chronos global."""
        dt = chronos.get_current_datetime()
        start_date = datetime.strptime("01-01-1000", "%d-%m-%Y")
        days_elapsed = (dt - start_date).days
        
        return cls(
            current_datetime=dt,
            time_of_day=chronos.get_time_of_day(),
            season=chronos.get_season(),
            turn_number=chronos.turn,
            days_elapsed=days_elapsed
        )
    
    def get_formatted_date(self) -> str:
        """Retorna data formatada para narrativa."""
        return self.current_datetime.strftime("%d do Mês %m, Ano %Y")
    
    def get_time_description(self) -> str:
        """Retorna descrição do período do dia."""
        descriptions = {
            "dawn": "Aurora",
            "morning": "Manhã",
            "noon": "Meio-dia",
            "afternoon": "Tarde",
            "dusk": "Crepúsculo",
            "evening": "Noite",
            "night": "Noite profunda",
            "midnight": "Madrugada"
        }
        return descriptions.get(self.time_of_day, "Desconhecido")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_datetime": self.current_datetime.isoformat(),
            "time_of_day": self.time_of_day,
            "season": self.season,
            "turn_number": self.turn_number,
            "days_elapsed": self.days_elapsed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimeContext":
        return cls(
            current_datetime=datetime.fromisoformat(data["current_datetime"]),
            time_of_day=data["time_of_day"],
            season=data["season"],
            turn_number=data["turn_number"],
            days_elapsed=data["days_elapsed"]
        )


@dataclass
class TurnSummary:
    """
    Resumo de um turno para histórico.
    Mantido em memória para contexto rápido.
    """
    turn_number: int
    player_input: str
    interpreted_action: str           # O que o Referee entendeu
    action_result: Optional[str]      # Resultado mecânico (dano, etc)
    scene_description: str            # Narração do Narrator
    location: str
    npcs_involved: List[str]          # Nomes dos NPCs envolvidos
    emotional_beat: str               # Como o turno afetou a tensão
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Eventos importantes que ocorreram
    combat_occurred: bool = False
    npc_killed: Optional[str] = None  # Nome do NPC morto, se houver
    item_obtained: Optional[str] = None
    location_changed: bool = False
    new_location: Optional[str] = None
    
    def get_compact_summary(self) -> str:
        """Retorna resumo compacto para contexto de IA."""
        parts = [f"Turno {self.turn_number}: {self.player_input}"]
        
        if self.combat_occurred:
            parts.append("[COMBATE]")
        if self.npc_killed:
            parts.append(f"[MATOU: {self.npc_killed}]")
        if self.location_changed:
            parts.append(f"[MOVEU: {self.new_location}]")
        if self.item_obtained:
            parts.append(f"[OBTEVE: {self.item_obtained}]")
            
        parts.append(f"-> {self.interpreted_action}")
        
        return " ".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_number": self.turn_number,
            "player_input": self.player_input,
            "interpreted_action": self.interpreted_action,
            "action_result": self.action_result,
            "scene_description": self.scene_description,
            "location": self.location,
            "npcs_involved": self.npcs_involved,
            "emotional_beat": self.emotional_beat,
            "timestamp": self.timestamp.isoformat(),
            "combat_occurred": self.combat_occurred,
            "npc_killed": self.npc_killed,
            "item_obtained": self.item_obtained,
            "location_changed": self.location_changed,
            "new_location": self.new_location
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TurnSummary":
        return cls(
            turn_number=data["turn_number"],
            player_input=data["player_input"],
            interpreted_action=data["interpreted_action"],
            action_result=data.get("action_result"),
            scene_description=data["scene_description"],
            location=data["location"],
            npcs_involved=data["npcs_involved"],
            emotional_beat=data["emotional_beat"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            combat_occurred=data.get("combat_occurred", False),
            npc_killed=data.get("npc_killed"),
            item_obtained=data.get("item_obtained"),
            location_changed=data.get("location_changed", False),
            new_location=data.get("new_location")
        )


@dataclass
class NarrativeHook:
    """
    Hook narrativo plantado para uso futuro.
    Pode ser foreshadowing, chekhov gun, ou thread de personagem.
    """
    id: str
    hook_type: HookType
    description: str              # O que foi plantado
    planted_turn: int             # Turno em que foi plantado
    planted_location: str         # Onde foi plantado
    target_entity: Optional[str]  # NPC/objeto relacionado
    resolution_hint: Optional[str] = None  # Como pode ser resolvido
    urgency: int = 0              # 0=baixa, 1=média, 2=alta
    expires_turn: Optional[int] = None  # Turno limite (se houver)
    resolved: bool = False
    resolved_turn: Optional[int] = None
    
    @classmethod
    def create(
        cls,
        hook_type: HookType,
        description: str,
        current_turn: int,
        location: str,
        target_entity: Optional[str] = None,
        urgency: int = 0,
        expires_in_turns: Optional[int] = None
    ) -> "NarrativeHook":
        """Factory method para criar novo hook."""
        expires_turn = None
        if expires_in_turns:
            expires_turn = current_turn + expires_in_turns
            
        return cls(
            id=str(uuid.uuid4())[:8],
            hook_type=hook_type,
            description=description,
            planted_turn=current_turn,
            planted_location=location,
            target_entity=target_entity,
            urgency=urgency,
            expires_turn=expires_turn
        )
    
    def is_expired(self, current_turn: int) -> bool:
        """Verifica se o hook expirou."""
        if self.expires_turn is None:
            return False
        return current_turn > self.expires_turn
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "hook_type": self.hook_type.value,
            "description": self.description,
            "planted_turn": self.planted_turn,
            "planted_location": self.planted_location,
            "target_entity": self.target_entity,
            "resolution_hint": self.resolution_hint,
            "urgency": self.urgency,
            "expires_turn": self.expires_turn,
            "resolved": self.resolved,
            "resolved_turn": self.resolved_turn
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NarrativeHook":
        return cls(
            id=data["id"],
            hook_type=HookType(data["hook_type"]),
            description=data["description"],
            planted_turn=data["planted_turn"],
            planted_location=data["planted_location"],
            target_entity=data.get("target_entity"),
            resolution_hint=data.get("resolution_hint"),
            urgency=data.get("urgency", 0),
            expires_turn=data.get("expires_turn"),
            resolved=data.get("resolved", False),
            resolved_turn=data.get("resolved_turn")
        )


@dataclass
class PlotThread:
    """
    Thread de plot ativa - uma linha narrativa em andamento.
    Pode ser quest, vingança, romance, investigação, etc.
    """
    id: str
    title: str                    # Nome curto da thread
    description: str              # Descrição detalhada
    status: ThreadStatus
    started_turn: int
    started_location: str
    
    # Envolvidos
    primary_npcs: List[str]       # NPCs principais desta thread
    related_locations: List[str]  # Locais relacionados
    
    # Progresso
    milestones: List[str] = field(default_factory=list)  # Marcos alcançados
    current_objective: Optional[str] = None               # Objetivo atual
    tension_contribution: float = 0.0  # Quanto contribui para tensão (0.0-1.0)
    
    # Timing
    last_interaction_turn: int = 0
    turns_since_last_interaction: int = 0
    
    @classmethod
    def create(
        cls,
        title: str,
        description: str,
        current_turn: int,
        location: str,
        primary_npcs: List[str] = None,
        initial_objective: Optional[str] = None
    ) -> "PlotThread":
        """Factory method para criar nova thread."""
        return cls(
            id=str(uuid.uuid4())[:8],
            title=title,
            description=description,
            status=ThreadStatus.ACTIVE,
            started_turn=current_turn,
            started_location=location,
            primary_npcs=primary_npcs or [],
            related_locations=[location],
            current_objective=initial_objective,
            last_interaction_turn=current_turn
        )
    
    def update_interaction(self, current_turn: int) -> None:
        """Atualiza timestamp de última interação."""
        self.turns_since_last_interaction = 0
        self.last_interaction_turn = current_turn
    
    def age(self, turns: int = 1) -> None:
        """Envelhece a thread (aumenta tempo desde última interação)."""
        self.turns_since_last_interaction += turns
        
        # Auto-pause se muito tempo sem interação
        if self.turns_since_last_interaction > 20 and self.status == ThreadStatus.ACTIVE:
            self.status = ThreadStatus.PAUSED
            logger.info(f"PlotThread '{self.title}' pausada por inatividade")
    
    def add_milestone(self, milestone: str) -> None:
        """Adiciona marco alcançado."""
        self.milestones.append(milestone)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "started_turn": self.started_turn,
            "started_location": self.started_location,
            "primary_npcs": self.primary_npcs,
            "related_locations": self.related_locations,
            "milestones": self.milestones,
            "current_objective": self.current_objective,
            "tension_contribution": self.tension_contribution,
            "last_interaction_turn": self.last_interaction_turn,
            "turns_since_last_interaction": self.turns_since_last_interaction
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlotThread":
        thread = cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            status=ThreadStatus(data["status"]),
            started_turn=data["started_turn"],
            started_location=data["started_location"],
            primary_npcs=data["primary_npcs"],
            related_locations=data["related_locations"],
            milestones=data.get("milestones", []),
            current_objective=data.get("current_objective"),
            tension_contribution=data.get("tension_contribution", 0.0),
            last_interaction_turn=data.get("last_interaction_turn", 0),
            turns_since_last_interaction=data.get("turns_since_last_interaction", 0)
        )
        return thread


@dataclass
class SessionContext:
    """
    Contexto completo de uma sessão de jogo.
    Mantém estado que persiste entre turnos e permite
    que a IA tenha memória de curto prazo consistente.
    """
    session_id: str
    player_id: int
    player_name: str
    
    # Estado atual
    current_location: str
    present_entities: List[Entity] = field(default_factory=list)
    
    # Histórico recente (últimos N turnos em memória)
    turn_history: List[TurnSummary] = field(default_factory=list)
    max_history_size: int = 20  # Manter últimos 20 turnos em memória
    
    # Contexto temporal
    time_context: Optional[TimeContext] = None
    
    # Narrativa
    current_beat: NarrativeBeat = NarrativeBeat.SETUP
    tension_level: float = 0.0  # 0.0 (calmo) a 1.0 (clímax)
    
    # Hooks e Threads
    pending_hooks: List[NarrativeHook] = field(default_factory=list)
    resolved_hooks: List[NarrativeHook] = field(default_factory=list)
    active_threads: List[PlotThread] = field(default_factory=list)
    
    # Combate atual (se houver)
    in_combat: bool = False
    combat_round: int = 0
    combat_participants: List[str] = field(default_factory=list)
    
    # Flags de estado
    last_action_type: str = "none"  # attack, talk, move, observe, etc
    consecutive_combat_turns: int = 0
    consecutive_peaceful_turns: int = 0
    
    # Metadados
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    total_turns: int = 0
    
    @classmethod
    def create_new(
        cls,
        player_id: int,
        player_name: str,
        starting_location: str = "Início da Jornada"
    ) -> "SessionContext":
        """Cria novo contexto de sessão para um jogador."""
        return cls(
            session_id=str(uuid.uuid4()),
            player_id=player_id,
            player_name=player_name,
            current_location=starting_location
        )
    
    # ==================== MÉTODOS DE TURNO ====================
    
    def add_turn(self, turn: TurnSummary) -> None:
        """
        Adiciona um turno ao histórico.
        Mantém apenas os últimos max_history_size turnos.
        """
        self.turn_history.append(turn)
        self.total_turns += 1
        
        # Manter tamanho do histórico
        if len(self.turn_history) > self.max_history_size:
            self.turn_history = self.turn_history[-self.max_history_size:]
        
        # Atualizar flags de estado
        self._update_state_flags(turn)
        
        # Atualizar tensão
        self._update_tension(turn)
        
        # Envelhecer threads
        for thread in self.active_threads:
            if thread.status == ThreadStatus.ACTIVE:
                thread.age()
        
        self.last_updated = datetime.utcnow()
        logger.debug(f"Turno {turn.turn_number} adicionado. Total: {self.total_turns}")
    
    def _update_state_flags(self, turn: TurnSummary) -> None:
        """Atualiza flags de estado baseado no turno."""
        self.last_action_type = turn.interpreted_action.split()[0] if turn.interpreted_action else "none"
        
        if turn.combat_occurred:
            self.consecutive_combat_turns += 1
            self.consecutive_peaceful_turns = 0
            self.in_combat = True
        else:
            self.consecutive_peaceful_turns += 1
            if self.consecutive_peaceful_turns >= 2:
                self.in_combat = False
                self.consecutive_combat_turns = 0
        
        if turn.location_changed and turn.new_location:
            self.current_location = turn.new_location
    
    def _update_tension(self, turn: TurnSummary) -> None:
        """
        Atualiza nível de tensão baseado nos eventos do turno.
        A tensão naturalmente decai com turnos pacíficos e
        aumenta com combate/eventos dramáticos.
        """
        # Fatores de aumento
        if turn.combat_occurred:
            self.tension_level += 0.15
        if turn.npc_killed:
            self.tension_level += 0.1
        if turn.emotional_beat == "climax":
            self.tension_level += 0.2
        
        # Fatores de diminuição
        if not turn.combat_occurred and self.consecutive_peaceful_turns > 0:
            self.tension_level -= 0.05
        if turn.emotional_beat == "resolution":
            self.tension_level -= 0.15
        
        # Contribuição das threads
        thread_tension = sum(t.tension_contribution for t in self.active_threads if t.status == ThreadStatus.ACTIVE)
        self.tension_level = (self.tension_level + thread_tension) / 2
        
        # Clamp entre 0 e 1
        self.tension_level = max(0.0, min(1.0, self.tension_level))
        
        # Atualizar beat narrativo baseado na tensão
        self._update_narrative_beat()
    
    def _update_narrative_beat(self) -> None:
        """Atualiza o beat narrativo baseado na tensão."""
        if self.tension_level < 0.2:
            self.current_beat = NarrativeBeat.SETUP
        elif self.tension_level < 0.4:
            self.current_beat = NarrativeBeat.RISING_ACTION
        elif self.tension_level < 0.7:
            if self.current_beat == NarrativeBeat.CLIMAX:
                self.current_beat = NarrativeBeat.FALLING_ACTION
            else:
                self.current_beat = NarrativeBeat.RISING_ACTION
        elif self.tension_level < 0.85:
            self.current_beat = NarrativeBeat.CLIMAX
        else:
            self.current_beat = NarrativeBeat.CLIMAX
    
    def get_last_n_turns(self, n: int) -> List[TurnSummary]:
        """Retorna os últimos N turnos."""
        return self.turn_history[-n:] if n > 0 else []
    
    def get_turn_context_string(self, n: int = 5) -> str:
        """
        Retorna string formatada com contexto dos últimos N turnos.
        Útil para incluir no prompt da IA.
        """
        turns = self.get_last_n_turns(n)
        if not turns:
            return "Nenhum histórico de turnos disponível."
        
        lines = ["=== HISTÓRICO RECENTE ==="]
        for turn in turns:
            lines.append(turn.get_compact_summary())
        
        return "\n".join(lines)
    
    # ==================== MÉTODOS DE ENTIDADES ====================
    
    def get_present_entities(self) -> List[Entity]:
        """Retorna lista de entidades presentes na cena."""
        return self.present_entities
    
    def set_present_entities(self, entities: List[Entity]) -> None:
        """Define as entidades presentes na cena."""
        self.present_entities = entities
        logger.debug(f"Entidades atualizadas: {[e.name for e in entities]}")
    
    def add_entity(self, entity: Entity) -> None:
        """Adiciona uma entidade à cena."""
        if not any(e.id == entity.id and e.entity_type == entity.entity_type for e in self.present_entities):
            self.present_entities.append(entity)
    
    def remove_entity(self, entity_id: int, entity_type: EntityType) -> None:
        """Remove uma entidade da cena."""
        self.present_entities = [
            e for e in self.present_entities 
            if not (e.id == entity_id and e.entity_type == entity_type)
        ]
    
    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        """Busca entidade por nome (case insensitive)."""
        name_lower = name.lower()
        for entity in self.present_entities:
            if entity.name.lower() == name_lower:
                return entity
        return None
    
    def get_hostile_entities(self) -> List[Entity]:
        """Retorna apenas entidades hostis."""
        return [e for e in self.present_entities if e.disposition_to_player == "hostile"]
    
    def get_friendly_entities(self) -> List[Entity]:
        """Retorna apenas entidades amigáveis."""
        return [e for e in self.present_entities if e.disposition_to_player == "friendly"]
    
    def get_speaking_entities(self) -> List[Entity]:
        """Retorna apenas entidades que podem falar."""
        return [e for e in self.present_entities if e.can_speak]
    
    def get_entity_context_string(self) -> str:
        """Retorna string formatada com entidades presentes."""
        if not self.present_entities:
            return "Nenhuma criatura ou pessoa visível nas proximidades."
        
        lines = ["=== ENTIDADES PRESENTES ==="]
        for entity in self.present_entities:
            hp_status = "saudável" if entity.current_hp_percent > 0.7 else (
                "ferido" if entity.current_hp_percent > 0.3 else "gravemente ferido"
            )
            can_speak = "pode falar" if entity.can_speak else "não fala"
            lines.append(
                f"- {entity.name} ({entity.species}, {entity.gender}): "
                f"{entity.emotional_state}, {hp_status}, {can_speak}"
            )
        
        return "\n".join(lines)
    
    # ==================== MÉTODOS DE TENSÃO ====================
    
    def update_tension(self, delta: float) -> None:
        """Atualiza tensão manualmente."""
        self.tension_level = max(0.0, min(1.0, self.tension_level + delta))
        self._update_narrative_beat()
    
    def get_tension_description(self) -> str:
        """Retorna descrição textual do nível de tensão."""
        if self.tension_level < 0.2:
            return "tranquilo"
        elif self.tension_level < 0.4:
            return "tenso"
        elif self.tension_level < 0.6:
            return "perigoso"
        elif self.tension_level < 0.8:
            return "intenso"
        else:
            return "crítico"
    
    # ==================== MÉTODOS DE HOOKS ====================
    
    def plant_hook(self, hook: NarrativeHook) -> None:
        """Planta um novo hook narrativo."""
        self.pending_hooks.append(hook)
        logger.info(f"Hook plantado: {hook.hook_type.value} - {hook.description[:50]}")
    
    def resolve_hook(self, hook_id: str, resolution_turn: int) -> Optional[NarrativeHook]:
        """Resolve um hook e move para lista de resolvidos."""
        for i, hook in enumerate(self.pending_hooks):
            if hook.id == hook_id:
                hook.resolved = True
                hook.resolved_turn = resolution_turn
                self.resolved_hooks.append(hook)
                self.pending_hooks.pop(i)
                logger.info(f"Hook resolvido: {hook.description[:50]}")
                return hook
        return None
    
    def get_hooks_by_type(self, hook_type: HookType) -> List[NarrativeHook]:
        """Retorna hooks pendentes de um tipo específico."""
        return [h for h in self.pending_hooks if h.hook_type == hook_type]
    
    def get_urgent_hooks(self) -> List[NarrativeHook]:
        """Retorna hooks com urgência alta."""
        return [h for h in self.pending_hooks if h.urgency >= 2]
    
    def get_expiring_hooks(self, current_turn: int, turns_ahead: int = 5) -> List[NarrativeHook]:
        """Retorna hooks que vão expirar em breve."""
        threshold = current_turn + turns_ahead
        return [
            h for h in self.pending_hooks 
            if h.expires_turn and h.expires_turn <= threshold
        ]
    
    def cleanup_expired_hooks(self, current_turn: int) -> List[NarrativeHook]:
        """Remove hooks expirados e retorna lista dos removidos."""
        expired = [h for h in self.pending_hooks if h.is_expired(current_turn)]
        self.pending_hooks = [h for h in self.pending_hooks if not h.is_expired(current_turn)]
        
        for hook in expired:
            logger.warning(f"Hook expirou: {hook.description[:50]}")
        
        return expired
    
    # ==================== MÉTODOS DE THREADS ====================
    
    def add_plot_thread(self, thread: PlotThread) -> None:
        """Adiciona nova thread de plot."""
        self.active_threads.append(thread)
        logger.info(f"Thread criada: {thread.title}")
    
    def get_thread(self, thread_id: str) -> Optional[PlotThread]:
        """Busca thread por ID."""
        for thread in self.active_threads:
            if thread.id == thread_id:
                return thread
        return None
    
    def get_active_threads(self) -> List[PlotThread]:
        """Retorna apenas threads ativas."""
        return [t for t in self.active_threads if t.status == ThreadStatus.ACTIVE]
    
    def update_thread(self, thread_id: str, current_turn: int, milestone: Optional[str] = None) -> None:
        """Atualiza interação com uma thread."""
        thread = self.get_thread(thread_id)
        if thread:
            thread.update_interaction(current_turn)
            if milestone:
                thread.add_milestone(milestone)
    
    def resolve_thread(self, thread_id: str) -> None:
        """Marca uma thread como resolvida."""
        thread = self.get_thread(thread_id)
        if thread:
            thread.status = ThreadStatus.RESOLVED
            logger.info(f"Thread resolvida: {thread.title}")
    
    # ==================== MÉTODOS DE COMBATE ====================
    
    def start_combat(self, participants: List[str]) -> None:
        """Inicia combate."""
        self.in_combat = True
        self.combat_round = 1
        self.combat_participants = participants
        self.update_tension(0.2)
        logger.info(f"Combate iniciado com: {participants}")
    
    def advance_combat_round(self) -> None:
        """Avança para próximo round de combate."""
        self.combat_round += 1
    
    def end_combat(self) -> None:
        """Encerra combate."""
        self.in_combat = False
        self.combat_round = 0
        self.combat_participants = []
        self.consecutive_combat_turns = 0
        logger.info("Combate encerrado")
    
    # ==================== SERIALIZAÇÃO ====================
    
    def serialize(self) -> Dict[str, Any]:
        """Serializa contexto para persistência."""
        return {
            "session_id": self.session_id,
            "player_id": self.player_id,
            "player_name": self.player_name,
            "current_location": self.current_location,
            "present_entities": [asdict(e) for e in self.present_entities],
            "turn_history": [t.to_dict() for t in self.turn_history],
            "time_context": self.time_context.to_dict() if self.time_context else None,
            "current_beat": self.current_beat.value,
            "tension_level": self.tension_level,
            "pending_hooks": [h.to_dict() for h in self.pending_hooks],
            "resolved_hooks": [h.to_dict() for h in self.resolved_hooks],
            "active_threads": [t.to_dict() for t in self.active_threads],
            "in_combat": self.in_combat,
            "combat_round": self.combat_round,
            "combat_participants": self.combat_participants,
            "last_action_type": self.last_action_type,
            "consecutive_combat_turns": self.consecutive_combat_turns,
            "consecutive_peaceful_turns": self.consecutive_peaceful_turns,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "total_turns": self.total_turns
        }
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "SessionContext":
        """Deserializa contexto de dados persistidos."""
        # Reconstruir entidades
        entities = []
        for e_data in data.get("present_entities", []):
            entity_type = EntityType(e_data["entity_type"])
            entities.append(Entity(
                id=e_data["id"],
                name=e_data["name"],
                entity_type=entity_type,
                species=e_data.get("species", "human"),
                gender=e_data.get("gender", "unknown"),
                can_speak=e_data.get("can_speak", True),
                emotional_state=e_data.get("emotional_state", "neutral"),
                rank=e_data.get("rank", 1),
                current_hp_percent=e_data.get("current_hp_percent", 1.0),
                disposition_to_player=e_data.get("disposition_to_player", "neutral"),
                notable_traits=e_data.get("notable_traits", [])
            ))
        
        # Reconstruir histórico de turnos
        turns = [TurnSummary.from_dict(t) for t in data.get("turn_history", [])]
        
        # Reconstruir time context
        time_ctx = None
        if data.get("time_context"):
            time_ctx = TimeContext.from_dict(data["time_context"])
        
        # Reconstruir hooks
        pending_hooks = [NarrativeHook.from_dict(h) for h in data.get("pending_hooks", [])]
        resolved_hooks = [NarrativeHook.from_dict(h) for h in data.get("resolved_hooks", [])]
        
        # Reconstruir threads
        threads = [PlotThread.from_dict(t) for t in data.get("active_threads", [])]
        
        return cls(
            session_id=data["session_id"],
            player_id=data["player_id"],
            player_name=data["player_name"],
            current_location=data["current_location"],
            present_entities=entities,
            turn_history=turns,
            time_context=time_ctx,
            current_beat=NarrativeBeat(data.get("current_beat", "setup")),
            tension_level=data.get("tension_level", 0.0),
            pending_hooks=pending_hooks,
            resolved_hooks=resolved_hooks,
            active_threads=threads,
            in_combat=data.get("in_combat", False),
            combat_round=data.get("combat_round", 0),
            combat_participants=data.get("combat_participants", []),
            last_action_type=data.get("last_action_type", "none"),
            consecutive_combat_turns=data.get("consecutive_combat_turns", 0),
            consecutive_peaceful_turns=data.get("consecutive_peaceful_turns", 0),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            total_turns=data.get("total_turns", 0)
        )
    
    def to_json(self) -> str:
        """Serializa para JSON string."""
        return json.dumps(self.serialize(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "SessionContext":
        """Deserializa de JSON string."""
        return cls.deserialize(json.loads(json_str))
    
    # ==================== CONTEXTO PARA IA ====================
    
    def get_full_context_for_ai(self) -> str:
        """
        Retorna contexto completo formatado para prompt de IA.
        Usado pelo Narrator e outros agentes.
        """
        parts = []
        
        # Tempo
        if self.time_context:
            parts.append(f"📅 {self.time_context.get_formatted_date()} | {self.time_context.get_time_description()}")
        
        # Localização
        parts.append(f"📍 Localização: {self.current_location}")
        
        # Tensão
        parts.append(f"⚡ Atmosfera: {self.get_tension_description()} (tensão: {self.tension_level:.1%})")
        parts.append(f"🎭 Beat Narrativo: {self.current_beat.value}")
        
        # Combate
        if self.in_combat:
            parts.append(f"⚔️ EM COMBATE - Round {self.combat_round}")
            parts.append(f"   Participantes: {', '.join(self.combat_participants)}")
        
        # Entidades
        parts.append("")
        parts.append(self.get_entity_context_string())
        
        # Histórico
        parts.append("")
        parts.append(self.get_turn_context_string(5))
        
        # Hooks urgentes
        urgent = self.get_urgent_hooks()
        if urgent:
            parts.append("")
            parts.append("=== HOOKS URGENTES ===")
            for hook in urgent[:3]:
                parts.append(f"- [{hook.hook_type.value}] {hook.description}")
        
        # Threads ativas
        active_threads = self.get_active_threads()
        if active_threads:
            parts.append("")
            parts.append("=== THREADS ATIVAS ===")
            for thread in active_threads[:3]:
                parts.append(f"- {thread.title}: {thread.current_objective or 'Em andamento'}")
        
        return "\n".join(parts)


# Singleton para sessão atual (por worker/request)
_current_session: Optional[SessionContext] = None


def get_current_session() -> Optional[SessionContext]:
    """Retorna sessão atual (para uso em contexto de request)."""
    global _current_session
    return _current_session


def set_current_session(session: SessionContext) -> None:
    """Define sessão atual."""
    global _current_session
    _current_session = session
    logger.debug(f"Sessão definida: {session.session_id}")


def clear_current_session() -> None:
    """Limpa sessão atual."""
    global _current_session
    _current_session = None
