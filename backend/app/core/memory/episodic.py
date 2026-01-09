"""
Episodic Memory Store - Memórias de Eventos Específicos
GEM RPG ORBIS - Arquitetura Cognitiva

Episodic memories são eventos específicos que aconteceram em um 
momento e lugar específicos. Incluem contexto temporal, emocional
e participantes.

Exemplos:
- "Yi Fan me atacou na Floresta Nublada usando golpe de fogo"
- "O jogador me ajudou a derrotar o bandido"
- "Fui humilhado publicamente no mercado"
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

logger = logging.getLogger(__name__)

__all__ = [
    "EpisodicMemory",
    "EpisodicStore",
    "TimeRange",
    "EmotionalValence",
]


class EmotionalValence(str, Enum):
    """Valência emocional de uma memória."""
    VERY_NEGATIVE = "very_negative"  # Trauma, humilhação, dor intensa
    NEGATIVE = "negative"            # Derrota, ofensa, perda
    NEUTRAL = "neutral"              # Evento comum
    POSITIVE = "positive"            # Vitória, ajuda recebida
    VERY_POSITIVE = "very_positive"  # Momento épico, salvação


@dataclass
class TimeRange:
    """Range temporal para queries de memória."""
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    
    @classmethod
    def last_n_hours(cls, hours: int) -> "TimeRange":
        """Cria range para as últimas N horas."""
        now = datetime.utcnow()
        from datetime import timedelta
        return cls(start=now - timedelta(hours=hours), end=now)
    
    @classmethod
    def last_n_days(cls, days: int) -> "TimeRange":
        """Cria range para os últimos N dias."""
        now = datetime.utcnow()
        from datetime import timedelta
        return cls(start=now - timedelta(days=days), end=now)
    
    @classmethod
    def all_time(cls) -> "TimeRange":
        """Cria range sem limites."""
        return cls(start=None, end=None)


@dataclass
class EpisodicMemory:
    """
    Uma memória episódica - um evento específico que ocorreu.
    
    Attributes:
        entity_id: ID da entidade dona da memória (NPC ou Player)
        timestamp: Quando o evento ocorreu (tempo real)
        game_timestamp: Quando o evento ocorreu (tempo in-game)
        location: Onde o evento ocorreu
        participants: Lista de nomes dos participantes
        event_type: Tipo do evento (combat, dialogue, observation, etc)
        raw_description: Descrição bruta do que aconteceu
        emotional_valence: Impacto emocional do evento
        importance_score: Quão importante é esta memória (0.0-1.0)
        embedding: Vetor de embedding para busca semântica
        metadata: Dados adicionais específicos do evento
    """
    entity_id: int
    timestamp: datetime
    game_timestamp: str  # Formato: "DD-MM-YYYY HH:MM"
    location: str
    participants: List[str]
    event_type: str
    raw_description: str
    emotional_valence: EmotionalValence = EmotionalValence.NEUTRAL
    importance_score: float = 0.5
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # ID do banco (preenchido após persistência)
    id: Optional[int] = None
    
    def get_summary(self) -> str:
        """Retorna resumo compacto da memória."""
        participants_str = ", ".join(self.participants[:3])
        if len(self.participants) > 3:
            participants_str += f" e mais {len(self.participants) - 3}"
        
        return f"[{self.event_type.upper()}] {self.raw_description[:100]}... ({participants_str})"
    
    def get_emotional_modifier(self) -> float:
        """Retorna modificador de emoção para cálculos de relevância."""
        modifiers = {
            EmotionalValence.VERY_NEGATIVE: -1.0,
            EmotionalValence.NEGATIVE: -0.5,
            EmotionalValence.NEUTRAL: 0.0,
            EmotionalValence.POSITIVE: 0.5,
            EmotionalValence.VERY_POSITIVE: 1.0,
        }
        return modifiers.get(self.emotional_valence, 0.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "timestamp": self.timestamp.isoformat(),
            "game_timestamp": self.game_timestamp,
            "location": self.location,
            "participants": self.participants,
            "event_type": self.event_type,
            "raw_description": self.raw_description,
            "emotional_valence": self.emotional_valence.value,
            "importance_score": self.importance_score,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EpisodicMemory":
        """Deserializa de dicionário."""
        return cls(
            id=data.get("id"),
            entity_id=data["entity_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            game_timestamp=data["game_timestamp"],
            location=data["location"],
            participants=data["participants"],
            event_type=data["event_type"],
            raw_description=data["raw_description"],
            emotional_valence=EmotionalValence(data.get("emotional_valence", "neutral")),
            importance_score=data.get("importance_score", 0.5),
            metadata=data.get("metadata", {}),
        )


class EpisodicStore:
    """
    Store para memórias episódicas.
    Gerencia persistência e busca de eventos específicos.
    """
    
    def __init__(self, session: "AsyncSession"):
        self.session = session
        self._embedding_service = None
    
    @property
    def embedding_service(self):
        """Lazy load do embedding service."""
        if self._embedding_service is None:
            from app.services.embedding_service import EmbeddingService
            self._embedding_service = EmbeddingService()
        return self._embedding_service
    
    async def add(self, memory: EpisodicMemory) -> EpisodicMemory:
        """
        Adiciona uma memória episódica ao store.
        Gera embedding automaticamente se não fornecido.
        """
        # Gerar embedding se não existir
        if memory.embedding is None:
            memory.embedding = self._generate_embedding(memory)
        
        # Preparar conteúdo para persistência
        content = self._format_memory_content(memory)
        
        # Usar a tabela existente de Memory para compatibilidade
        from sqlalchemy import text
        from pgvector.sqlalchemy import Vector
        from sqlalchemy import bindparam
        
        # Inserir na tabela memory com campos extras em JSON
        sql = text("""
            INSERT INTO memory (npc_id, content, embedding)
            VALUES (:entity_id, :content, :embedding)
            RETURNING id
        """).bindparams(
            bindparam("embedding", type_=Vector(128))
        )
        
        result = await self.session.execute(sql, {
            "entity_id": memory.entity_id,
            "content": content,
            "embedding": memory.embedding,
        })
        
        await self.session.commit()
        
        row = result.fetchone()
        if row:
            memory.id = row[0]
        
        logger.info(f"Memória episódica adicionada para entidade {memory.entity_id}: {memory.event_type}")
        return memory
    
    def _generate_embedding(self, memory: EpisodicMemory) -> List[float]:
        """Gera embedding para uma memória."""
        # Combinar informações relevantes para embedding rico
        text_parts = [
            memory.raw_description,
            f"Local: {memory.location}",
            f"Tipo: {memory.event_type}",
            f"Participantes: {', '.join(memory.participants)}",
        ]
        text_for_embedding = " | ".join(text_parts)
        
        vec = self.embedding_service.generate_embedding(text_for_embedding)
        
        # Ajustar para 128D (compatível com schema atual)
        if len(vec) > 128:
            vec = vec[:128]
        elif len(vec) < 128:
            vec = vec + [0.0] * (128 - len(vec))
        
        return vec
    
    def _format_memory_content(self, memory: EpisodicMemory) -> str:
        """Formata memória para armazenamento como texto estruturado."""
        import json
        
        content_obj = {
            "type": "episodic",
            "event_type": memory.event_type,
            "description": memory.raw_description,
            "location": memory.location,
            "participants": memory.participants,
            "game_time": memory.game_timestamp,
            "emotional_valence": memory.emotional_valence.value,
            "importance": memory.importance_score,
            "metadata": memory.metadata,
        }
        
        return json.dumps(content_obj, ensure_ascii=False)
    
    async def query(
        self,
        entity_id: int,
        time_range: Optional[TimeRange] = None,
        event_types: Optional[List[str]] = None,
        min_importance: float = 0.0,
        limit: int = 10
    ) -> List[EpisodicMemory]:
        """
        Busca memórias episódicas com filtros.
        
        Args:
            entity_id: ID da entidade
            time_range: Range temporal (opcional)
            event_types: Tipos de evento para filtrar (opcional)
            min_importance: Importância mínima (0.0-1.0)
            limit: Máximo de resultados
        
        Returns:
            Lista de memórias episódicas ordenadas por recência
        """
        from sqlalchemy import text
        
        # Query base
        sql = """
            SELECT id, content 
            FROM memory 
            WHERE npc_id = :entity_id
            ORDER BY id DESC
            LIMIT :limit
        """
        
        result = await self.session.execute(
            text(sql),
            {"entity_id": entity_id, "limit": limit * 2}  # Pegar mais para filtrar
        )
        
        rows = result.fetchall()
        memories = []
        
        for row in rows:
            memory = self._parse_memory_content(row[0], row[1], entity_id)
            if memory:
                # Filtrar por event_types se especificado
                if event_types and memory.event_type not in event_types:
                    continue
                
                # Filtrar por importância
                if memory.importance_score < min_importance:
                    continue
                
                memories.append(memory)
                
                if len(memories) >= limit:
                    break
        
        return memories
    
    async def query_semantic(
        self,
        entity_id: int,
        query_text: str,
        limit: int = 5,
        min_similarity: float = 0.0
    ) -> List[EpisodicMemory]:
        """
        Busca semântica de memórias usando embeddings.
        
        Args:
            entity_id: ID da entidade
            query_text: Texto da query
            limit: Máximo de resultados
            min_similarity: Similaridade mínima (0.0-1.0)
        
        Returns:
            Lista de memórias ordenadas por similaridade
        """
        from sqlalchemy import text
        from pgvector.sqlalchemy import Vector
        from sqlalchemy import bindparam
        
        # Gerar embedding da query
        query_vec = self.embedding_service.generate_embedding(query_text)
        if len(query_vec) > 128:
            query_vec = query_vec[:128]
        elif len(query_vec) < 128:
            query_vec = query_vec + [0.0] * (128 - len(query_vec))
        
        # Busca vetorial com distância coseno
        sql = text("""
            SELECT id, content, 1 - (embedding <=> :qvec) as similarity
            FROM memory
            WHERE npc_id = :entity_id
            ORDER BY embedding <=> :qvec
            LIMIT :limit
        """).bindparams(
            bindparam("qvec", type_=Vector(128))
        )
        
        result = await self.session.execute(sql, {
            "entity_id": entity_id,
            "qvec": query_vec,
            "limit": limit
        })
        
        rows = result.fetchall()
        memories = []
        
        for row in rows:
            similarity = row[2] if len(row) > 2 else 0.5
            if similarity < min_similarity:
                continue
            
            memory = self._parse_memory_content(row[0], row[1], entity_id)
            if memory:
                memories.append(memory)
        
        return memories
    
    async def get_recent(self, entity_id: int, n: int = 5) -> List[EpisodicMemory]:
        """Retorna as N memórias mais recentes."""
        return await self.query(entity_id, limit=n)
    
    async def get_by_location(self, entity_id: int, location: str, limit: int = 10) -> List[EpisodicMemory]:
        """Retorna memórias que ocorreram em uma localização específica."""
        all_memories = await self.query(entity_id, limit=limit * 3)
        return [m for m in all_memories if m.location == location][:limit]
    
    async def get_by_participant(self, entity_id: int, participant_name: str, limit: int = 10) -> List[EpisodicMemory]:
        """Retorna memórias envolvendo um participante específico."""
        all_memories = await self.query(entity_id, limit=limit * 3)
        return [
            m for m in all_memories 
            if any(participant_name.lower() in p.lower() for p in m.participants)
        ][:limit]
    
    async def get_traumatic(self, entity_id: int, limit: int = 5) -> List[EpisodicMemory]:
        """Retorna memórias traumáticas (very_negative)."""
        all_memories = await self.query(entity_id, limit=limit * 5)
        return [
            m for m in all_memories 
            if m.emotional_valence == EmotionalValence.VERY_NEGATIVE
        ][:limit]
    
    async def count(self, entity_id: int) -> int:
        """Conta total de memórias de uma entidade."""
        from sqlalchemy import text
        
        result = await self.session.execute(
            text("SELECT COUNT(*) FROM memory WHERE npc_id = :entity_id"),
            {"entity_id": entity_id}
        )
        
        return result.scalar() or 0
    
    def _parse_memory_content(
        self, 
        memory_id: int, 
        content: str, 
        entity_id: int
    ) -> Optional[EpisodicMemory]:
        """
        Parseia conteúdo de memória do banco.
        Suporta formato antigo (string simples) e novo (JSON estruturado).
        """
        import json
        
        try:
            # Tentar parsear como JSON (formato novo)
            if content.startswith("{"):
                data = json.loads(content)
                
                return EpisodicMemory(
                    id=memory_id,
                    entity_id=entity_id,
                    timestamp=datetime.utcnow(),  # Aproximação
                    game_timestamp=data.get("game_time", "01-01-1000 12:00"),
                    location=data.get("location", "Desconhecido"),
                    participants=data.get("participants", []),
                    event_type=data.get("event_type", "unknown"),
                    raw_description=data.get("description", content),
                    emotional_valence=EmotionalValence(data.get("emotional_valence", "neutral")),
                    importance_score=data.get("importance", 0.5),
                    metadata=data.get("metadata", {}),
                )
            else:
                # Formato antigo: string simples
                # Tentar extrair informações do texto
                event_type = "unknown"
                if "[ATTACKED_BY_PLAYER]" in content:
                    event_type = "combat"
                elif "[DIALOGUE]" in content:
                    event_type = "dialogue"
                elif "[OBSERVATION]" in content:
                    event_type = "observation"
                
                # Extrair participantes do texto
                participants = []
                words = content.split()
                for i, word in enumerate(words):
                    if word.lower() in ["me", "atacou", "disse", "ajudou"]:
                        if i > 0:
                            participants.append(words[i-1])
                
                return EpisodicMemory(
                    id=memory_id,
                    entity_id=entity_id,
                    timestamp=datetime.utcnow(),
                    game_timestamp="01-01-1000 12:00",
                    location="Desconhecido",
                    participants=participants,
                    event_type=event_type,
                    raw_description=content,
                    emotional_valence=EmotionalValence.NEGATIVE if "ATTACKED" in content else EmotionalValence.NEUTRAL,
                    importance_score=0.5,
                )
                
        except Exception as e:
            logger.warning(f"Erro ao parsear memória {memory_id}: {e}")
            return None
