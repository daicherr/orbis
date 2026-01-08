"""Migração para adicionar coluna gold na tabela player."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config import settings

async def migrate():
    print("=== MIGRAÇÃO: Adicionar coluna 'gold' na tabela player ===")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        # Verificar se a coluna já existe
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'player' AND column_name = 'gold'
        """))
        exists = result.fetchone()
        
        if exists:
            print("✓ Coluna 'gold' já existe.")
        else:
            print("Adicionando coluna 'gold'...")
            await conn.execute(text("""
                ALTER TABLE player 
                ADD COLUMN gold INTEGER DEFAULT 100
            """))
            print("✓ Coluna 'gold' adicionada com sucesso!")
    
    await engine.dispose()
    print("Migração concluída!")

if __name__ == "__main__":
    asyncio.run(migrate())
