"""
Semantic Memory Store - Fatos e Conhecimento Geral
GEM RPG ORBIS - Arquitetura Cognitiva

Semantic memories são fatos extraídos de experiências.
Não têm contexto temporal específico, mas representam
conhecimento duradouro sobre o mundo.

Exemplos:
- "Yi Fan é hostil"
- "Yi Fan usa técnicas de fogo"
- "O mercador Wang é confiável"
- "A Floresta Nublada é perigosa à noite"
"""

from __future__ import annotations
import logging
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

logger = logging.getLogger(__name__)

__all__ = [
    "SemanticFact",
    "SemanticStore",
    "FactType",
    "FactConfidence",
]


class FactType(str, Enum):
    """Tipos de fatos semânticos."""
    # Sobre entidades
    ENTITY_TRAIT = "entity_trait"           # Característica de entidade
    ENTITY_RELATION = "entity_relation"     # Relação entre entidades
    ENTITY_ABILITY = "entity_ability"       # Habilidade de entidade
    ENTITY_WEAKNESS = "entity_weakness"     # Fraqueza de entidade
    ENTITY_AFFILIATION = "entity_affiliation"  # Afiliação a facção/grupo
    
    # Sobre locais
    LOCATION_TRAIT = "location_trait"       # Característica de local
    LOCATION_DANGER = "location_danger"     # Perigo em local
    LOCATION_RESOURCE = "location_resource" # Recurso em local
    
    # Sobre o mundo
    WORLD_RULE = "world_rule"               # Regra do mundo
    WORLD_EVENT = "world_event"             # Evento mundial
    
    # Sobre o jogador
    PLAYER_PREFERENCE = "player_preference" # Preferência do jogador
    PLAYER_ENEMY = "player_enemy"           # Inimigo do jogador
    PLAYER_ALLY = "player_ally"             # Aliado do jogador


class FactConfidence(str, Enum):
    """Nível de confiança em um fato."""
    CERTAIN = "certain"       # Testemunhou diretamente
    PROBABLE = "probable"     # Evidência forte
    POSSIBLE = "possible"     # Alguma evidência
    RUMOR = "rumor"           # Ouviu dizer
    SPECULATION = "speculation"  # Dedução própria


@dataclass
class SemanticFact:
    """
    Um fato semântico - conhecimento extraído de experiências.
    
    Attributes:
        entity_id: ID da entidade dona do fato
        fact_type: Tipo do fato
        subject: Sobre quem/o quê é o fato
        predicate: O que está sendo afirmado
        object: Objeto da afirmação (se houver)
        confidence: Nível de confiança
        source_memory_ids: IDs das memórias que originaram este fato
        first_learned: Quando aprendeu este fato
        last_confirmed: Última confirmação
        times_confirmed: Quantas vezes foi confirmado
        embedding: Vetor para busca semântica
    """
    entity_id: int
    fact_type: FactType
    subject: str           # Ex: "Yi Fan"
    predicate: str         # Ex: "é hostil"
    object: Optional[str] = None  # Ex: "ao jogador"
    confidence: FactConfidence = FactConfidence.POSSIBLE
    source_memory_ids: List[int] = field(default_factory=list)
    first_learned: datetime = field(default_factory=datetime.utcnow)
    last_confirmed: datetime = field(default_factory=datetime.utcnow)
    times_confirmed: int = 1
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # ID do banco (gerado como hash do fato)
    id: Optional[str] = None
    
    def __post_init__(self):
        """Gera ID único baseado no conteúdo do fato."""
        if self.id is None:
            import hashlib
            content = f"{self.entity_id}:{self.subject}:{self.predicate}:{self.object or ''}"
            self.id = hashlib.md5(content.encode()).hexdigest()[:12]
    
    def get_statement(self) -> str:
        """Retorna o fato como uma frase."""
        if self.object:
            return f"{self.subject} {self.predicate} {self.object}"
        return f"{self.subject} {self.predicate}"
    
    def matches(self, subject: Optional[str] = None, predicate_contains: Optional[str] = None) -> bool:
        """Verifica se o fato corresponde aos critérios."""
        if subject and subject.lower() not in self.subject.lower():
            return False
        if predicate_contains and predicate_contains.lower() not in self.predicate.lower():
            return False
        return True
    
    def strengthen(self, source_memory_id: Optional[int] = None) -> None:
        """Fortalece o fato (foi confirmado novamente)."""
        self.times_confirmed += 1
        self.last_confirmed = datetime.utcnow()
        
        if source_memory_id and source_memory_id not in self.source_memory_ids:
            self.source_memory_ids.append(source_memory_id)
        
        # Aumentar confiança baseado em confirmações
        if self.times_confirmed >= 5 and self.confidence != FactConfidence.CERTAIN:
            self.confidence = FactConfidence.CERTAIN
        elif self.times_confirmed >= 3 and self.confidence == FactConfidence.POSSIBLE:
            self.confidence = FactConfidence.PROBABLE
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "fact_type": self.fact_type.value,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "confidence": self.confidence.value,
            "source_memory_ids": self.source_memory_ids,
            "first_learned": self.first_learned.isoformat(),
            "last_confirmed": self.last_confirmed.isoformat(),
            "times_confirmed": self.times_confirmed,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SemanticFact":
        """Deserializa de dicionário."""
        fact = cls(
            entity_id=data["entity_id"],
            fact_type=FactType(data["fact_type"]),
            subject=data["subject"],
            predicate=data["predicate"],
            object=data.get("object"),
            confidence=FactConfidence(data.get("confidence", "possible")),
            source_memory_ids=data.get("source_memory_ids", []),
            first_learned=datetime.fromisoformat(data["first_learned"]),
            last_confirmed=datetime.fromisoformat(data["last_confirmed"]),
            times_confirmed=data.get("times_confirmed", 1),
            metadata=data.get("metadata", {}),
        )
        fact.id = data.get("id")
        return fact


class SemanticStore:
    """
    Store para fatos semânticos.
    Usa a tabela de memória existente com tipo "semantic".
    """
    
    def __init__(self, session: "AsyncSession"):
        self.session = session
        self._embedding_service = None
        # Cache em memória de fatos por entidade
        self._fact_cache: Dict[int, Dict[str, SemanticFact]] = {}
    
    @property
    def embedding_service(self):
        """Lazy load do embedding service."""
        if self._embedding_service is None:
            from app.services.embedding_service import EmbeddingService
            self._embedding_service = EmbeddingService()
        return self._embedding_service
    
    async def upsert(self, fact: SemanticFact) -> SemanticFact:
        """
        Insere ou atualiza um fato.
        Se o fato já existe (mesmo subject/predicate), fortalece.
        """
        # Verificar se já existe no cache
        entity_facts = self._fact_cache.get(fact.entity_id, {})
        existing = entity_facts.get(fact.id)
        
        if existing:
            # Fortalecer fato existente
            existing.strengthen()
            await self._persist_fact(existing)
            return existing
        
        # Verificar no banco
        existing_from_db = await self._find_existing(fact)
        if existing_from_db:
            existing_from_db.strengthen()
            await self._persist_fact(existing_from_db)
            
            # Atualizar cache
            if fact.entity_id not in self._fact_cache:
                self._fact_cache[fact.entity_id] = {}
            self._fact_cache[fact.entity_id][existing_from_db.id] = existing_from_db
            
            return existing_from_db
        
        # Novo fato
        fact.embedding = self._generate_embedding(fact)
        await self._persist_fact(fact)
        
        # Adicionar ao cache
        if fact.entity_id not in self._fact_cache:
            self._fact_cache[fact.entity_id] = {}
        self._fact_cache[fact.entity_id][fact.id] = fact
        
        logger.info(f"Fato semântico adicionado: {fact.get_statement()}")
        return fact
    
    async def _find_existing(self, fact: SemanticFact) -> Optional[SemanticFact]:
        """Busca fato existente no banco."""
        from sqlalchemy import text
        
        # Buscar por conteúdo similar
        sql = text("""
            SELECT id, content FROM memory
            WHERE npc_id = :entity_id
            AND content LIKE :pattern
            LIMIT 1
        """)
        
        # Padrão para encontrar fatos semânticos com mesmo subject/predicate
        pattern = f'%"type": "semantic"%"subject": "{fact.subject}"%"predicate": "{fact.predicate}"%'
        
        result = await self.session.execute(sql, {
            "entity_id": fact.entity_id,
            "pattern": pattern
        })
        
        row = result.fetchone()
        if row:
            return self._parse_fact_content(row[0], row[1], fact.entity_id)
        
        return None
    
    async def _persist_fact(self, fact: SemanticFact) -> None:
        """Persiste fato no banco."""
        from sqlalchemy import text
        from pgvector.sqlalchemy import Vector
        from sqlalchemy import bindparam
        
        content = json.dumps({
            "type": "semantic",
            **fact.to_dict()
        }, ensure_ascii=False)
        
        # Verificar se já existe no banco (por ID do fato)
        check_sql = text("""
            SELECT id FROM memory 
            WHERE npc_id = :entity_id 
            AND content LIKE :pattern
            LIMIT 1
        """)
        
        result = await self.session.execute(check_sql, {
            "entity_id": fact.entity_id,
            "pattern": f'%"id": "{fact.id}"%'
        })
        
        existing_row = result.fetchone()
        
        if existing_row:
            # Atualizar existente
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
            # Inserir novo
            insert_sql = text("""
                INSERT INTO memory (npc_id, content, embedding)
                VALUES (:entity_id, :content, :embedding)
            """).bindparams(
                bindparam("embedding", type_=Vector(128))
            )
            
            await self.session.execute(insert_sql, {
                "entity_id": fact.entity_id,
                "content": content,
                "embedding": fact.embedding,
            })
        
        await self.session.commit()
    
    def _generate_embedding(self, fact: SemanticFact) -> List[float]:
        """Gera embedding para um fato."""
        statement = fact.get_statement()
        vec = self.embedding_service.generate_embedding(statement)
        
        # Ajustar para 128D
        if len(vec) > 128:
            vec = vec[:128]
        elif len(vec) < 128:
            vec = vec + [0.0] * (128 - len(vec))
        
        return vec
    
    async def query(
        self,
        entity_id: int,
        query_text: Optional[str] = None,
        subject: Optional[str] = None,
        fact_types: Optional[List[FactType]] = None,
        min_confidence: FactConfidence = FactConfidence.RUMOR,
        limit: int = 10
    ) -> List[SemanticFact]:
        """
        Busca fatos semânticos com filtros.
        
        Args:
            entity_id: ID da entidade
            query_text: Texto para busca semântica (opcional)
            subject: Filtrar por subject (opcional)
            fact_types: Tipos de fato para filtrar (opcional)
            min_confidence: Confiança mínima
            limit: Máximo de resultados
        
        Returns:
            Lista de fatos ordenados por relevância/confiança
        """
        from sqlalchemy import text
        
        # Buscar todos os fatos semânticos da entidade
        sql = text("""
            SELECT id, content FROM memory
            WHERE npc_id = :entity_id
            AND content LIKE '%"type": "semantic"%'
            ORDER BY id DESC
            LIMIT :limit
        """)
        
        result = await self.session.execute(sql, {
            "entity_id": entity_id,
            "limit": limit * 3  # Pegar mais para filtrar
        })
        
        rows = result.fetchall()
        facts = []
        
        confidence_order = [
            FactConfidence.CERTAIN,
            FactConfidence.PROBABLE,
            FactConfidence.POSSIBLE,
            FactConfidence.RUMOR,
            FactConfidence.SPECULATION,
        ]
        min_conf_index = confidence_order.index(min_confidence)
        
        for row in rows:
            fact = self._parse_fact_content(row[0], row[1], entity_id)
            if not fact:
                continue
            
            # Filtrar por subject
            if subject and not fact.matches(subject=subject):
                continue
            
            # Filtrar por fact_types
            if fact_types and fact.fact_type not in fact_types:
                continue
            
            # Filtrar por confiança
            fact_conf_index = confidence_order.index(fact.confidence)
            if fact_conf_index > min_conf_index:
                continue
            
            facts.append(fact)
            
            if len(facts) >= limit:
                break
        
        # Se houver query_text, reordenar por relevância semântica
        if query_text and facts:
            facts = await self._rerank_by_similarity(facts, query_text)
        
        return facts
    
    async def _rerank_by_similarity(
        self, 
        facts: List[SemanticFact], 
        query_text: str
    ) -> List[SemanticFact]:
        """Reordena fatos por similaridade com a query."""
        query_vec = self.embedding_service.generate_embedding(query_text)
        if len(query_vec) > 128:
            query_vec = query_vec[:128]
        elif len(query_vec) < 128:
            query_vec = query_vec + [0.0] * (128 - len(query_vec))
        
        # Calcular similaridade para cada fato
        def cosine_similarity(vec1, vec2):
            if not vec1 or not vec2:
                return 0.0
            dot = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(b * b for b in vec2) ** 0.5
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return dot / (norm1 * norm2)
        
        scored_facts = []
        for fact in facts:
            if fact.embedding:
                score = cosine_similarity(query_vec, fact.embedding)
            else:
                score = 0.0
            scored_facts.append((fact, score))
        
        # Ordenar por score descendente
        scored_facts.sort(key=lambda x: x[1], reverse=True)
        
        return [f for f, _ in scored_facts]
    
    async def get_all_facts(self, entity_id: int) -> List[SemanticFact]:
        """Retorna todos os fatos de uma entidade."""
        return await self.query(entity_id, limit=100)
    
    async def get_facts_about(self, entity_id: int, subject: str) -> List[SemanticFact]:
        """Retorna todos os fatos sobre um sujeito específico."""
        return await self.query(entity_id, subject=subject, limit=20)
    
    async def get_entity_relationships(self, entity_id: int) -> List[SemanticFact]:
        """Retorna fatos de relacionamento."""
        return await self.query(
            entity_id, 
            fact_types=[FactType.ENTITY_RELATION],
            limit=20
        )
    
    async def get_known_dangers(self, entity_id: int) -> List[SemanticFact]:
        """Retorna perigos conhecidos."""
        return await self.query(
            entity_id,
            fact_types=[FactType.LOCATION_DANGER, FactType.ENTITY_WEAKNESS],
            limit=10
        )
    
    async def forget(self, entity_id: int, fact_id: str) -> bool:
        """Remove um fato (esquece)."""
        from sqlalchemy import text
        
        # Remover do cache
        if entity_id in self._fact_cache:
            if fact_id in self._fact_cache[entity_id]:
                del self._fact_cache[entity_id][fact_id]
        
        # Remover do banco
        sql = text("""
            DELETE FROM memory
            WHERE npc_id = :entity_id
            AND content LIKE :pattern
        """)
        
        await self.session.execute(sql, {
            "entity_id": entity_id,
            "pattern": f'%"id": "{fact_id}"%'
        })
        
        await self.session.commit()
        logger.info(f"Fato esquecido: {fact_id}")
        return True
    
    def _parse_fact_content(
        self, 
        memory_id: int, 
        content: str, 
        entity_id: int
    ) -> Optional[SemanticFact]:
        """Parseia conteúdo de fato do banco."""
        try:
            data = json.loads(content)
            
            if data.get("type") != "semantic":
                return None
            
            return SemanticFact.from_dict(data)
            
        except Exception as e:
            logger.warning(f"Erro ao parsear fato {memory_id}: {e}")
            return None
    
    def clear_cache(self, entity_id: Optional[int] = None) -> None:
        """Limpa cache de fatos."""
        if entity_id:
            if entity_id in self._fact_cache:
                del self._fact_cache[entity_id]
        else:
            self._fact_cache.clear()
