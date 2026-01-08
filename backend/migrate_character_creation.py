"""
Migração: Adiciona campos de Character Creation ao Player
Adiciona: appearance, constitution_type, origin_location, backstory
"""

import asyncio
from sqlmodel import text
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database.db_connection import engine

async def migrate():
    migrations = [
        "ALTER TABLE player ADD COLUMN IF NOT EXISTS appearance TEXT DEFAULT NULL;",
        "ALTER TABLE player ADD COLUMN IF NOT EXISTS constitution_type VARCHAR(50) DEFAULT 'Mortal' NOT NULL;",
        "ALTER TABLE player ADD COLUMN IF NOT EXISTS origin_location VARCHAR(100) DEFAULT 'Floresta Nublada' NOT NULL;",
        "ALTER TABLE player ADD COLUMN IF NOT EXISTS backstory TEXT DEFAULT NULL;",
    ]
    
    async with AsyncSession(engine) as session:
        for migration_sql in migrations:
            print(f"Executando: {migration_sql}")
            await session.exec(text(migration_sql))
            await session.commit()
    
    print("✅ Migração de Character Creation concluída!")

if __name__ == "__main__":
    asyncio.run(migrate())
