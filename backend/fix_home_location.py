"""Quick fix para adicionar colunas e atualizar home_location dos players existentes"""
import asyncio
from sqlalchemy import text
from app.database.db_connection import engine

async def add_columns_and_update():
    # Adicionar colunas primeiro
    columns_to_add = [
        ("home_location", "VARCHAR(255)"),
        ("home_location_id", "INTEGER"),
        ("first_scene_context", "TEXT"),
        ("important_npc_name", "VARCHAR(100)")
    ]
    
    async with engine.begin() as conn:
        for col_name, col_type in columns_to_add:
            try:
                await conn.execute(text(f"ALTER TABLE player ADD COLUMN {col_name} {col_type}"))
                print(f"✅ Coluna 'player.{col_name}' adicionada")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print(f"⏭️ Coluna 'player.{col_name}' já existe")
                else:
                    print(f"⚠️ Erro: {e}")
    
    # Atualizar players em transação separada
    async with engine.begin() as conn:
        try:
            result = await conn.execute(text("""
                UPDATE player 
                SET home_location = origin_location 
                WHERE home_location IS NULL AND origin_location IS NOT NULL
            """))
            print(f"✅ Players atualizados: home_location = origin_location")
        except Exception as e:
            print(f"⚠️ Erro ao atualizar: {e}")

if __name__ == "__main__":
    asyncio.run(add_columns_and_update())
