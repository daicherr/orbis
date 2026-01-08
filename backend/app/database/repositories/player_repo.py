from typing import Optional, List
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
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
        constitution: str = "Mortal Body",
        # Novos campos para contexto inicial
        first_scene_context: Optional[str] = None,
        important_npc_name: Optional[str] = None
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
            current_location=origin_location,  # Começa na origem
            # Novos campos
            first_scene_context=first_scene_context,
            important_npc_name=important_npc_name,
            home_location=origin_location  # Default: home = origin
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
        # Marcar campos JSON como modificados para forçar UPDATE
        flag_modified(player, 'inventory')
        flag_modified(player, 'status_effects')
        flag_modified(player, 'learned_skills')
        flag_modified(player, 'active_arrays')
        flag_modified(player, 'spiritual_flames')
        flag_modified(player, 'kill_history')
        
        self.session.add(player)
        await self.session.commit()
        await self.session.refresh(player)
        return player

    async def get_all(self) -> List[Player]:
        """Retorna todos os jogadores."""
        result = await self.session.exec(select(Player))
        return result.all()

    async def delete(self, player_id: int) -> bool:
        """Deleta um jogador pelo ID."""
        player = await self.get_by_id(player_id)
        if player:
            await self.session.delete(player)
            await self.session.commit()
            return True
        return False

