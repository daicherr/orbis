from typing import List
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import text
from pgvector.sqlalchemy import Vector
from app.services.embedding_service import EmbeddingService
from app.database.models.memory import Memory

class HybridSearchRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_memory(self, npc_id: int, content: str, embedding_dim: int = 128) -> Memory:
        """Insere uma memória com embedding calculado."""
        embedder = EmbeddingService()
        vec = embedder.generate_embedding(content)

        # Ajusta dimensão do vetor do modelo vs. coluna configurada
        # Se a dimensão divergir, redimensiona com truncamento/zero-pad
        if len(vec) != embedding_dim:
            if len(vec) > embedding_dim:
                vec = vec[:embedding_dim]
            else:
                vec = vec + [0.0] * (embedding_dim - len(vec))

        mem = Memory(npc_id=npc_id, content=content)
        # Atribui vetor diretamente; pgvector trata a conversão
        setattr(mem, "embedding", vec)

        self.session.add(mem)
        await self.session.commit()
        await self.session.refresh(mem)
        return mem

    async def find_relevant_memories(
        self, 
        npc_id: int, 
        query_text: str, 
        limit: int = 5
    ) -> List[str]:
        """
        Encontra as memórias mais relevantes para um NPC com base em uma consulta.
        Combina busca SQL (por palavras-chave) e busca vetorial (semântica).
        """
        
        # 1. Gerar o embedding da consulta
        embedder = EmbeddingService()
        query_vec = embedder.generate_embedding(query_text)
        # Adapta para 128D (compatível com Memory.embedding definido como Vector(128))
        if len(query_vec) > 128:
            query_vec = query_vec[:128]
        elif len(query_vec) < 128:
            query_vec = query_vec + [0.0] * (128 - len(query_vec))

        # 2. Executar a query híbrida (SQL + Vetor)
        # Esta é uma representação simplificada da query que seria necessária.
        # O pgvector permite calcular a distância entre vetores no próprio SQL.
        
        # query = """
        # SELECT content FROM memories
        # WHERE npc_id = :npc_id
        # ORDER BY embedding <-> :query_vector
        # LIMIT :limit
        # """
        
        # result = await self.session.execute(text(query), {
        #     "npc_id": npc_id,
        #     "query_vector": query_vector,
        #     "limit": limit
        # })
        
        # memories = result.scalars().all()

        # 2. Query híbrida: filtra por NPC e ordena pela distância vetorial (cosine)<->
        from sqlalchemy import bindparam
        sql = text(
            """
            SELECT content
            FROM memory
            WHERE npc_id = :npc_id
            ORDER BY embedding <-> :qvec
            LIMIT :limit
            """
        ).bindparams(
            bindparam("qvec", type_=Vector(128))
        )

        # O driver pgvector aceita lista de floats diretamente quando o tipo é Vector
        result = await self.session.execute(
            sql,
            {"npc_id": npc_id, "qvec": query_vec, "limit": limit},
        )
        rows = result.fetchall()
        return [r[0] for r in rows]
