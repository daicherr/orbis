"""
WorldEventRepository - Gerencia eventos globais que afetam todos os players
Permite criar eventos e investigá-los
"""
from typing import Optional, List
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.world_state import WorldEvent


class WorldEventRepository:
    """
    Repository para WorldEvent.
    Gerencia eventos que afetam o mundo e podem ser investigados por players.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_event(
        self,
        event_type: str,
        description: str,
        turn_occurred: int,
        location_affected: str = None,
        caused_by_player_id: int = None,
        caused_by_npc_id: int = None,
        author_alias: str = None,
        public_description: str = None,
        secret_description: str = None,
        investigation_difficulty: int = 5,
        clues: List[str] = None,
        effects: dict = None
    ) -> WorldEvent:
        """
        Cria um novo evento global.
        
        Exemplo:
            create_event(
                event_type="destruction",
                description="A Vila Crisântemos foi arrasada por um cultivador misterioso",
                turn_occurred=42,
                location_affected="Vila Crisântemos",
                caused_by_player_id=5,  # Player 5 fez isso
                author_alias="Demônio de Olhos Vermelhos",
                public_description="Uma tragédia terrível ocorreu na Vila Crisântemos",
                secret_description="O atacante usava técnicas da Seita da Lua Sombria",
                investigation_difficulty=7,
                clues=["Marcas de garras demoníacas", "Cheiro de enxofre"]
            )
        """
        event = WorldEvent(
            event_type=event_type,
            description=description,
            turn_occurred=turn_occurred,
            location_affected=location_affected,
            caused_by_player_id=caused_by_player_id,
            caused_by_npc_id=caused_by_npc_id,
            author_alias=author_alias or "Desconhecido",
            public_description=public_description or description,
            secret_description=secret_description or "",
            investigation_difficulty=investigation_difficulty,
            clues=clues or [],
            effects=effects or {},
            is_active=True
        )
        
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event
    
    async def get_events_for_location(self, location: str) -> List[WorldEvent]:
        """
        Busca eventos que afetam uma localização específica.
        Usado quando player chega em um local para modificar a descrição.
        """
        stmt = select(WorldEvent).where(
            WorldEvent.location_affected == location,
            WorldEvent.is_active == True
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_active_events(self) -> List[WorldEvent]:
        """Busca todos os eventos ativos no mundo"""
        stmt = select(WorldEvent).where(WorldEvent.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_events_by_player(self, player_id: int) -> List[WorldEvent]:
        """Busca eventos causados por um player específico"""
        stmt = select(WorldEvent).where(WorldEvent.caused_by_player_id == player_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def investigate_event(
        self,
        event_id: int,
        investigator_rank: int
    ) -> dict:
        """
        Player tenta investigar um evento para descobrir o autor.
        
        Retorna:
            {
                "success": True/False,
                "clues_found": ["pista1", "pista2"],
                "author_revealed": True/False,
                "author_info": {...} se revelado
            }
        """
        stmt = select(WorldEvent).where(WorldEvent.id == event_id)
        result = await self.session.execute(stmt)
        event = result.scalar_one_or_none()
        
        if not event:
            return {"success": False, "reason": "Evento não encontrado"}
        
        # Dificuldade vs Rank do investigador
        # Rank 1-3: Pode investigar dificuldade 1-3
        # Rank 4-6: Pode investigar dificuldade 4-6
        # Rank 7-9: Pode investigar qualquer dificuldade
        
        base_success_chance = (investigator_rank * 10) - (event.investigation_difficulty * 8)
        base_success_chance = max(10, min(90, base_success_chance))  # Entre 10% e 90%
        
        import random
        roll = random.randint(1, 100)
        
        response = {
            "success": roll <= base_success_chance,
            "clues_found": [],
            "author_revealed": False,
            "author_info": None,
            "public_info": event.public_description
        }
        
        if response["success"]:
            # Sucesso - revela pistas
            num_clues = min(len(event.clues), 1 + (investigator_rank // 3))
            response["clues_found"] = event.clues[:num_clues]
            
            # Se roll muito bom, revela autor
            if roll <= base_success_chance // 2:
                response["author_revealed"] = True
                response["secret_info"] = event.secret_description
                
                if event.caused_by_player_id:
                    response["author_info"] = {
                        "type": "player",
                        "alias": event.author_alias,
                        "player_id": event.caused_by_player_id
                    }
                elif event.caused_by_npc_id:
                    response["author_info"] = {
                        "type": "npc",
                        "alias": event.author_alias,
                        "npc_id": event.caused_by_npc_id
                    }
        
        return response
    
    async def mark_event_resolved(self, event_id: int):
        """Marca um evento como resolvido/inativo"""
        stmt = select(WorldEvent).where(WorldEvent.id == event_id)
        result = await self.session.execute(stmt)
        event = result.scalar_one_or_none()
        
        if event:
            event.is_active = False
            await self.session.commit()

    async def get_recent_events(self, limit: int = 10, since_turn: int = None) -> List[WorldEvent]:
        """
        Busca os eventos mais recentes.
        Usado pelos simuladores para verificar eventos que afetam economia.
        
        Args:
            limit: Número máximo de eventos a retornar
            since_turn: Buscar apenas eventos desde este turno (opcional)
        
        Returns:
            Lista de eventos ordenados por turn_occurred (mais recentes primeiro)
        """
        if since_turn is not None:
            stmt = select(WorldEvent).where(
                WorldEvent.turn_occurred >= since_turn
            ).order_by(WorldEvent.turn_occurred.desc()).limit(limit)
        else:
            stmt = select(WorldEvent).order_by(WorldEvent.turn_occurred.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_events_by_type(self, event_type: str, limit: int = 10) -> List[WorldEvent]:
        """
        Busca eventos por tipo.
        
        Args:
            event_type: Tipo do evento (destruction, war, alliance, etc.)
            limit: Número máximo de eventos
        
        Returns:
            Lista de eventos do tipo especificado
        """
        stmt = select(WorldEvent).where(
            WorldEvent.event_type == event_type
        ).order_by(WorldEvent.turn_occurred.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
