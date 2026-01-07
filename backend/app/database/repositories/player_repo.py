from typing import Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database.models.player import Player

class PlayerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str) -> Player:
        """Cria um novo jogador com valores padrão, evitando duplicatas por nome."""
        # Verifica se já existe um jogador com este nome
        existing = await self.session.exec(
            select(Player).where(Player.name == name).order_by(Player.id.desc())
        )
        player = existing.first()
        if player:
            return player

        new_player = Player(name=name)
        self.session.add(new_player)
        await self.session.commit()
        await self.session.refresh(new_player)
        return new_player

    async def get_by_id(self, player_id: int) -> Optional[Player]:
        """Busca um jogador pelo seu ID."""
        result = await self.session.exec(select(Player).where(Player.id == player_id))
        return result.one_or_none()

    async def get_by_name(self, name: str) -> Optional[Player]:
        """Busca um jogador pelo nome."""
        result = await self.session.exec(
            select(Player).where(Player.name == name).order_by(Player.id.desc())
        )
        return result.first()

    async def update(self, player: Player) -> Player:
        """Atualiza os dados de um jogador no banco."""
        self.session.add(player)
        await self.session.commit()
        await self.session.refresh(player)
        return player

