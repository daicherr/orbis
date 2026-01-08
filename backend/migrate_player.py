"""
Script de migração para adicionar novas colunas do GDD ao Player
"""
import asyncio
from sqlalchemy import text
from app.database.db_connection import engine

async def migrate_player_table():
    """Adiciona colunas novas do GDD ao Player table"""
    
    migrations = [
        # Sistema de Cultivation
        "ALTER TABLE player ADD COLUMN IF NOT EXISTS cultivation_tier INTEGER DEFAULT 1",
        "ALTER TABLE player ADD COLUMN IF NOT EXISTS can_fly BOOLEAN DEFAULT FALSE",
        "ALTER TABLE player ADD COLUMN IF NOT EXISTS physics_type VARCHAR DEFAULT 'newtonian'",
        
        # Tríade Energética - Máximos
        "ALTER TABLE player ADD COLUMN IF NOT EXISTS max_quintessential_essence FLOAT DEFAULT 100.0",
        "ALTER TABLE player ADD COLUMN IF NOT EXISTS max_shadow_chi FLOAT DEFAULT 100.0",
        "ALTER TABLE player ADD COLUMN IF NOT EXISTS max_yuan_qi FLOAT DEFAULT 100.0",
        
        # Atributos de Combate Adicionais
        "ALTER TABLE player ADD COLUMN IF NOT EXISTS speed FLOAT DEFAULT 10.0",
        "ALTER TABLE player ADD COLUMN IF NOT EXISTS strength FLOAT DEFAULT 10.0",
        "ALTER TABLE player ADD COLUMN IF NOT EXISTS betrayals INTEGER DEFAULT 0",
        
        # Localização
        "ALTER TABLE player ADD COLUMN IF NOT EXISTS current_location VARCHAR DEFAULT 'Início da Jornada'",
        
        # Arrays e Alquimia
        "ALTER TABLE player ADD COLUMN IF NOT EXISTS active_arrays JSON DEFAULT '[]'",
        "ALTER TABLE player ADD COLUMN IF NOT EXISTS spiritual_flames JSON DEFAULT '[]'",
        "ALTER TABLE player ADD COLUMN IF NOT EXISTS learned_skills JSON DEFAULT '[\"silent_strike\"]'",
    ]
    
    async with engine.begin() as conn:
        print("🔧 Iniciando migração do Player table...")
        for migration_sql in migrations:
            try:
                await conn.execute(text(migration_sql))
                col_name = migration_sql.split("ADD COLUMN IF NOT EXISTS")[1].split()[0]
                print(f"  ✅ Coluna '{col_name}' adicionada/verificada")
            except Exception as e:
                print(f"  ⚠️ Erro: {e}")
        
        print("✨ Migração concluída!")

if __name__ == "__main__":
    asyncio.run(migrate_player_table())
