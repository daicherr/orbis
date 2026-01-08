from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from app.config import settings

# Cria engine assíncrono; para psycopg3/async basta usar create_async_engine com o driver 'postgresql+psycopg'
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True,
)

async def init_db():
    # Importar todos os modelos para que o SQLModel os registre no metadata
    from app.database.models.player import Player
    from app.database.models.npc import NPC
    from app.database.models.world_state import WorldEvent, Faction, GlobalEconomy
    from app.database.models.logs import GameLog
    from app.database.models.location import DynamicLocation, LocationAlias
    from app.database.models.quest import Quest
    from app.database.models.memory import Memory
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
