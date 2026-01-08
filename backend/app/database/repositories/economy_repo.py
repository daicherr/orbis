"""
GlobalEconomy Repository - CRUD operations for GlobalEconomy model
Manages dynamic economy: prices, supply, demand
"""

from typing import Optional, List
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database.models.world_state import GlobalEconomy


class GlobalEconomyRepository:
    """Repository para operações CRUD de GlobalEconomy."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        resource_name: str,
        base_price: float,
        current_price: float = None,
        supply: int = 100,
        demand: int = 100
    ) -> GlobalEconomy:
        """Cria um novo item de economia."""
        
        item = GlobalEconomy(
            resource_name=resource_name,
            base_price=base_price,
            current_price=current_price or base_price,
            supply=supply,
            demand=demand
        )
        
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        
        return item
    
    async def get_by_id(self, item_id: int) -> Optional[GlobalEconomy]:
        """Busca item por ID."""
        
        statement = select(GlobalEconomy).where(GlobalEconomy.id == item_id)
        result = await self.session.exec(statement)
        return result.first()
    
    async def get_by_name(self, resource_name: str) -> Optional[GlobalEconomy]:
        """Busca item por nome do recurso."""
        
        statement = select(GlobalEconomy).where(
            GlobalEconomy.resource_name == resource_name
        )
        result = await self.session.exec(statement)
        return result.first()
    
    async def get_all(self) -> List[GlobalEconomy]:
        """Retorna todos os itens da economia."""
        
        statement = select(GlobalEconomy)
        results = await self.session.exec(statement)
        return list(results.all())
    
    async def update(self, item: GlobalEconomy) -> GlobalEconomy:
        """Atualiza um item da economia."""
        
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        
        return item
    
    async def update_price(
        self, 
        resource_name: str, 
        new_price: float
    ) -> Optional[GlobalEconomy]:
        """Atualiza o preço atual de um recurso."""
        
        item = await self.get_by_name(resource_name)
        
        if item:
            item.current_price = new_price
            return await self.update(item)
        
        return None
    
    async def adjust_price_by_percentage(
        self, 
        resource_name: str, 
        percentage: float
    ) -> Optional[GlobalEconomy]:
        """
        Ajusta o preço por porcentagem.
        
        Args:
            resource_name: Nome do recurso
            percentage: Porcentagem (ex: 0.1 = +10%, -0.2 = -20%)
        """
        
        item = await self.get_by_name(resource_name)
        
        if item:
            item.current_price = item.current_price * (1 + percentage)
            # Mínimo 10% do preço base
            item.current_price = max(item.current_price, item.base_price * 0.1)
            # Máximo 500% do preço base
            item.current_price = min(item.current_price, item.base_price * 5)
            return await self.update(item)
        
        return None
    
    async def update_supply(
        self, 
        resource_name: str, 
        amount: int
    ) -> Optional[GlobalEconomy]:
        """
        Atualiza a oferta de um recurso.
        
        Args:
            resource_name: Nome do recurso
            amount: Quantidade (positivo = mais oferta, negativo = menos)
        """
        
        item = await self.get_by_name(resource_name)
        
        if item:
            item.supply = max(0, item.supply + amount)
            # Recalcular preço baseado em oferta/demanda
            await self._recalculate_price(item)
            return await self.update(item)
        
        return None
    
    async def update_demand(
        self, 
        resource_name: str, 
        amount: int
    ) -> Optional[GlobalEconomy]:
        """
        Atualiza a demanda de um recurso.
        
        Args:
            resource_name: Nome do recurso
            amount: Quantidade (positivo = mais demanda, negativo = menos)
        """
        
        item = await self.get_by_name(resource_name)
        
        if item:
            item.demand = max(0, item.demand + amount)
            # Recalcular preço baseado em oferta/demanda
            await self._recalculate_price(item)
            return await self.update(item)
        
        return None
    
    async def _recalculate_price(self, item: GlobalEconomy):
        """
        Recalcula o preço baseado em oferta e demanda.
        
        Fórmula: preço = preço_base * (demanda / oferta)
        Com limites de 10% a 500% do preço base.
        """
        
        if item.supply <= 0:
            # Sem oferta = preço máximo
            item.current_price = item.base_price * 5
        else:
            ratio = item.demand / item.supply
            item.current_price = item.base_price * ratio
            
            # Aplicar limites
            item.current_price = max(item.current_price, item.base_price * 0.1)
            item.current_price = min(item.current_price, item.base_price * 5)
    
    async def delete(self, item_id: int) -> bool:
        """Remove um item da economia."""
        
        item = await self.get_by_id(item_id)
        
        if item:
            await self.session.delete(item)
            await self.session.commit()
            return True
        
        return False
    
    async def get_price_multiplier(self, resource_name: str) -> float:
        """
        Retorna o multiplicador de preço atual vs base.
        Útil para aplicar em transações.
        """
        
        item = await self.get_by_name(resource_name)
        
        if item and item.base_price > 0:
            return item.current_price / item.base_price
        
        return 1.0
    
    async def simulate_market_tick(self):
        """
        Simula um tick do mercado.
        Preços tendem a voltar ao normal lentamente.
        """
        
        all_items = await self.get_all()
        
        for item in all_items:
            # Preço tende ao base_price (5% por tick)
            diff = item.base_price - item.current_price
            adjustment = diff * 0.05
            item.current_price += adjustment
            
            # Oferta tende a 100 (regeneração)
            if item.supply < 100:
                item.supply = min(100, item.supply + 5)
            
            await self.update(item)
    
    async def initialize_default_economy(self) -> List[GlobalEconomy]:
        """
        Inicializa a economia padrão do jogo.
        Chamado na primeira execução.
        """
        
        default_items = [
            # Comida e Consumíveis
            {"resource_name": "Arroz", "base_price": 5, "supply": 200, "demand": 150},
            {"resource_name": "Carne de Besta", "base_price": 20, "supply": 100, "demand": 120},
            {"resource_name": "Pílula de Qi Básica", "base_price": 50, "supply": 80, "demand": 100},
            {"resource_name": "Pílula de Recuperação", "base_price": 100, "supply": 50, "demand": 80},
            {"resource_name": "Pílula de Cultivo", "base_price": 500, "supply": 20, "demand": 50},
            
            # Materiais
            {"resource_name": "Ferro Comum", "base_price": 10, "supply": 150, "demand": 100},
            {"resource_name": "Ferro Celestial", "base_price": 200, "supply": 30, "demand": 60},
            {"resource_name": "Cristal de Yuan Qi", "base_price": 300, "supply": 40, "demand": 70},
            {"resource_name": "Pedra Espiritual", "base_price": 100, "supply": 100, "demand": 100},
            
            # Ervas
            {"resource_name": "Moongrass", "base_price": 15, "supply": 80, "demand": 90},
            {"resource_name": "Shadowleaf", "base_price": 25, "supply": 60, "demand": 80},
            {"resource_name": "Raiz de Sangue", "base_price": 80, "supply": 40, "demand": 60},
            {"resource_name": "Flor do Lótus", "base_price": 150, "supply": 20, "demand": 40},
            
            # Equipamentos (preços base para cálculo)
            {"resource_name": "Espada Comum", "base_price": 100, "supply": 50, "demand": 40},
            {"resource_name": "Armadura de Couro", "base_price": 150, "supply": 40, "demand": 35},
            {"resource_name": "Arma Espiritual", "base_price": 1000, "supply": 10, "demand": 30},
            
            # Raros
            {"resource_name": "Núcleo de Besta", "base_price": 500, "supply": 15, "demand": 40},
            {"resource_name": "Pergaminho de Técnica", "base_price": 800, "supply": 10, "demand": 25},
            {"resource_name": "Artefato Antigo", "base_price": 2000, "supply": 5, "demand": 15},
        ]
        
        created_items = []
        
        for item_data in default_items:
            # Verificar se já existe
            existing = await self.get_by_name(item_data["resource_name"])
            
            if not existing:
                item = await self.create(
                    resource_name=item_data["resource_name"],
                    base_price=item_data["base_price"],
                    supply=item_data["supply"],
                    demand=item_data["demand"]
                )
                created_items.append(item)
                print(f"[ECONOMY REPO] Created: {item.resource_name} @ {item.base_price} gold")
        
        return created_items

    async def apply_event_effects(self, event_type: str, location: str = None):
        """
        Aplica efeitos de eventos mundiais na economia.
        
        Args:
            event_type: Tipo do evento
            location: Localização afetada (opcional)
        """
        
        effects = {
            "village_destroyed": {
                "Arroz": 0.5,  # +50% no preço
                "Carne de Besta": 0.3,
            },
            "mine_collapsed": {
                "Ferro Comum": 0.4,
                "Ferro Celestial": 0.6,
                "Cristal de Yuan Qi": 0.3,
            },
            "monster_horde": {
                "Carne de Besta": -0.2,  # -20% (mais disponível)
                "Núcleo de Besta": -0.3,
            },
            "faction_war": {
                "Espada Comum": 0.3,
                "Armadura de Couro": 0.25,
                "Arma Espiritual": 0.4,
                "Pílula de Recuperação": 0.5,
            },
            "good_harvest": {
                "Arroz": -0.3,
                "Moongrass": -0.2,
                "Shadowleaf": -0.2,
            },
            "trade_route_opened": {
                "Artefato Antigo": -0.2,
                "Pergaminho de Técnica": -0.15,
            }
        }
        
        event_effects = effects.get(event_type, {})
        
        for resource_name, percentage in event_effects.items():
            await self.adjust_price_by_percentage(resource_name, percentage)
            print(f"[ECONOMY] {resource_name} price adjusted by {percentage*100:+.0f}% due to {event_type}")
