from typing import Optional, List
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database.models.player import Player

class PlayerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, 
        name: str,
        appearance: Optional[str] = None,
        constitution_type: str = "Mortal",
        origin_location: str = "Floresta Nublada",
        backstory: Optional[str] = None,
        constitution: str = "Mortal Body"
    ) -> Player:
        """Cria um novo jogador com valores padrão, evitando duplicatas por nome."""
        # Verifica se já existe um jogador com este nome
        existing = await self.session.exec(
            select(Player).where(Player.name == name).order_by(Player.id.desc())
        )
        player = existing.first()
        if player:
            return player

        new_player = Player(
            name=name,
            appearance=appearance,
            constitution_type=constitution_type,
            origin_location=origin_location,
            backstory=backstory,
            constitution=constitution,
            current_location=origin_location  # Começa na origem
        )
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

    async def get_all(self) -> List[Player]:
        """Retorna todos os jogadores."""
        result = await self.session.exec(select(Player))
        return result.all()

