"""Script de teste para verificar a API do RPG."""
import asyncio
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings
from app.database.models.player import Player

async def test_db():
    print("=== TESTE DE BANCO DE DADOS ===")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    async with AsyncSession(engine) as session:
        try:
            result = await session.exec(select(Player))
            players = result.all()
            print(f"✓ Encontrados {len(players)} jogadores:")
            for p in players:
                print(f"  - ID={p.id}: {p.name} (Tier {p.cultivation_tier}, HP={p.current_hp}/{p.max_hp})")
        except Exception as e:
            print(f"✗ Erro ao buscar jogadores: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db())
