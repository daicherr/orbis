"""
Economy Simulator - Dynamic economy based on world events
Prices fluctuate based on supply/demand and world events
"""

from typing import List, Dict, Any, Optional
import random


class EconomySimulator:
    """
    Simula economia dinâmica do mundo.
    Preços sobem/descem baseado em eventos, oferta e demanda.
    """
    
    def __init__(self, economy_repo=None, world_event_repo=None):
        """
        Inicializa o simulador de economia.
        
        Args:
            economy_repo: GlobalEconomyRepository
            world_event_repo: WorldEventRepository
        """
        self.economy_repo = economy_repo
        self.world_event_repo = world_event_repo
        
        # Cache local para operações sem banco
        self.price_cache: Dict[str, float] = {}
        self.supply_cache: Dict[str, int] = {}
        self.demand_cache: Dict[str, int] = {}

    async def simulate_economy_tick(self, current_turn: int) -> List[Dict[str, Any]]:
        """
        Executa uma rodada de simulação econômica.
        Chamado pelo DailyTickSimulator.
        
        Returns:
            Lista de eventos econômicos gerados
        """
        events = []
        
        # 1. Processar eventos mundiais recentes
        world_events = await self._get_recent_events(current_turn)
        for event in world_events:
            econ_events = await self._process_world_event(event, current_turn)
            events.extend(econ_events)
        
        # 2. Simular flutuações naturais de mercado
        market_events = await self._simulate_market_fluctuations(current_turn)
        events.extend(market_events)
        
        # 3. Regenerar oferta (recursos renováveis)
        await self._regenerate_supply()
        
        # 4. Normalizar preços (tendem ao base)
        await self._normalize_prices()
        
        return events

    async def _get_recent_events(self, current_turn: int) -> List[Dict[str, Any]]:
        """Busca eventos mundiais que afetam economia."""
        
        if not self.world_event_repo:
            return []
        
        # Buscar eventos dos últimos 5 turnos
        events = await self.world_event_repo.get_recent_events(
            since_turn=current_turn - 5
        )
        
        return [
            {
                "type": e.event_type,
                "location": e.location_affected,
                "effects": e.effects,
                "turn": e.turn_occurred
            }
            for e in events
        ]

    async def _process_world_event(
        self, 
        event: Dict[str, Any],
        current_turn: int
    ) -> List[Dict[str, Any]]:
        """
        Processa um evento mundial e ajusta economia.
        
        Tipos de evento e seus efeitos:
        - destruction: +50% preço de comida e materiais de construção
        - npc_death: Se era comerciante, +20% preço de seus produtos
        - faction_war: +30% preço de armas e pílulas
        - calamity: +100% preço de tudo na região
        - monster_horde: -20% preço de drops de monstro (mais disponível)
        """
        
        effects = []
        event_type = event.get("type", "generic")
        location = event.get("location")
        
        # Mapear tipos de evento para efeitos econômicos
        economic_effects = self._get_economic_effects(event_type)
        
        for resource_name, percentage in economic_effects.items():
            if self.economy_repo:
                await self.economy_repo.adjust_price_by_percentage(
                    resource_name, 
                    percentage
                )
            
            effects.append({
                "type": "price_change",
                "resource": resource_name,
                "change": percentage,
                "reason": event_type,
                "location": location,
                "turn": current_turn
            })
            
            print(f"[ECONOMY] {resource_name}: {percentage*100:+.0f}% due to {event_type}")
        
        return effects

    def _get_economic_effects(self, event_type: str) -> Dict[str, float]:
        """Retorna os efeitos econômicos de cada tipo de evento."""
        
        effects_map = {
            "destruction": {
                "Arroz": 0.5,
                "Carne de Besta": 0.3,
                "Ferro Comum": 0.4,
                "Pedra Espiritual": 0.2,
            },
            "village_destroyed": {
                "Arroz": 0.6,
                "Carne de Besta": 0.4,
                "Pílula de Recuperação": 0.3,
            },
            "npc_death": {
                # Efeito menor, depende do NPC
                "Pergaminho de Técnica": 0.1,
            },
            "faction_war": {
                "Espada Comum": 0.3,
                "Armadura de Couro": 0.25,
                "Arma Espiritual": 0.4,
                "Pílula de Recuperação": 0.5,
                "Pílula de Qi Básica": 0.3,
            },
            "calamity": {
                "Arroz": 1.0,  # Dobra o preço
                "Pílula de Recuperação": 0.8,
                "Pedra Espiritual": 0.5,
            },
            "monster_horde": {
                "Carne de Besta": -0.3,  # Mais disponível
                "Núcleo de Besta": -0.25,
            },
            "mine_collapsed": {
                "Ferro Comum": 0.5,
                "Ferro Celestial": 0.8,
                "Cristal de Yuan Qi": 0.6,
            },
            "trade_route_blocked": {
                "Artefato Antigo": 0.4,
                "Pergaminho de Técnica": 0.3,
            },
            "good_harvest": {
                "Arroz": -0.3,
                "Moongrass": -0.25,
                "Shadowleaf": -0.2,
                "Flor do Lótus": -0.15,
            },
            "festival": {
                # Preços caem durante festivais
                "Arroz": -0.2,
                "Carne de Besta": -0.15,
                "Pílula de Qi Básica": -0.1,
            }
        }
        
        return effects_map.get(event_type, {})

    async def _simulate_market_fluctuations(
        self, 
        current_turn: int
    ) -> List[Dict[str, Any]]:
        """
        Simula flutuações aleatórias de mercado.
        5% de chance de evento de mercado por recurso.
        """
        
        events = []
        
        if not self.economy_repo:
            return events
        
        try:
            all_items = await self.economy_repo.get_all()
            
            for item in all_items:
                # 5% de chance de flutuação significativa
                if random.random() < 0.05:
                    # Flutuação entre -20% e +20%
                    fluctuation = random.uniform(-0.2, 0.2)
                    
                    try:
                        await self.economy_repo.adjust_price_by_percentage(
                            item.resource_name,
                            fluctuation
                        )
                        
                        if abs(fluctuation) > 0.1:
                            direction = "subiu" if fluctuation > 0 else "caiu"
                            events.append({
                                "type": "market_fluctuation",
                                "resource": item.resource_name,
                                "change": fluctuation,
                                "turn": current_turn
                            })
                            print(f"[MARKET] {item.resource_name} {direction} {abs(fluctuation)*100:.0f}%")
                    except Exception as e:
                        pass  # Ignorar erros de update individual
        except Exception as e:
            print(f"[ECONOMY] Erro ao buscar itens: {e}")
        
        return events
        
        return events

    async def _regenerate_supply(self):
        """
        Regenera oferta de recursos renováveis.
        Recursos naturais regeneram 5% por turno até máximo 100.
        """
        
        if not self.economy_repo:
            return
        
        renewable_resources = [
            "Arroz", "Moongrass", "Shadowleaf", "Carne de Besta",
            "Raiz de Sangue", "Flor do Lótus"
        ]
        
        for resource_name in renewable_resources:
            try:
                item = await self.economy_repo.get_by_name(resource_name)
                
                if item and item.supply < 100:
                    regeneration = max(1, int(item.supply * 0.05))
                    item.supply = min(100, item.supply + regeneration)
                    await self.economy_repo.update(item)
            except Exception as e:
                pass  # Ignorar erros de update individual

    async def _normalize_prices(self):
        """
        Preços tendem a voltar ao normal lentamente.
        3% de aproximação ao preço base por turno.
        
        NOTA: Desabilitado temporariamente por problema de sessão async.
        TODO: Implementar com batch update ou SQL direto.
        """
        
        # Por enquanto, não fazer nada aqui para evitar erros de sessão
        # A normalização será feita quando o jogador interagir com a loja
        pass

    # === MÉTODOS PÚBLICOS ===
    
    async def get_current_price(self, resource_name: str) -> float:
        """Retorna o preço atual de um recurso."""
        
        if self.economy_repo:
            item = await self.economy_repo.get_by_name(resource_name)
            if item:
                return item.current_price
        
        return self.price_cache.get(resource_name, 100)
    
    async def get_price_multiplier(self, resource_name: str) -> float:
        """
        Retorna o multiplicador de preço (atual/base).
        Útil para aplicar em transações.
        """
        
        if self.economy_repo:
            return await self.economy_repo.get_price_multiplier(resource_name)
        
        return 1.0
    
    async def player_bought(self, resource_name: str, quantity: int):
        """
        Registra compra do jogador.
        Aumenta demanda, pode aumentar preço.
        """
        
        if self.economy_repo:
            # Aumentar demanda
            await self.economy_repo.update_demand(resource_name, quantity)
            # Diminuir oferta
            await self.economy_repo.update_supply(resource_name, -quantity)
    
    async def player_sold(self, resource_name: str, quantity: int):
        """
        Registra venda do jogador.
        Aumenta oferta, pode diminuir preço.
        """
        
        if self.economy_repo:
            # Aumentar oferta
            await self.economy_repo.update_supply(resource_name, quantity)
    
    async def get_market_report(self) -> Dict[str, Any]:
        """
        Gera relatório de mercado para o jogador.
        Mostra preços atuais vs base e tendências.
        """
        
        report = {
            "trending_up": [],
            "trending_down": [],
            "stable": [],
            "prices": {}
        }
        
        if not self.economy_repo:
            return report
        
        all_items = await self.economy_repo.get_all()
        
        for item in all_items:
            multiplier = item.current_price / item.base_price if item.base_price > 0 else 1
            
            report["prices"][item.resource_name] = {
                "current": item.current_price,
                "base": item.base_price,
                "multiplier": round(multiplier, 2),
                "supply": item.supply,
                "demand": item.demand
            }
            
            if multiplier > 1.2:
                report["trending_up"].append(item.resource_name)
            elif multiplier < 0.8:
                report["trending_down"].append(item.resource_name)
            else:
                report["stable"].append(item.resource_name)
        
        return report

    async def apply_regional_modifier(
        self, 
        location: str, 
        resource_name: str, 
        base_price: float
    ) -> float:
        """
        Aplica modificador regional ao preço.
        Alguns locais têm recursos mais baratos/caros.
        """
        
        regional_modifiers = {
            "Vila Crisântemos": {
                "Arroz": 0.8,  # -20% (produzem)
                "Arma Espiritual": 1.3,  # +30% (difícil conseguir)
            },
            "Cidade Imperial": {
                "Arroz": 1.1,  # +10% (importado)
                "Arma Espiritual": 0.9,  # -10% (abundante)
            },
            "Montanha das Cem Ervas": {
                "Moongrass": 0.6,
                "Shadowleaf": 0.6,
                "Flor do Lótus": 0.7,
            },
            "Cavernas Cristalinas": {
                "Cristal de Yuan Qi": 0.7,
                "Ferro Celestial": 0.75,
            },
            "Porto Sul": {
                "Artefato Antigo": 0.85,  # Contrabando
            }
        }
        
        location_mods = regional_modifiers.get(location, {})
        modifier = location_mods.get(resource_name, 1.0)
        
        # Também aplicar multiplicador global
        global_multiplier = await self.get_price_multiplier(resource_name)
        
        return base_price * modifier * global_multiplier

