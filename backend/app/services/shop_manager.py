"""
Shop Manager & Economy System
Gerencia preços dinâmicos baseados em initial_economy.json (Sprint 5)
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path

class ShopManager:
    """
    Sistema de economia que lê initial_economy.json e calcula preços dinâmicos.
    Implementa:
    - Conversão de moedas (Gold Tael ↔ Spirit Stones)
    - Preços base por categoria (pílulas, materiais, serviços)
    - Modificadores por localização (guerra, monopólio de seita, mercado negro)
    """
    
    def __init__(self, economy_path: str = "./lore_library/initial_economy.json"):
        self.economy_data = self._load_economy_data(economy_path)
        self.currency_system = self.economy_data.get("currency_system", {})
        self.resource_matrix = self.economy_data.get("resource_value_matrix", {})
        self.location_modifiers = self.economy_data.get("economic_modifiers", {})
    
    def _load_economy_data(self, path: str) -> Dict[str, Any]:
        """Carrega os dados da economia do arquivo JSON."""
        economy_path = Path(path)
        
        if not economy_path.exists():
            print(f"WARNING: initial_economy.json não encontrado em {path}. Usando economia padrão.")
            return self._get_default_economy()
        
        try:
            with open(economy_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"ERROR ao carregar initial_economy.json: {e}")
            return self._get_default_economy()
    
    def _get_default_economy(self) -> Dict[str, Any]:
        """Economia padrão caso o arquivo não exista."""
        return {
            "currency_system": {
                "gold_tael": {"value": 1, "symbol": "🪙"},
                "spirit_stones": {"value": 1000, "symbol": "💎"}
            },
            "resource_value_matrix": {
                "pills": {"min": 50, "max": 500},
                "materials": {"min": 300, "max": 50000},
                "services": {"min": 50, "max": 10000}
            },
            "economic_modifiers": {
                "war_tax": 1.5,
                "sect_monopoly": 2.0,
                "black_market_markup": 1.3
            }
        }
    
    def convert_gold_to_spirit_stones(self, gold_amount: float) -> float:
        """
        Converte Gold Tael para Spirit Stones.
        1 Spirit Stone = 1000 Gold Tael (padrão do GDD)
        """
        conversion_rate = self.currency_system.get("spirit_stones", {}).get("value", 1000)
        return gold_amount / conversion_rate
    
    def convert_spirit_stones_to_gold(self, spirit_stones: float) -> float:
        """
        Converte Spirit Stones para Gold Tael.
        1 Spirit Stone = 1000 Gold Tael (padrão do GDD)
        """
        conversion_rate = self.currency_system.get("spirit_stones", {}).get("value", 1000)
        return spirit_stones * conversion_rate
    
    def get_base_price(self, item_category: str, item_tier: int = 1) -> float:
        """
        Retorna o preço base de um item baseado em sua categoria e tier.
        
        Args:
            item_category: "pills", "materials", "services", "weapons", etc.
            item_tier: Tier de cultivação do item (1-9)
        
        Returns:
            Preço em Gold Tael
        """
        
        # Buscar faixa de preço na matriz
        category_data = self.resource_matrix.get(item_category, {})
        min_price = category_data.get("min", 100)
        max_price = category_data.get("max", 1000)
        
        # Escalar preço por tier (exponencial)
        # Tier 1 = min_price, Tier 9 = max_price
        tier_multiplier = (item_tier - 1) / 8  # 0.0 a 1.0
        base_price = min_price + (max_price - min_price) * (tier_multiplier ** 2)  # Curva quadrática
        
        return round(base_price, 2)
    
    def get_price(
        self, 
        item_id: str, 
        item_category: str, 
        item_tier: int, 
        location: str = "neutral",
        modifiers: list[str] = None
    ) -> Dict[str, Any]:
        """
        Calcula o preço final de um item considerando localização e modificadores.
        
        Args:
            item_id: ID do item (ex: "qi_condensation_pill")
            item_category: Categoria ("pills", "materials", etc.)
            item_tier: Tier do item (1-9)
            location: Local da compra ("Vila Crisântemos", "Cidade Imperial", etc.)
            modifiers: Lista de modificadores ativos (["war_tax", "sect_monopoly"])
        
        Returns:
            {
                "item_id": str,
                "base_price": float,
                "final_price": float,
                "currency": "gold_tael",
                "modifiers_applied": list
            }
        """
        
        base_price = self.get_base_price(item_category, item_tier)
        final_price = base_price
        applied_modifiers = []
        
        # Aplicar modificadores econômicos
        if modifiers:
            for mod_name in modifiers:
                modifier_value = self.location_modifiers.get(mod_name, 1.0)
                final_price *= modifier_value
                applied_modifiers.append({
                    "name": mod_name,
                    "multiplier": modifier_value
                })
        
        # Modificadores por localização (hardcoded baseado no lore)
        location_multipliers = {
            "Vila Crisântemos": 0.9,  # Barato (vila pequena)
            "Cidade Imperial": 1.2,     # Caro (capital)
            "Templo Abismo": 1.5,       # Muito caro (seita isolada)
            "Cidade Subterrânea": 1.3,  # Black market markup
            "Montanha Arcaica": 2.0     # Extremamente caro (seita poderosa)
        }
        
        location_mult = location_multipliers.get(location, 1.0)
        if location_mult != 1.0:
            final_price *= location_mult
            applied_modifiers.append({
                "name": f"location_{location}",
                "multiplier": location_mult
            })
        
        return {
            "item_id": item_id,
            "base_price": round(base_price, 2),
            "final_price": round(final_price, 2),
            "currency": "gold_tael",
            "spirit_stones_equivalent": round(self.convert_gold_to_spirit_stones(final_price), 4),
            "modifiers_applied": applied_modifiers
        }
    
    def calculate_sell_price(self, buy_price: float, condition: float = 1.0) -> float:
        """
        Calcula o preço de venda de um item.
        
        Args:
            buy_price: Preço de compra original
            condition: Condição do item (0.0 a 1.0, onde 1.0 = perfeito)
        
        Returns:
            Preço de venda em Gold Tael (70% do valor original * condição)
        """
        
        sell_multiplier = 0.7  # Lojistas compram por 70% do valor
        return round(buy_price * sell_multiplier * condition, 2)
    
    def can_afford(self, player_gold: float, item_price: float) -> bool:
        """Verifica se o jogador pode comprar um item."""
        return player_gold >= item_price
    
    def format_price(self, price: float) -> str:
        """
        Formata o preço para exibição.
        
        Returns:
            String formatada (ex: "1,500 🪙 Gold Tael (1.5 💎 Spirit Stones)")
        """
        
        gold_symbol = self.currency_system.get("gold_tael", {}).get("symbol", "🪙")
        spirit_symbol = self.currency_system.get("spirit_stones", {}).get("symbol", "💎")
        
        spirit_stones = self.convert_gold_to_spirit_stones(price)
        
        # Exibir em Gold se < 1 Spirit Stone, senão exibir ambos
        if spirit_stones < 1.0:
            return f"{price:,.0f} {gold_symbol} Gold Tael"
        else:
            return f"{price:,.0f} {gold_symbol} Gold Tael ({spirit_stones:.2f} {spirit_symbol} Spirit Stones)"


# Instância global (Singleton)
shop_manager = ShopManager()
