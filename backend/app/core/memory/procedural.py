"""
Procedural Memory Store - Padrões de Comportamento
GEM RPG ORBIS - Arquitetura Cognitiva

Procedural memories são padrões de comportamento detectados
a partir de múltiplas experiências. Representam "como fazer" 
e expectativas sobre comportamentos.

Exemplos:
- "Yi Fan sempre ataca primeiro"
- "Yi Fan foge quando HP < 30%"
- "O jogador costuma poupar inimigos derrotados"
- "Guardas patrulham o mercado de manhã"
"""

from __future__ import annotations
import logging
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple, TYPE_CHECKING
from enum import Enum
from collections import Counter

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession
    from app.core.memory.episodic import EpisodicMemory

logger = logging.getLogger(__name__)

__all__ = [
    "BehaviorPattern",
    "ProceduralStore",
    "PatternType",
    "PatternStrength",
]


class PatternType(str, Enum):
    """Tipos de padrões comportamentais."""
    # Combate
    COMBAT_OPENER = "combat_opener"           # Como inicia combate
    COMBAT_FINISHER = "combat_finisher"       # Como finaliza combate
    COMBAT_ESCAPE = "combat_escape"           # Quando/como foge
    COMBAT_STYLE = "combat_style"             # Estilo geral de luta
    
    # Social
    DIALOGUE_STYLE = "dialogue_style"         # Como conversa
    NEGOTIATION = "negotiation"               # Como negocia
    REACTION_TO_THREAT = "reaction_threat"    # Como reage a ameaças
    REACTION_TO_KINDNESS = "reaction_kind"    # Como reage a gentileza
    
    # Rotina
    DAILY_ROUTINE = "daily_routine"           # Rotina diária
    LOCATION_PREFERENCE = "location_pref"     # Preferência de local
    TIME_PREFERENCE = "time_pref"             # Preferência de horário
    
    # Decisão
    DECISION_MAKING = "decision_making"       # Como toma decisões
    RISK_TOLERANCE = "risk_tolerance"         # Tolerância a risco
    LOYALTY = "loyalty"                       # Padrão de lealdade


class PatternStrength(str, Enum):
    """Força de um padrão detectado."""
    WEAK = "weak"           # 2-3 ocorrências
    MODERATE = "moderate"   # 4-6 ocorrências
    STRONG = "strong"       # 7-10 ocorrências
    DEFINITIVE = "definitive"  # 10+ ocorrências


@dataclass
class BehaviorPattern:
    """
    Um padrão de comportamento detectado.
    
    Attributes:
        entity_id: ID da entidade com este padrão
        pattern_type: Tipo do padrão
        trigger: O que dispara este comportamento
        behavior: O comportamento observado
        frequency: Frequência observada (0.0-1.0)
        occurrences: Número de vezes observado
        exceptions: Número de exceções ao padrão
        last_observed: Última vez que foi observado
        source_memory_ids: Memórias que geraram este padrão
        strength: Força do padrão
        metadata: Dados adicionais
    """
    entity_id: int
    pattern_type: PatternType
    trigger: str              # Ex: "início de combate"
    behavior: str             # Ex: "usa ataque mais forte"
    frequency: float = 0.5    # Proporção de vezes que segue o padrão
    occurrences: int = 1
    exceptions: int = 0
    first_observed: datetime = field(default_factory=datetime.utcnow)
    last_observed: datetime = field(default_factory=datetime.utcnow)
    source_memory_ids: List[int] = field(default_factory=list)
    strength: PatternStrength = PatternStrength.WEAK
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # ID gerado
    id: Optional[str] = None
    
    def __post_init__(self):
        """Gera ID único."""
        if self.id is None:
            import hashlib
            content = f"{self.entity_id}:{self.pattern_type.value}:{self.trigger}"
            self.id = hashlib.md5(content.encode()).hexdigest()[:12]
        self._update_strength()
    
    def _update_strength(self) -> None:
        """Atualiza força baseada em ocorrências."""
        if self.occurrences >= 10:
            self.strength = PatternStrength.DEFINITIVE
        elif self.occurrences >= 7:
            self.strength = PatternStrength.STRONG
        elif self.occurrences >= 4:
            self.strength = PatternStrength.MODERATE
        else:
            self.strength = PatternStrength.WEAK
    
    def observe(self, followed: bool = True, memory_id: Optional[int] = None) -> None:
        """Registra uma observação do padrão."""
        if followed:
            self.occurrences += 1
        else:
            self.exceptions += 1
        
        total = self.occurrences + self.exceptions
        self.frequency = self.occurrences / total if total > 0 else 0.5
        
        self.last_observed = datetime.utcnow()
        
        if memory_id and memory_id not in self.source_memory_ids:
            self.source_memory_ids.append(memory_id)
        
        self._update_strength()
    
    def get_description(self) -> str:
        """Retorna descrição do padrão."""
        reliability = "sempre" if self.frequency > 0.9 else (
            "geralmente" if self.frequency > 0.7 else (
                "frequentemente" if self.frequency > 0.5 else "às vezes"
            )
        )
        return f"Quando {self.trigger}, {reliability} {self.behavior}"
    
    def get_prediction_confidence(self) -> float:
        """Retorna confiança de previsão baseada em força e frequência."""
        strength_multiplier = {
            PatternStrength.WEAK: 0.5,
            PatternStrength.MODERATE: 0.7,
            PatternStrength.STRONG: 0.85,
            PatternStrength.DEFINITIVE: 0.95,
        }
        return self.frequency * strength_multiplier.get(self.strength, 0.5)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "pattern_type": self.pattern_type.value,
            "trigger": self.trigger,
            "behavior": self.behavior,
            "frequency": self.frequency,
            "occurrences": self.occurrences,
            "exceptions": self.exceptions,
            "first_observed": self.first_observed.isoformat(),
            "last_observed": self.last_observed.isoformat(),
            "source_memory_ids": self.source_memory_ids,
            "strength": self.strength.value,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BehaviorPattern":
        """Deserializa de dicionário."""
        pattern = cls(
            entity_id=data["entity_id"],
            pattern_type=PatternType(data["pattern_type"]),
            trigger=data["trigger"],
            behavior=data["behavior"],
            frequency=data.get("frequency", 0.5),
            occurrences=data.get("occurrences", 1),
            exceptions=data.get("exceptions", 0),
            first_observed=datetime.fromisoformat(data["first_observed"]),
            last_observed=datetime.fromisoformat(data["last_observed"]),
            source_memory_ids=data.get("source_memory_ids", []),
            strength=PatternStrength(data.get("strength", "weak")),
            metadata=data.get("metadata", {}),
        )
        pattern.id = data.get("id")
        return pattern


class ProceduralStore:
    """
    Store para padrões de comportamento.
    Detecta e armazena padrões a partir de memórias episódicas.
    """
    
    def __init__(self, session: "AsyncSession"):
        self.session = session
        # Cache de padrões por entidade
        self._pattern_cache: Dict[int, Dict[str, BehaviorPattern]] = {}
        
        # Configurações de detecção
        self.min_occurrences_for_pattern = 2
        self.pattern_decay_days = 30  # Padrões não observados decaem
    
    async def add(self, pattern: BehaviorPattern) -> BehaviorPattern:
        """Adiciona ou atualiza um padrão."""
        # Verificar se já existe
        existing = await self._find_existing(pattern)
        
        if existing:
            # Atualizar existente
            existing.observe(followed=True)
            await self._persist_pattern(existing)
            
            # Atualizar cache
            if pattern.entity_id not in self._pattern_cache:
                self._pattern_cache[pattern.entity_id] = {}
            self._pattern_cache[pattern.entity_id][existing.id] = existing
            
            return existing
        
        # Novo padrão
        await self._persist_pattern(pattern)
        
        # Adicionar ao cache
        if pattern.entity_id not in self._pattern_cache:
            self._pattern_cache[pattern.entity_id] = {}
        self._pattern_cache[pattern.entity_id][pattern.id] = pattern
        
        logger.info(f"Padrão adicionado: {pattern.get_description()}")
        return pattern
    
    async def _find_existing(self, pattern: BehaviorPattern) -> Optional[BehaviorPattern]:
        """Busca padrão existente."""
        # Primeiro no cache
        entity_patterns = self._pattern_cache.get(pattern.entity_id, {})
        if pattern.id in entity_patterns:
            return entity_patterns[pattern.id]
        
        # Depois no banco
        from sqlalchemy import text
        
        sql = text("""
            SELECT id, content FROM memory
            WHERE npc_id = :entity_id
            AND content LIKE :pattern
            LIMIT 1
        """)
        
        result = await self.session.execute(sql, {
            "entity_id": pattern.entity_id,
            "pattern": f'%"type": "procedural"%"id": "{pattern.id}"%'
        })
        
        row = result.fetchone()
        if row:
            return self._parse_pattern_content(row[0], row[1], pattern.entity_id)
        
        return None
    
    async def _persist_pattern(self, pattern: BehaviorPattern) -> None:
        """Persiste padrão no banco."""
        from sqlalchemy import text
        from pgvector.sqlalchemy import Vector
        from sqlalchemy import bindparam
        
        content = json.dumps({
            "type": "procedural",
            **pattern.to_dict()
        }, ensure_ascii=False)
        
        # Gerar embedding simples para o padrão
        from app.services.embedding_service import EmbeddingService
        embedder = EmbeddingService()
        embedding = embedder.generate_embedding(pattern.get_description())
        if len(embedding) > 128:
            embedding = embedding[:128]
        elif len(embedding) < 128:
            embedding = embedding + [0.0] * (128 - len(embedding))
        
        # Verificar se já existe
        check_sql = text("""
            SELECT id FROM memory 
            WHERE npc_id = :entity_id 
            AND content LIKE :pattern
            LIMIT 1
        """)
        
        result = await self.session.execute(check_sql, {
            "entity_id": pattern.entity_id,
            "pattern": f'%"id": "{pattern.id}"%'
        })
        
        existing_row = result.fetchone()
        
        if existing_row:
            # Atualizar
            update_sql = text("""
                UPDATE memory 
                SET content = :content
                WHERE id = :memory_id
            """)
            
            await self.session.execute(update_sql, {
                "content": content,
                "memory_id": existing_row[0]
            })
        else:
            # Inserir
            insert_sql = text("""
                INSERT INTO memory (npc_id, content, embedding)
                VALUES (:entity_id, :content, :embedding)
            """).bindparams(
                bindparam("embedding", type_=Vector(128))
            )
            
            await self.session.execute(insert_sql, {
                "entity_id": pattern.entity_id,
                "content": content,
                "embedding": embedding,
            })
        
        await self.session.commit()
    
    async def get_patterns(
        self,
        entity_id: int,
        pattern_types: Optional[List[PatternType]] = None,
        min_strength: PatternStrength = PatternStrength.WEAK
    ) -> List[BehaviorPattern]:
        """
        Retorna padrões de uma entidade.
        
        Args:
            entity_id: ID da entidade
            pattern_types: Tipos de padrão para filtrar (opcional)
            min_strength: Força mínima do padrão
        
        Returns:
            Lista de padrões ordenados por força
        """
        from sqlalchemy import text
        
        sql = text("""
            SELECT id, content FROM memory
            WHERE npc_id = :entity_id
            AND content LIKE '%"type": "procedural"%'
            ORDER BY id DESC
            LIMIT 50
        """)
        
        result = await self.session.execute(sql, {"entity_id": entity_id})
        rows = result.fetchall()
        
        patterns = []
        strength_order = [
            PatternStrength.DEFINITIVE,
            PatternStrength.STRONG,
            PatternStrength.MODERATE,
            PatternStrength.WEAK,
        ]
        min_strength_index = strength_order.index(min_strength)
        
        for row in rows:
            pattern = self._parse_pattern_content(row[0], row[1], entity_id)
            if not pattern:
                continue
            
            # Filtrar por tipo
            if pattern_types and pattern.pattern_type not in pattern_types:
                continue
            
            # Filtrar por força
            pattern_strength_index = strength_order.index(pattern.strength)
            if pattern_strength_index > min_strength_index:
                continue
            
            patterns.append(pattern)
        
        # Ordenar por força (mais forte primeiro)
        patterns.sort(key=lambda p: (
            strength_order.index(p.strength),
            -p.frequency
        ))
        
        return patterns
    
    async def detect_patterns(
        self,
        entity_id: int,
        recent_events: List["EpisodicMemory"]
    ) -> List[BehaviorPattern]:
        """
        Detecta padrões em eventos recentes.
        Analisa sequências de eventos e comportamentos recorrentes.
        
        Args:
            entity_id: ID da entidade
            recent_events: Lista de memórias episódicas recentes
        
        Returns:
            Lista de padrões detectados ou fortalecidos
        """
        if len(recent_events) < self.min_occurrences_for_pattern:
            return []
        
        detected_patterns = []
        
        # Analisar padrões de combate
        combat_events = [e for e in recent_events if e.event_type == "combat"]
        if len(combat_events) >= 2:
            combat_patterns = self._analyze_combat_patterns(entity_id, combat_events)
            detected_patterns.extend(combat_patterns)
        
        # Analisar padrões de localização
        location_counts = Counter(e.location for e in recent_events)
        for location, count in location_counts.most_common(3):
            if count >= 2:
                pattern = BehaviorPattern(
                    entity_id=entity_id,
                    pattern_type=PatternType.LOCATION_PREFERENCE,
                    trigger="escolha de localização",
                    behavior=f"frequenta {location}",
                    occurrences=count,
                    source_memory_ids=[e.id for e in recent_events if e.location == location and e.id]
                )
                detected_patterns.append(pattern)
        
        # Analisar padrões de reação
        reaction_patterns = self._analyze_reaction_patterns(entity_id, recent_events)
        detected_patterns.extend(reaction_patterns)
        
        # Persistir padrões detectados
        final_patterns = []
        for pattern in detected_patterns:
            saved = await self.add(pattern)
            final_patterns.append(saved)
        
        return final_patterns
    
    def _analyze_combat_patterns(
        self,
        entity_id: int,
        combat_events: List["EpisodicMemory"]
    ) -> List[BehaviorPattern]:
        """Analisa padrões em eventos de combate."""
        patterns = []
        
        # Detectar padrão de abertura de combate
        openers = []
        for event in combat_events:
            description_lower = event.raw_description.lower()
            if "primeiro" in description_lower or "iniciou" in description_lower:
                if "ataque" in description_lower:
                    openers.append("ataque agressivo")
                elif "defesa" in description_lower or "recuo" in description_lower:
                    openers.append("posição defensiva")
                else:
                    openers.append("abordagem cautelosa")
        
        if openers:
            most_common_opener = Counter(openers).most_common(1)[0]
            if most_common_opener[1] >= 2:
                patterns.append(BehaviorPattern(
                    entity_id=entity_id,
                    pattern_type=PatternType.COMBAT_OPENER,
                    trigger="início de combate",
                    behavior=f"usa {most_common_opener[0]}",
                    occurrences=most_common_opener[1]
                ))
        
        # Detectar padrão de fuga
        escapes = []
        for event in combat_events:
            description_lower = event.raw_description.lower()
            if "fugiu" in description_lower or "recuou" in description_lower or "escapou" in description_lower:
                if "ferido" in description_lower or "hp baixo" in description_lower:
                    escapes.append("quando ferido gravemente")
                elif "cercado" in description_lower:
                    escapes.append("quando cercado")
                else:
                    escapes.append("quando em desvantagem")
        
        if escapes:
            most_common_escape = Counter(escapes).most_common(1)[0]
            if most_common_escape[1] >= 2:
                patterns.append(BehaviorPattern(
                    entity_id=entity_id,
                    pattern_type=PatternType.COMBAT_ESCAPE,
                    trigger=most_common_escape[0],
                    behavior="foge do combate",
                    occurrences=most_common_escape[1]
                ))
        
        return patterns
    
    def _analyze_reaction_patterns(
        self,
        entity_id: int,
        events: List["EpisodicMemory"]
    ) -> List[BehaviorPattern]:
        """Analisa padrões de reação."""
        patterns = []
        
        # Agrupar por valência emocional e tipo de reação
        reactions_to_negative = []
        reactions_to_positive = []
        
        for event in events:
            description_lower = event.raw_description.lower()
            
            if event.emotional_valence.value.startswith("negative"):
                if "atacou" in description_lower or "revidou" in description_lower:
                    reactions_to_negative.append("retalia")
                elif "fugiu" in description_lower or "recuou" in description_lower:
                    reactions_to_negative.append("evita confronto")
                elif "guardou rancor" in description_lower or "lembrar" in description_lower:
                    reactions_to_negative.append("guarda rancor")
            
            if event.emotional_valence.value.startswith("positive"):
                if "agradeceu" in description_lower or "gratidão" in description_lower:
                    reactions_to_positive.append("demonstra gratidão")
                elif "ajudou" in description_lower or "retribuiu" in description_lower:
                    reactions_to_positive.append("retribui o favor")
        
        # Criar padrões para reações comuns
        if reactions_to_negative:
            most_common = Counter(reactions_to_negative).most_common(1)[0]
            if most_common[1] >= 2:
                patterns.append(BehaviorPattern(
                    entity_id=entity_id,
                    pattern_type=PatternType.REACTION_TO_THREAT,
                    trigger="ameaça ou agressão",
                    behavior=most_common[0],
                    occurrences=most_common[1]
                ))
        
        if reactions_to_positive:
            most_common = Counter(reactions_to_positive).most_common(1)[0]
            if most_common[1] >= 2:
                patterns.append(BehaviorPattern(
                    entity_id=entity_id,
                    pattern_type=PatternType.REACTION_TO_KINDNESS,
                    trigger="ajuda ou gentileza",
                    behavior=most_common[0],
                    occurrences=most_common[1]
                ))
        
        return patterns
    
    async def predict_behavior(
        self,
        entity_id: int,
        trigger: str
    ) -> Optional[Tuple[str, float]]:
        """
        Prevê comportamento baseado em padrões.
        
        Args:
            entity_id: ID da entidade
            trigger: Situação/gatilho
        
        Returns:
            Tuple (comportamento previsto, confiança) ou None
        """
        patterns = await self.get_patterns(entity_id, min_strength=PatternStrength.MODERATE)
        
        # Encontrar padrão com trigger mais similar
        trigger_lower = trigger.lower()
        best_match = None
        best_score = 0.0
        
        for pattern in patterns:
            pattern_trigger_lower = pattern.trigger.lower()
            
            # Calcular similaridade simples (palavras em comum)
            trigger_words = set(trigger_lower.split())
            pattern_words = set(pattern_trigger_lower.split())
            
            if not pattern_words:
                continue
            
            common = len(trigger_words & pattern_words)
            score = common / len(pattern_words)
            
            if score > best_score:
                best_score = score
                best_match = pattern
        
        if best_match and best_score > 0.3:
            confidence = best_match.get_prediction_confidence() * best_score
            return (best_match.behavior, confidence)
        
        return None
    
    def _parse_pattern_content(
        self,
        memory_id: int,
        content: str,
        entity_id: int
    ) -> Optional[BehaviorPattern]:
        """Parseia conteúdo de padrão do banco."""
        try:
            data = json.loads(content)
            
            if data.get("type") != "procedural":
                return None
            
            return BehaviorPattern.from_dict(data)
            
        except Exception as e:
            logger.warning(f"Erro ao parsear padrão {memory_id}: {e}")
            return None
    
    def clear_cache(self, entity_id: Optional[int] = None) -> None:
        """Limpa cache de padrões."""
        if entity_id:
            if entity_id in self._pattern_cache:
                del self._pattern_cache[entity_id]
        else:
            self._pattern_cache.clear()
