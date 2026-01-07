import asyncio
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import text
from app.database.db_connection import engine
from app.database.models.npc import NPC
from app.database.repositories.npc_repo import NpcRepository

async def seed_initial_npcs():
    """Popula o banco de dados com NPCs iniciais se eles não existirem."""
    
    initial_npcs = [
        NPC(name="Ferreiro Wang", personality_traits=["rude", "habilidoso", "orgulhoso"], current_location="Forja da Vila"),
        NPC(name="Anciã Mei", personality_traits=["sábia", "gentil", "misteriosa"], current_location="Casa de Chá"),
        NPC(name="Guarda Chen", personality_traits=["leal", "severo", "vigilante"], current_location="Portão da Vila"),
        NPC(name="Vendedor Ambulante Li", personality_traits=["ganancioso", "falador", "covarde"], current_location="Praça do Mercado"),
    ]

    print("Iniciando o povoamento do banco de dados com NPCs...")
    
    async with AsyncSession(engine) as session:
        npc_repo = NpcRepository(session)
        
        for npc_data in initial_npcs:
            # Verifica se um NPC com o mesmo nome já existe
            result = await session.exec(select(NPC).where(NPC.name == npc_data.name))
            exists = result.first()
            if exists is None:
                print(f"Criando NPC: {npc_data.name}")
                await npc_repo.create(npc_data)
            else:
                print(f"NPC '{npc_data.name}' já existe. Pulando.")
    
    print("Povoamento do banco de dados concluído.")

if __name__ == "__main__":
    # Para executar este script de forma independente:
    # python -m app.database.init_db
    asyncio.run(seed_initial_npcs())

async def ensure_pgvector_extension():
    """Garante que a extensão 'vector' (pgvector) esteja habilitada."""
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        print("Extensão pgvector verificada/habilitada.")
