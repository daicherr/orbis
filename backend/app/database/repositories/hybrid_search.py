from typing import List
from sqlmodel.ext.asyncio.session import AsyncSession
# from pgvector.sqlalchemy import Vector
# from app.services.embedding_service import generate_embedding

class HybridSearchRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

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
        # query_vector = generate_embedding(query_text)

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

        print(f"Buscando memórias para NPC {npc_id} sobre '{query_text}'...")

        # Retorno mockado, pois a implementação real depende do pgvector
        mock_memories = [
            f"Lembro-me de quando o jogador me ajudou com os goblins.",
            f"O jogador mencionou uma vez que gosta de chá de jasmim.",
            f"Aquele dia na praça do mercado foi muito movimentado."
        ]
        
        return mock_memories[:limit]
