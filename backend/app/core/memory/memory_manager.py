"""
Hierarchical Memory Manager - Orquestrador do Sistema de Memória
GEM RPG ORBIS - Arquitetura Cognitiva

Este módulo orquestra os três stores de memória:
1. Episodic - Eventos específicos
2. Semantic - Fatos extraídos
3. Procedural - Padrões de comportamento

Fornece interface unificada para remember() e recall().
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from enum import Enum

from app.core.memory.episodic import (
    EpisodicMemory, EpisodicStore, EmotionalValence, TimeRange
)
from app.core.memory.semantic import (
    SemanticFact, SemanticStore, FactType, FactConfidence
)
from app.core.memory.procedural import (
    BehaviorPattern, ProceduralStore, PatternType
)

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession
    from app.core.session_context import SessionContext

logger = logging.getLogger(__name__)

__all__ = [
    "HierarchicalMemory",
    "MemoryBundle",
    "GameEvent",
    "EventType",
]


class EventType(str, Enum):
    """Tipos de eventos do jogo para processamento de memória."""
    COMBAT_ATTACK = "combat_attack"
    COMBAT_DEFEND = "combat_defend"
    COMBAT_KILL = "combat_kill"
    COMBAT_FLEE = "combat_flee"
    COMBAT_DEFEAT = "combat_defeat"
    
    DIALOGUE_FRIENDLY = "dialogue_friendly"
    DIALOGUE_HOSTILE = "dialogue_hostile"
    DIALOGUE_NEUTRAL = "dialogue_neutral"
    DIALOGUE_THREAT = "dialogue_threat"
    DIALOGUE_BARGAIN = "dialogue_bargain"
    
    OBSERVATION = "observation"
    DISCOVERY = "discovery"
    TRAVEL = "travel"
    
    TRADE_BUY = "trade_buy"
    TRADE_SELL = "trade_sell"
    
    HELP_GIVEN = "help_given"
    HELP_RECEIVED = "help_received"
    
    BETRAYAL = "betrayal"
    PROMISE = "promise"
    
    CULTIVATION = "cultivation"
    BREAKTHROUGH = "breakthrough"


@dataclass
class GameEvent:
    """
    Evento do jogo para processamento de memória.
    Usado como input para remember().
    """
    event_type: EventType
    description: str
    location: str
    game_time: str  # "DD-MM-YYYY HH:MM"
    
    # Participantes
    actor_name: str  # Quem fez a ação
    actor_id: Optional[int] = None
    target_name: Optional[str] = None
    target_id: Optional[int] = None
    other_participants: List[str] = field(default_factory=list)
    
    # Resultado
    outcome: Optional[str] = None  # "success", "failure", "partial"
    damage_dealt: Optional[float] = None
    damage_received: Optional[float] = None
    item_exchanged: Optional[str] = None
    
    # Contexto emocional
    emotional_impact: Optional[EmotionalValence] = None
    
    # Metadados
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def get_participants(self) -> List[str]:
        """Retorna lista de todos os participantes."""
        participants = [self.actor_name]
        if self.target_name:
            participants.append(self.target_name)
        participants.extend(self.other_participants)
        return list(set(participants))  # Remove duplicatas
    
    def calculate_importance(self) -> float:
        """
        Calcula importância do evento (0.0-1.0).
        Eventos de combate, morte, traição são mais importantes.
        """
        base_importance = {
            EventType.COMBAT_KILL: 0.9,
            EventType.COMBAT_DEFEAT: 0.85,
            EventType.BETRAYAL: 0.95,
            EventType.BREAKTHROUGH: 0.8,
            EventType.COMBAT_ATTACK: 0.6,
            EventType.COMBAT_FLEE: 0.5,
            EventType.DIALOGUE_THREAT: 0.7,
            EventType.HELP_GIVEN: 0.6,
            EventType.HELP_RECEIVED: 0.6,
            EventType.PROMISE: 0.7,
            EventType.DISCOVERY: 0.65,
            EventType.TRADE_BUY: 0.3,
            EventType.TRADE_SELL: 0.3,
            EventType.DIALOGUE_FRIENDLY: 0.4,
            EventType.DIALOGUE_NEUTRAL: 0.2,
            EventType.OBSERVATION: 0.2,
            EventType.TRAVEL: 0.1,
        }
        
        importance = base_importance.get(self.event_type, 0.5)
        
        # Modificadores
        if self.emotional_impact:
            if self.emotional_impact in [EmotionalValence.VERY_NEGATIVE, EmotionalValence.VERY_POSITIVE]:
                importance = min(1.0, importance + 0.2)
            elif self.emotional_impact in [EmotionalValence.NEGATIVE, EmotionalValence.POSITIVE]:
                importance = min(1.0, importance + 0.1)
        
        if self.damage_dealt and self.damage_dealt > 50:
            importance = min(1.0, importance + 0.1)
        
        if self.damage_received and self.damage_received > 50:
            importance = min(1.0, importance + 0.15)
        
        return importance
    
    def infer_emotional_impact(self) -> EmotionalValence:
        """Infere impacto emocional se não especificado."""
        if self.emotional_impact:
            return self.emotional_impact
        
        # Mapeamento de tipo para valência
        negative_types = [
            EventType.COMBAT_ATTACK, EventType.COMBAT_DEFEAT,
            EventType.DIALOGUE_HOSTILE, EventType.DIALOGUE_THREAT,
            EventType.BETRAYAL
        ]
        very_negative_types = [EventType.COMBAT_KILL]
        positive_types = [
            EventType.HELP_RECEIVED, EventType.DIALOGUE_FRIENDLY,
            EventType.TRADE_BUY
        ]
        very_positive_types = [EventType.BREAKTHROUGH, EventType.HELP_GIVEN]
        
        if self.event_type in very_negative_types:
            return EmotionalValence.VERY_NEGATIVE
        elif self.event_type in negative_types:
            return EmotionalValence.NEGATIVE
        elif self.event_type in very_positive_types:
            return EmotionalValence.VERY_POSITIVE
        elif self.event_type in positive_types:
            return EmotionalValence.POSITIVE
        else:
            return EmotionalValence.NEUTRAL


@dataclass
class MemoryBundle:
    """
    Pacote de memórias retornado por recall().
    Contém informações de todos os tipos de memória relevantes.
    """
    # Memórias episódicas relevantes
    episodic_memories: List[EpisodicMemory] = field(default_factory=list)
    
    # Fatos semânticos relevantes
    semantic_facts: List[SemanticFact] = field(default_factory=list)
    
    # Padrões comportamentais
    behavior_patterns: List[BehaviorPattern] = field(default_factory=list)
    
    # Resumos para uso em prompts
    episodic_summary: str = ""
    semantic_summary: str = ""
    behavioral_summary: str = ""
    
    # Previsões
    predicted_behavior: Optional[str] = None
    prediction_confidence: float = 0.0
    
    # Contexto emocional
    dominant_emotion: Optional[EmotionalValence] = None
    relationship_stance: str = "neutral"  # friendly, hostile, neutral, wary
    
    def is_empty(self) -> bool:
        """Verifica se o bundle está vazio."""
        return (
            not self.episodic_memories and 
            not self.semantic_facts and 
            not self.behavior_patterns
        )
    
    def get_full_context(self) -> str:
        """Retorna contexto completo formatado para IA."""
        parts = []
        
        if self.episodic_summary:
            parts.append("=== MEMÓRIAS RECENTES ===")
            parts.append(self.episodic_summary)
        
        if self.semantic_summary:
            parts.append("\n=== FATOS CONHECIDOS ===")
            parts.append(self.semantic_summary)
        
        if self.behavioral_summary:
            parts.append("\n=== PADRÕES DE COMPORTAMENTO ===")
            parts.append(self.behavioral_summary)
        
        if self.predicted_behavior:
            parts.append(f"\n=== PREVISÃO ({self.prediction_confidence:.0%} confiança) ===")
            parts.append(f"Comportamento esperado: {self.predicted_behavior}")
        
        if self.dominant_emotion:
            parts.append(f"\nEstado emocional dominante: {self.dominant_emotion.value}")
        
        parts.append(f"Postura em relação ao jogador: {self.relationship_stance}")
        
        return "\n".join(parts)
    
    def get_compact_context(self, max_items: int = 3) -> str:
        """Retorna contexto compacto para prompts menores."""
        parts = []
        
        # Top memórias
        for mem in self.episodic_memories[:max_items]:
            parts.append(f"- {mem.get_summary()}")
        
        # Top fatos
        for fact in self.semantic_facts[:max_items]:
            parts.append(f"- FATO: {fact.get_statement()}")
        
        # Top padrões
        for pattern in self.behavior_patterns[:max_items]:
            parts.append(f"- PADRÃO: {pattern.get_description()}")
        
        if self.predicted_behavior:
            parts.append(f"- PREVISÃO: {self.predicted_behavior}")
        
        return "\n".join(parts) if parts else "Nenhuma memória relevante."


class HierarchicalMemory:
    """
    Orquestrador do sistema de memória hierárquico.
    Gerencia os três stores e fornece interface unificada.
    """
    
    def __init__(self, session: "AsyncSession"):
        self.session = session
        self.episodic_store = EpisodicStore(session)
        self.semantic_store = SemanticStore(session)
        self.procedural_store = ProceduralStore(session)
        
        # Configurações
        self.auto_extract_facts = True
        self.auto_detect_patterns = True
        self.consolidation_threshold = 50  # Consolidar após N memórias
    
    async def remember(
        self,
        entity_id: int,
        event: GameEvent,
        importance_override: Optional[float] = None
    ) -> EpisodicMemory:
        """
        Processa e armazena um evento na memória.
        
        1. Cria memória episódica do evento
        2. Extrai fatos semânticos (se auto_extract_facts)
        3. Detecta padrões (se auto_detect_patterns e suficientes eventos)
        
        Args:
            entity_id: ID da entidade que está lembrando
            event: O evento a ser lembrado
            importance_override: Importância manual (opcional)
        
        Returns:
            A memória episódica criada
        """
        # 1. Calcular importância
        importance = importance_override if importance_override is not None else event.calculate_importance()
        
        # 2. Inferir emoção se não especificada
        emotional_valence = event.infer_emotional_impact()
        
        # 3. Criar memória episódica
        episodic_memory = EpisodicMemory(
            entity_id=entity_id,
            timestamp=event.timestamp,
            game_timestamp=event.game_time,
            location=event.location,
            participants=event.get_participants(),
            event_type=event.event_type.value,
            raw_description=event.description,
            emotional_valence=emotional_valence,
            importance_score=importance,
            metadata={
                "outcome": event.outcome,
                "damage_dealt": event.damage_dealt,
                "damage_received": event.damage_received,
                "item_exchanged": event.item_exchanged,
                **event.metadata
            }
        )
        
        # 4. Persistir memória episódica
        saved_memory = await self.episodic_store.add(episodic_memory)
        
        logger.info(f"Memória criada para entidade {entity_id}: {event.event_type.value}")
        
        # 5. Extrair fatos semânticos (se habilitado)
        if self.auto_extract_facts:
            facts = self._extract_facts_from_event(entity_id, event, saved_memory.id)
            for fact in facts:
                await self.semantic_store.upsert(fact)
        
        # 6. Detectar padrões (se habilitado e suficientes memórias)
        if self.auto_detect_patterns:
            memory_count = await self.episodic_store.count(entity_id)
            if memory_count >= 5 and memory_count % 5 == 0:  # A cada 5 memórias
                recent = await self.episodic_store.get_recent(entity_id, n=10)
                await self.procedural_store.detect_patterns(entity_id, recent)
        
        # 7. Consolidar se necessário
        memory_count = await self.episodic_store.count(entity_id)
        if memory_count >= self.consolidation_threshold:
            await self.consolidate(entity_id)
        
        return saved_memory
    
    def _extract_facts_from_event(
        self,
        entity_id: int,
        event: GameEvent,
        memory_id: Optional[int]
    ) -> List[SemanticFact]:
        """
        Extrai fatos semânticos de um evento.
        Transforma eventos específicos em conhecimento geral.
        """
        facts = []
        
        # Fatos sobre ator
        if event.target_name:
            # Evento de combate
            if event.event_type in [EventType.COMBAT_ATTACK, EventType.COMBAT_KILL]:
                facts.append(SemanticFact(
                    entity_id=entity_id,
                    fact_type=FactType.ENTITY_RELATION,
                    subject=event.actor_name,
                    predicate="é hostil a",
                    object=event.target_name if event.target_id != entity_id else "mim",
                    confidence=FactConfidence.CERTAIN,
                    source_memory_ids=[memory_id] if memory_id else []
                ))
            
            # Evento de ajuda
            elif event.event_type in [EventType.HELP_GIVEN, EventType.HELP_RECEIVED]:
                facts.append(SemanticFact(
                    entity_id=entity_id,
                    fact_type=FactType.ENTITY_RELATION,
                    subject=event.actor_name,
                    predicate="ajudou" if event.event_type == EventType.HELP_GIVEN else "foi ajudado por",
                    object=event.target_name,
                    confidence=FactConfidence.CERTAIN,
                    source_memory_ids=[memory_id] if memory_id else []
                ))
            
            # Diálogo hostil
            elif event.event_type == EventType.DIALOGUE_THREAT:
                facts.append(SemanticFact(
                    entity_id=entity_id,
                    fact_type=FactType.ENTITY_RELATION,
                    subject=event.actor_name,
                    predicate="ameaçou",
                    object=event.target_name,
                    confidence=FactConfidence.CERTAIN,
                    source_memory_ids=[memory_id] if memory_id else []
                ))
        
        # Fatos sobre localização
        if event.event_type == EventType.COMBAT_ATTACK:
            facts.append(SemanticFact(
                entity_id=entity_id,
                fact_type=FactType.LOCATION_DANGER,
                subject=event.location,
                predicate="teve combate recentemente",
                confidence=FactConfidence.CERTAIN,
                source_memory_ids=[memory_id] if memory_id else []
            ))
        
        # Fatos sobre habilidades (se mencionado na descrição)
        description_lower = event.description.lower()
        if "fogo" in description_lower or "chama" in description_lower:
            facts.append(SemanticFact(
                entity_id=entity_id,
                fact_type=FactType.ENTITY_ABILITY,
                subject=event.actor_name,
                predicate="usa técnicas de fogo",
                confidence=FactConfidence.PROBABLE,
                source_memory_ids=[memory_id] if memory_id else []
            ))
        elif "gelo" in description_lower or "frio" in description_lower:
            facts.append(SemanticFact(
                entity_id=entity_id,
                fact_type=FactType.ENTITY_ABILITY,
                subject=event.actor_name,
                predicate="usa técnicas de gelo",
                confidence=FactConfidence.PROBABLE,
                source_memory_ids=[memory_id] if memory_id else []
            ))
        elif "sombra" in description_lower or "escuridão" in description_lower:
            facts.append(SemanticFact(
                entity_id=entity_id,
                fact_type=FactType.ENTITY_ABILITY,
                subject=event.actor_name,
                predicate="usa técnicas de sombra",
                confidence=FactConfidence.PROBABLE,
                source_memory_ids=[memory_id] if memory_id else []
            ))
        
        # Fato de traição
        if event.event_type == EventType.BETRAYAL:
            facts.append(SemanticFact(
                entity_id=entity_id,
                fact_type=FactType.ENTITY_TRAIT,
                subject=event.actor_name,
                predicate="é um traidor",
                confidence=FactConfidence.CERTAIN,
                source_memory_ids=[memory_id] if memory_id else []
            ))
        
        return facts
    
    async def recall(
        self,
        entity_id: int,
        query: str,
        context: Optional["SessionContext"] = None,
        include_episodic: bool = True,
        include_semantic: bool = True,
        include_procedural: bool = True,
        max_episodic: int = 5,
        max_semantic: int = 5,
        max_procedural: int = 3
    ) -> MemoryBundle:
        """
        Recupera memórias relevantes para uma query.
        
        Combina busca semântica (por embedding) com filtragem contextual.
        
        Args:
            entity_id: ID da entidade
            query: Texto da query (o que está sendo lembrado)
            context: SessionContext para contexto adicional
            include_episodic: Incluir memórias episódicas
            include_semantic: Incluir fatos semânticos
            include_procedural: Incluir padrões
            max_*: Limites por tipo
        
        Returns:
            MemoryBundle com memórias relevantes
        """
        bundle = MemoryBundle()
        
        # 1. Buscar memórias episódicas
        if include_episodic:
            episodic = await self.episodic_store.query_semantic(
                entity_id=entity_id,
                query_text=query,
                limit=max_episodic
            )
            bundle.episodic_memories = episodic
            
            if episodic:
                summaries = [m.get_summary() for m in episodic[:3]]
                bundle.episodic_summary = "\n".join(summaries)
                
                # Determinar emoção dominante
                emotions = [m.emotional_valence for m in episodic]
                emotion_counts = {}
                for e in emotions:
                    emotion_counts[e] = emotion_counts.get(e, 0) + 1
                if emotion_counts:
                    bundle.dominant_emotion = max(emotion_counts, key=emotion_counts.get)
        
        # 2. Buscar fatos semânticos
        if include_semantic:
            # Extrair subject potencial da query
            subject = self._extract_subject_from_query(query)
            
            semantic = await self.semantic_store.query(
                entity_id=entity_id,
                query_text=query,
                subject=subject,
                limit=max_semantic
            )
            bundle.semantic_facts = semantic
            
            if semantic:
                statements = [f.get_statement() for f in semantic[:3]]
                bundle.semantic_summary = "\n".join(statements)
                
                # Determinar postura baseada em fatos de relação
                for fact in semantic:
                    if fact.fact_type == FactType.ENTITY_RELATION:
                        if "hostil" in fact.predicate.lower() or "inimigo" in fact.predicate.lower():
                            bundle.relationship_stance = "hostile"
                            break
                        elif "amigo" in fact.predicate.lower() or "aliado" in fact.predicate.lower():
                            bundle.relationship_stance = "friendly"
                            break
                        elif "ajudou" in fact.predicate.lower():
                            bundle.relationship_stance = "friendly"
        
        # 3. Buscar padrões comportamentais
        if include_procedural:
            patterns = await self.procedural_store.get_patterns(
                entity_id=entity_id,
                min_strength=PatternType.COMBAT_OPENER  # Qualquer tipo
            )
            bundle.behavior_patterns = patterns[:max_procedural]
            
            if patterns:
                descriptions = [p.get_description() for p in patterns[:3]]
                bundle.behavioral_summary = "\n".join(descriptions)
            
            # Tentar prever comportamento
            prediction = await self.procedural_store.predict_behavior(entity_id, query)
            if prediction:
                bundle.predicted_behavior = prediction[0]
                bundle.prediction_confidence = prediction[1]
        
        logger.debug(
            f"Recall para entidade {entity_id}: "
            f"{len(bundle.episodic_memories)} episódicas, "
            f"{len(bundle.semantic_facts)} fatos, "
            f"{len(bundle.behavior_patterns)} padrões"
        )
        
        return bundle
    
    def _extract_subject_from_query(self, query: str) -> Optional[str]:
        """Tenta extrair um subject (nome) da query."""
        # Lista de palavras a ignorar
        ignore_words = {
            "o", "a", "os", "as", "um", "uma", "uns", "umas",
            "de", "da", "do", "das", "dos", "em", "na", "no", "nas", "nos",
            "para", "por", "com", "como", "que", "qual", "quais",
            "é", "foi", "era", "será", "seria",
            "eu", "você", "ele", "ela", "nós", "eles", "elas",
            "meu", "minha", "seu", "sua", "nosso", "nossa",
            "este", "esta", "esse", "essa", "aquele", "aquela",
            "jogador", "player", "personagem"
        }
        
        words = query.split()
        
        # Procurar palavras capitalizadas (nomes próprios)
        for word in words:
            word_clean = word.strip(".,!?:;")
            if word_clean and word_clean[0].isupper() and word_clean.lower() not in ignore_words:
                return word_clean
        
        return None
    
    async def consolidate(self, entity_id: int) -> None:
        """
        Consolida memórias antigas.
        
        - Memórias de baixa importância são compactadas
        - Fatos semânticos são fortalecidos ou esquecidos
        - Padrões fracos são removidos
        """
        logger.info(f"Iniciando consolidação para entidade {entity_id}")
        
        # Buscar todas as memórias
        all_memories = await self.episodic_store.query(entity_id, limit=100)
        
        if len(all_memories) < self.consolidation_threshold:
            return
        
        # Detectar novos padrões
        await self.procedural_store.detect_patterns(entity_id, all_memories[-20:])
        
        # Remover memórias muito antigas e de baixa importância
        old_low_importance = [
            m for m in all_memories 
            if m.importance_score < 0.3 and 
            (datetime.utcnow() - m.timestamp).days > 7
        ]
        
        # Por enquanto, apenas log - não deletar ainda
        if old_low_importance:
            logger.info(
                f"Consolidação: {len(old_low_importance)} memórias poderiam ser compactadas"
            )
        
        logger.info(f"Consolidação concluída para entidade {entity_id}")
    
    async def get_relationship_summary(
        self,
        entity_id: int,
        target_name: str
    ) -> Dict[str, Any]:
        """
        Retorna resumo do relacionamento entre entidade e alvo.
        
        Args:
            entity_id: ID da entidade
            target_name: Nome do alvo do relacionamento
        
        Returns:
            Dict com informações do relacionamento
        """
        # Buscar memórias envolvendo o alvo
        episodic = await self.episodic_store.get_by_participant(entity_id, target_name, limit=10)
        
        # Buscar fatos sobre o alvo
        semantic = await self.semantic_store.get_facts_about(entity_id, target_name)
        
        # Buscar padrões relacionados
        patterns = await self.procedural_store.get_patterns(entity_id)
        relevant_patterns = [
            p for p in patterns 
            if target_name.lower() in p.trigger.lower() or target_name.lower() in p.behavior.lower()
        ]
        
        # Analisar emoções
        emotions = [m.emotional_valence for m in episodic]
        positive_count = sum(1 for e in emotions if e.value.startswith("positive") or e.value == "very_positive")
        negative_count = sum(1 for e in emotions if e.value.startswith("negative") or e.value == "very_negative")
        
        # Determinar stance
        if negative_count > positive_count * 2:
            stance = "hostile"
        elif positive_count > negative_count * 2:
            stance = "friendly"
        elif negative_count > positive_count:
            stance = "wary"
        elif positive_count > negative_count:
            stance = "warm"
        else:
            stance = "neutral"
        
        return {
            "target": target_name,
            "stance": stance,
            "total_interactions": len(episodic),
            "positive_interactions": positive_count,
            "negative_interactions": negative_count,
            "known_facts": [f.get_statement() for f in semantic[:5]],
            "patterns": [p.get_description() for p in relevant_patterns[:3]],
            "last_interaction": episodic[0].timestamp.isoformat() if episodic else None,
        }
    
    async def forget_about(self, entity_id: int, target_name: str) -> int:
        """
        Remove todas as memórias sobre um alvo específico.
        Usado para "resetar" relacionamentos ou limpar dados.
        
        Returns:
            Número de memórias removidas
        """
        # Buscar memórias envolvendo o alvo
        memories = await self.episodic_store.get_by_participant(entity_id, target_name, limit=100)
        
        # Por segurança, não deletamos - apenas log
        logger.warning(
            f"forget_about chamado para {target_name}: "
            f"{len(memories)} memórias seriam removidas"
        )
        
        return len(memories)
    
    def clear_caches(self, entity_id: Optional[int] = None) -> None:
        """Limpa caches de todos os stores."""
        self.semantic_store.clear_cache(entity_id)
        self.procedural_store.clear_cache(entity_id)


# Factory function para criar HierarchicalMemory
async def create_memory_system(session: "AsyncSession") -> HierarchicalMemory:
    """Factory function para criar instância de HierarchicalMemory."""
    return HierarchicalMemory(session)
