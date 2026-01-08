from typing import Optional, List
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database.models.npc import NPC

class NpcRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, npc: NPC) -> NPC:
        """Cria um novo NPC."""
        self.session.add(npc)
        await self.session.commit()
        await self.session.refresh(npc)
        return npc

    async def get_by_id(self, npc_id: int) -> Optional[NPC]:
        """Busca um NPC pelo seu ID."""
        result = await self.session.exec(select(NPC).where(NPC.id == npc_id))
        return result.one_or_none()
        
    async def get_all(self) -> List[NPC]:
        """Busca todos os NPCs do banco de dados."""
        result = await self.session.exec(select(NPC))
        return result.all()
    
    async def get_by_location(self, location: str) -> List[NPC]:
        """Busca NPCs em uma localização específica (filtro crítico)."""
        result = await self.session.exec(
            select(NPC).where(NPC.current_location == location)
        )
        return result.all()

    async def update(self, npc: NPC) -> NPC:
        """Atualiza os dados de um NPC no banco."""
        self.session.add(npc)
        await self.session.commit()
        await self.session.refresh(npc)
        return npc
