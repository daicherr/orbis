"""
Faction Repository - CRUD operations for Faction model
"""

from typing import Optional, List
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database.models.world_state import Faction


class FactionRepository:
    """Repository para operações CRUD de Faction."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        name: str,
        power_level: int = 100,
        resources: int = 1000,
        relations: dict = None
    ) -> Faction:
        """Cria uma nova facção."""
        
        faction = Faction(
            name=name,
            power_level=power_level,
            resources=resources,
            relations=relations or {}
        )
        
        self.session.add(faction)
        await self.session.commit()
        await self.session.refresh(faction)
        
        return faction
    
    async def get_by_id(self, faction_id: int) -> Optional[Faction]:
        """Busca facção por ID."""
        
        statement = select(Faction).where(Faction.id == faction_id)
        result = await self.session.exec(statement)
        return result.first()
    
    async def get_by_name(self, name: str) -> Optional[Faction]:
        """Busca facção por nome."""
        
        statement = select(Faction).where(Faction.name == name)
        result = await self.session.exec(statement)
        return result.first()
    
    async def get_all(self) -> List[Faction]:
        """Retorna todas as facções."""
        
        statement = select(Faction)
        results = await self.session.exec(statement)
        return list(results.all())
    
    async def update(self, faction: Faction) -> Faction:
        """Atualiza uma facção."""
        
        self.session.add(faction)
        await self.session.commit()
        await self.session.refresh(faction)
        
        return faction
    
    async def update_power(self, faction_id: int, new_power: int) -> Optional[Faction]:
        """Atualiza o nível de poder de uma facção."""
        
        faction = await self.get_by_id(faction_id)
        
        if faction:
            faction.power_level = new_power
            return await self.update(faction)
        
        return None
    
    async def update_resources(self, faction_id: int, amount: int) -> Optional[Faction]:
        """
        Adiciona ou remove recursos de uma facção.
        
        Args:
            faction_id: ID da facção
            amount: Quantidade (positivo para adicionar, negativo para remover)
        """
        
        faction = await self.get_by_id(faction_id)
        
        if faction:
            faction.resources = max(0, faction.resources + amount)
            return await self.update(faction)
        
        return None
    
    async def set_relation(
        self, 
        faction_id: int, 
        other_faction_name: str, 
        relation: str
    ) -> Optional[Faction]:
        """
        Define a relação entre duas facções.
        
        Args:
            faction_id: ID da facção principal
            other_faction_name: Nome da outra facção
            relation: "allied", "neutral", "hostile", "at_war"
        """
        
        faction = await self.get_by_id(faction_id)
        
        if faction:
            if faction.relations is None:
                faction.relations = {}
            
            faction.relations[other_faction_name] = relation
            return await self.update(faction)
        
        return None
    
    async def get_enemies(self, faction_name: str) -> List[str]:
        """Retorna lista de nomes de facções inimigas."""
        
        faction = await self.get_by_name(faction_name)
        
        if not faction or not faction.relations:
            return []
        
        enemies = []
        for other_name, relation in faction.relations.items():
            if relation in ("hostile", "at_war"):
                enemies.append(other_name)
        
        return enemies
    
    async def get_allies(self, faction_name: str) -> List[str]:
        """Retorna lista de nomes de facções aliadas."""
        
        faction = await self.get_by_name(faction_name)
        
        if not faction or not faction.relations:
            return []
        
        allies = []
        for other_name, relation in faction.relations.items():
            if relation == "allied":
                allies.append(other_name)
        
        return allies
    
    async def delete(self, faction_id: int) -> bool:
        """Remove uma facção."""
        
        faction = await self.get_by_id(faction_id)
        
        if faction:
            await self.session.delete(faction)
            await self.session.commit()
            return True
        
        return False
    
    async def initialize_default_factions(self) -> List[Faction]:
        """
        Inicializa as facções padrão do jogo.
        Chamado na primeira execução.
        """
        
        default_factions = [
            {
                "name": "Império Central",
                "power_level": 1000,
                "resources": 10000,
                "relations": {
                    "Seita Arcaica": "neutral",
                    "Lua Sombria": "hostile",
                    "Monastério da Aurora": "allied",
                    "Guilda de Piratas": "hostile",
                    "Clã Luo": "allied",
                    "Nômades do Deserto": "neutral"
                }
            },
            {
                "name": "Seita Arcaica",
                "power_level": 800,
                "resources": 5000,
                "relations": {
                    "Império Central": "neutral",
                    "Lua Sombria": "neutral",
                    "Monastério da Aurora": "neutral"
                }
            },
            {
                "name": "Lua Sombria",
                "power_level": 500,
                "resources": 3000,
                "relations": {
                    "Império Central": "hostile",
                    "Monastério da Aurora": "hostile",
                    "Guilda de Piratas": "allied"
                }
            },
            {
                "name": "Monastério da Aurora",
                "power_level": 600,
                "resources": 4000,
                "relations": {
                    "Império Central": "allied",
                    "Lua Sombria": "hostile",
                    "Seita Arcaica": "neutral"
                }
            },
            {
                "name": "Guilda de Piratas",
                "power_level": 400,
                "resources": 6000,
                "relations": {
                    "Império Central": "hostile",
                    "Lua Sombria": "allied",
                    "Nômades do Deserto": "neutral"
                }
            },
            {
                "name": "Clã Luo",
                "power_level": 350,
                "resources": 8000,
                "relations": {
                    "Império Central": "allied",
                    "Guilda de Piratas": "hostile"
                }
            },
            {
                "name": "Nômades do Deserto",
                "power_level": 200,
                "resources": 1500,
                "relations": {
                    "Império Central": "neutral",
                    "Guilda de Piratas": "neutral"
                }
            }
        ]
        
        created_factions = []
        
        for faction_data in default_factions:
            # Verificar se já existe
            existing = await self.get_by_name(faction_data["name"])
            
            if not existing:
                faction = await self.create(
                    name=faction_data["name"],
                    power_level=faction_data["power_level"],
                    resources=faction_data["resources"],
                    relations=faction_data["relations"]
                )
                created_factions.append(faction)
                print(f"[FACTION REPO] Created: {faction.name}")
        
        return created_factions
