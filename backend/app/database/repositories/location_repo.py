"""
Location Repository - Acesso a dados de Localizações
GEM RPG ORBIS - Arquitetura Cognitiva

Repositório completo para operações com:
- Location: Locais estruturados do mapa do mundo
- DynamicLocation: Locais criados narrativamente
- LocationAlias: Aliases para referência rápida
- LocationVisit: Histórico de visitas
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database.models.location import (
    Location, DynamicLocation, LocationAlias, LocationVisit,
    LocationType, BiomeType, DangerLevel
)


class LocationRepository:
    """Repositório para localizações estruturadas do mapa."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    # ==================== CRUD BÁSICO ====================
    
    async def create(self, location: Location) -> Location:
        """Cria uma nova localização."""
        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        return location
    
    async def create_many(self, locations: List[Location]) -> List[Location]:
        """Cria múltiplas localizações."""
        for loc in locations:
            self.session.add(loc)
        await self.session.commit()
        for loc in locations:
            await self.session.refresh(loc)
        return locations
    
    async def get_by_id(self, location_id: int) -> Optional[Location]:
        """Busca uma localização pelo ID."""
        result = await self.session.exec(
            select(Location).where(Location.id == location_id)
        )
        return result.one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Location]:
        """Busca uma localização pelo nome exato."""
        result = await self.session.exec(
            select(Location).where(Location.name == name)
        )
        return result.one_or_none()
    
    async def search_by_name(self, name_partial: str) -> List[Location]:
        """Busca localizações cujo nome contém a string."""
        result = await self.session.exec(
            select(Location).where(Location.name.ilike(f"%{name_partial}%"))
        )
        return list(result.all())
    
    async def get_all(self) -> List[Location]:
        """Busca todas as localizações."""
        result = await self.session.exec(select(Location))
        return list(result.all())
    
    async def update(self, location: Location) -> Location:
        """Atualiza uma localização."""
        location.updated_at = datetime.utcnow()
        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        return location
    
    async def delete(self, location_id: int) -> bool:
        """Deleta uma localização."""
        location = await self.get_by_id(location_id)
        if location:
            await self.session.delete(location)
            await self.session.commit()
            return True
        return False

    # ==================== BUSCA POR TIPO ====================
    
    async def get_by_type(self, location_type: str) -> List[Location]:
        """Busca localizações por tipo."""
        result = await self.session.exec(
            select(Location).where(Location.location_type == location_type)
        )
        return list(result.all())
    
    async def get_cities(self) -> List[Location]:
        """Busca todas as cidades."""
        return await self.get_by_type(LocationType.CITY)
    
    async def get_villages(self) -> List[Location]:
        """Busca todas as vilas."""
        return await self.get_by_type(LocationType.VILLAGE)
    
    async def get_safe_zones(self) -> List[Location]:
        """Busca todas as zonas seguras."""
        result = await self.session.exec(
            select(Location).where(Location.is_safe_zone == True)
        )
        return list(result.all())
    
    async def get_by_biome(self, biome: str) -> List[Location]:
        """Busca localizações por bioma."""
        result = await self.session.exec(
            select(Location).where(Location.biome == biome)
        )
        return list(result.all())

    # ==================== BUSCA POR PERIGO/TIER ====================
    
    async def get_by_danger_level(self, danger_level: str) -> List[Location]:
        """Busca localizações por nível de perigo."""
        result = await self.session.exec(
            select(Location).where(Location.danger_level == danger_level)
        )
        return list(result.all())
    
    async def get_suitable_for_tier(self, player_tier: int) -> List[Location]:
        """Busca localizações adequadas para um tier de player."""
        result = await self.session.exec(
            select(Location).where(
                and_(
                    Location.recommended_tier <= player_tier,
                    Location.max_tier >= player_tier - 1  # Permite um pouco abaixo também
                )
            )
        )
        return list(result.all())
    
    async def get_challenging_for_tier(self, player_tier: int) -> List[Location]:
        """Busca localizações desafiadoras (1-2 tiers acima) para um player."""
        result = await self.session.exec(
            select(Location).where(
                and_(
                    Location.recommended_tier > player_tier,
                    Location.recommended_tier <= player_tier + 2
                )
            )
        )
        return list(result.all())

    # ==================== NAVEGAÇÃO/GRAFO ====================
    
    async def get_connected_locations(self, location_name: str) -> List[Location]:
        """Busca localizações conectadas a uma localização."""
        location = await self.get_by_name(location_name)
        if not location or not location.connections:
            return []
        
        connected_names = list(location.connections.keys())
        result = await self.session.exec(
            select(Location).where(Location.name.in_(connected_names))
        )
        return list(result.all())
    
    async def get_sub_locations(self, location_name: str) -> List[Location]:
        """Busca sub-localizações de uma localização."""
        location = await self.get_by_name(location_name)
        if not location or not location.sub_locations:
            return []
        
        result = await self.session.exec(
            select(Location).where(Location.name.in_(location.sub_locations))
        )
        return list(result.all())
    
    async def get_by_region(self, region_name: str) -> List[Location]:
        """Busca localizações em uma região."""
        result = await self.session.exec(
            select(Location).where(Location.parent_region == region_name)
        )
        return list(result.all())
    
    async def add_connection(
        self, 
        from_location: str, 
        to_location: str, 
        distance: int = 1,
        travel_time: str = "1 hour",
        danger: str = "low",
        bidirectional: bool = True
    ) -> bool:
        """Adiciona conexão entre duas localizações."""
        loc_from = await self.get_by_name(from_location)
        loc_to = await self.get_by_name(to_location)
        
        if not loc_from or not loc_to:
            return False
        
        # Adicionar conexão A -> B
        if loc_from.connections is None:
            loc_from.connections = {}
        loc_from.connections[to_location] = {
            "distance": distance,
            "travel_time": travel_time,
            "danger": danger
        }
        await self.update(loc_from)
        
        # Se bidirecional, adicionar B -> A
        if bidirectional:
            if loc_to.connections is None:
                loc_to.connections = {}
            loc_to.connections[from_location] = {
                "distance": distance,
                "travel_time": travel_time,
                "danger": danger
            }
            await self.update(loc_to)
        
        return True

    # ==================== FACÇÕES ====================
    
    async def get_by_faction(self, faction_id: str) -> List[Location]:
        """Busca localizações controladas por uma facção."""
        result = await self.session.exec(
            select(Location).where(Location.controlling_faction == faction_id)
        )
        return list(result.all())
    
    async def set_faction_control(
        self, 
        location_name: str, 
        faction_id: str, 
        influence: float = 100.0
    ) -> Optional[Location]:
        """Define controle de facção sobre uma localização."""
        location = await self.get_by_name(location_name)
        if location:
            location.controlling_faction = faction_id
            location.faction_influence = influence
            return await self.update(location)
        return None

    # ==================== RECURSOS ====================
    
    async def get_locations_with_resource(self, resource_type: str) -> List[Location]:
        """Busca localizações que têm um tipo de recurso."""
        all_locations = await self.get_all()
        return [
            loc for loc in all_locations 
            if loc.resources and resource_type in loc.resources
        ]
    
    async def add_resource(
        self, 
        location_name: str, 
        resource_type: str, 
        resource_names: List[str]
    ) -> Optional[Location]:
        """Adiciona recursos a uma localização."""
        location = await self.get_by_name(location_name)
        if location:
            if location.resources is None:
                location.resources = {}
            if resource_type not in location.resources:
                location.resources[resource_type] = []
            location.resources[resource_type].extend(resource_names)
            return await self.update(location)
        return None

    # ==================== CLIMA E EVENTOS ====================
    
    async def update_weather(self, location_name: str, weather: str) -> Optional[Location]:
        """Atualiza o clima atual de uma localização."""
        location = await self.get_by_name(location_name)
        if location:
            location.current_weather = weather
            return await self.update(location)
        return None
    
    async def get_locations_with_event(self, event_type: str) -> List[Location]:
        """Busca localizações que podem ter um tipo de evento."""
        all_locations = await self.get_all()
        return [
            loc for loc in all_locations 
            if loc.possible_events and event_type in loc.possible_events
        ]

    # ==================== CONTEXTO PARA IA ====================
    
    async def get_context_for_location(self, location_name: str) -> Dict[str, Any]:
        """
        Obtém contexto completo de uma localização para a IA.
        Inclui informações de navegação, perigo, recursos, etc.
        """
        location = await self.get_by_name(location_name)
        if not location:
            return {"error": f"Localização '{location_name}' não encontrada"}
        
        connected = await self.get_connected_locations(location_name)
        sub_locs = await self.get_sub_locations(location_name)
        
        return {
            "name": location.name,
            "display_name": location.display_name or location.name,
            "type": location.location_type,
            "biome": location.biome,
            "danger_level": location.danger_level,
            "tier_range": f"{location.recommended_tier}-{location.max_tier}",
            "description": location.description,
            "atmosphere": location.atmosphere,
            "current_weather": location.current_weather,
            "is_safe_zone": location.is_safe_zone,
            "controlling_faction": location.controlling_faction,
            "connected_locations": [c.name for c in connected],
            "sub_locations": [s.name for s in sub_locs],
            "resources": location.resources,
            "population": location.population,
            "context_string": location.to_context_string()
        }


class DynamicLocationRepository:
    """Repositório para localizações dinâmicas (criadas narrativamente)."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    # ==================== CRUD BÁSICO ====================
    
    async def create(self, location: DynamicLocation) -> DynamicLocation:
        """Cria uma nova localização dinâmica."""
        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        return location
    
    async def get_by_id(self, location_id: int) -> Optional[DynamicLocation]:
        """Busca uma localização dinâmica pelo ID."""
        result = await self.session.exec(
            select(DynamicLocation).where(DynamicLocation.id == location_id)
        )
        return result.one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[DynamicLocation]:
        """Busca uma localização dinâmica pelo nome."""
        result = await self.session.exec(
            select(DynamicLocation).where(DynamicLocation.name == name)
        )
        return result.one_or_none()
    
    async def search_by_name(self, name_partial: str) -> List[DynamicLocation]:
        """Busca localizações dinâmicas cujo nome contém a string."""
        result = await self.session.exec(
            select(DynamicLocation).where(DynamicLocation.name.ilike(f"%{name_partial}%"))
        )
        return list(result.all())
    
    async def get_all(self) -> List[DynamicLocation]:
        """Busca todas as localizações dinâmicas."""
        result = await self.session.exec(
            select(DynamicLocation).where(DynamicLocation.is_destroyed == False)
        )
        return list(result.all())
    
    async def update(self, location: DynamicLocation) -> DynamicLocation:
        """Atualiza uma localização dinâmica."""
        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        return location

    # ==================== BUSCA POR DONO ====================
    
    async def get_by_player(self, player_id: int) -> List[DynamicLocation]:
        """Busca localizações pertencentes a um player."""
        result = await self.session.exec(
            select(DynamicLocation).where(
                DynamicLocation.owner_player_id == player_id,
                DynamicLocation.is_destroyed == False
            )
        )
        return list(result.all())
    
    async def get_by_npc(self, npc_id: int) -> List[DynamicLocation]:
        """Busca localizações pertencentes a um NPC."""
        result = await self.session.exec(
            select(DynamicLocation).where(
                DynamicLocation.owner_npc_id == npc_id,
                DynamicLocation.is_destroyed == False
            )
        )
        return list(result.all())
    
    async def get_player_home(self, player_id: int) -> Optional[DynamicLocation]:
        """Busca a casa de um player."""
        result = await self.session.exec(
            select(DynamicLocation).where(
                DynamicLocation.owner_player_id == player_id,
                DynamicLocation.location_type == "residence",
                DynamicLocation.is_destroyed == False
            )
        )
        return result.first()

    # ==================== BUSCA POR LOCALIZAÇÃO PAI ====================
    
    async def get_by_parent(self, parent_location: str) -> List[DynamicLocation]:
        """Busca localizações dinâmicas em uma localização pai."""
        result = await self.session.exec(
            select(DynamicLocation).where(
                DynamicLocation.parent_location == parent_location,
                DynamicLocation.is_destroyed == False
            )
        )
        return list(result.all())
    
    async def get_shops_at_location(self, parent_location: str) -> List[DynamicLocation]:
        """Busca lojas em uma localização."""
        result = await self.session.exec(
            select(DynamicLocation).where(
                DynamicLocation.parent_location == parent_location,
                DynamicLocation.location_type == "shop",
                DynamicLocation.is_destroyed == False
            )
        )
        return list(result.all())

    # ==================== OPERAÇÕES ESPECIAIS ====================
    
    async def destroy(self, location_id: int, event_id: Optional[int] = None) -> Optional[DynamicLocation]:
        """Marca uma localização como destruída."""
        location = await self.get_by_id(location_id)
        if location:
            location.is_destroyed = True
            location.destruction_event_id = event_id
            return await self.update(location)
        return None
    
    async def record_visit(self, location_id: int) -> Optional[DynamicLocation]:
        """Registra visita a uma localização."""
        location = await self.get_by_id(location_id)
        if location:
            location.last_visited_at = datetime.utcnow()
            return await self.update(location)
        return None


class LocationAliasRepository:
    """Repositório para aliases de localização."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, alias: LocationAlias) -> LocationAlias:
        """Cria um novo alias."""
        self.session.add(alias)
        await self.session.commit()
        await self.session.refresh(alias)
        return alias
    
    async def get_by_alias(self, alias: str, player_id: int) -> Optional[LocationAlias]:
        """Busca alias para um player específico."""
        result = await self.session.exec(
            select(LocationAlias).where(
                LocationAlias.alias == alias.lower(),
                LocationAlias.player_id == player_id
            )
        )
        return result.one_or_none()
    
    async def get_player_aliases(self, player_id: int) -> List[LocationAlias]:
        """Busca todos os aliases de um player."""
        result = await self.session.exec(
            select(LocationAlias).where(LocationAlias.player_id == player_id)
        )
        return list(result.all())
    
    async def set_alias(
        self, 
        player_id: int, 
        alias: str, 
        location_id: Optional[int] = None,
        static_location_name: Optional[str] = None,
        static_location_id: Optional[int] = None
    ) -> LocationAlias:
        """Define ou atualiza um alias."""
        existing = await self.get_by_alias(alias, player_id)
        
        if existing:
            existing.location_id = location_id
            existing.static_location_name = static_location_name
            existing.static_location_id = static_location_id
            self.session.add(existing)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        
        new_alias = LocationAlias(
            alias=alias.lower(),
            player_id=player_id,
            location_id=location_id,
            static_location_name=static_location_name,
            static_location_id=static_location_id
        )
        return await self.create(new_alias)
    
    async def delete_alias(self, alias: str, player_id: int) -> bool:
        """Remove um alias."""
        existing = await self.get_by_alias(alias, player_id)
        if existing:
            await self.session.delete(existing)
            await self.session.commit()
            return True
        return False


class LocationVisitRepository:
    """Repositório para histórico de visitas."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def record_visit(
        self,
        player_id: int,
        location_name: str,
        location_id: Optional[int] = None,
        dynamic_location_id: Optional[int] = None
    ) -> LocationVisit:
        """Registra ou atualiza uma visita."""
        # Buscar visita existente
        result = await self.session.exec(
            select(LocationVisit).where(
                LocationVisit.player_id == player_id,
                LocationVisit.location_name == location_name
            )
        )
        existing = result.one_or_none()
        
        if existing:
            existing.last_visit = datetime.utcnow()
            existing.visit_count += 1
            self.session.add(existing)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        
        visit = LocationVisit(
            player_id=player_id,
            location_name=location_name,
            location_id=location_id,
            dynamic_location_id=dynamic_location_id
        )
        self.session.add(visit)
        await self.session.commit()
        await self.session.refresh(visit)
        return visit
    
    async def get_player_visits(self, player_id: int) -> List[LocationVisit]:
        """Busca histórico de visitas de um player."""
        result = await self.session.exec(
            select(LocationVisit).where(LocationVisit.player_id == player_id)
        )
        return list(result.all())
    
    async def has_visited(self, player_id: int, location_name: str) -> bool:
        """Verifica se um player já visitou uma localização."""
        result = await self.session.exec(
            select(LocationVisit).where(
                LocationVisit.player_id == player_id,
                LocationVisit.location_name == location_name
            )
        )
        return result.one_or_none() is not None
    
    async def get_discovered_locations(self, player_id: int) -> List[str]:
        """Retorna lista de localizações descobertas por um player."""
        visits = await self.get_player_visits(player_id)
        return [v.location_name for v in visits]
    
    async def add_secret_found(
        self, 
        player_id: int, 
        location_name: str, 
        secret: str
    ) -> Optional[LocationVisit]:
        """Adiciona um segredo descoberto em uma localização."""
        result = await self.session.exec(
            select(LocationVisit).where(
                LocationVisit.player_id == player_id,
                LocationVisit.location_name == location_name
            )
        )
        visit = result.one_or_none()
        
        if visit:
            if visit.secrets_found is None:
                visit.secrets_found = []
            if secret not in visit.secrets_found:
                visit.secrets_found.append(secret)
                self.session.add(visit)
                await self.session.commit()
                await self.session.refresh(visit)
            return visit
        return None
    
    async def add_npc_met(
        self, 
        player_id: int, 
        location_name: str, 
        npc_name: str
    ) -> Optional[LocationVisit]:
        """Adiciona um NPC encontrado em uma localização."""
        result = await self.session.exec(
            select(LocationVisit).where(
                LocationVisit.player_id == player_id,
                LocationVisit.location_name == location_name
            )
        )
        visit = result.one_or_none()
        
        if visit:
            if visit.npcs_met is None:
                visit.npcs_met = []
            if npc_name not in visit.npcs_met:
                visit.npcs_met.append(npc_name)
                self.session.add(visit)
                await self.session.commit()
                await self.session.refresh(visit)
            return visit
        return None
