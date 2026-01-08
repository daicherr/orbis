"""
Loot Manager
Gera drops baseados em loot_tables.json (Sprint 5 - Integração com Lore)
"""

import json
import os
import random
from typing import Dict, Any, List
from pathlib import Path

class LootManager:
    """
    Sistema de loot que lê loot_tables.json e gera drops baseados em probabilidades.
    Baseado no sistema de drop do GDD (cores, sangue, pele, ossos).
    [SPRINT 5] Atualizado para usar estrutura completa do loot_tables.json
    """
    
    def __init__(self, loot_tables_path: str = "./ruleset_source/mechanics/loot_tables.json"):
        self.loot_tables = self._load_loot_tables(loot_tables_path)

    def _load_loot_tables(self, file_path: str) -> Dict[str, Any]:
        """Carrega as tabelas de loot do arquivo JSON."""
        loot_path = Path(file_path)
        
        if not loot_path.exists():
            print(f"WARNING: loot_tables.json não encontrado em {file_path}. Usando tabela vazia.")
            return {"monsters": {}, "exploration": {}, "bosses": {}}
        
        try:
            with open(loot_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Validar estrutura (backward compatibility)
                if "monsters" not in data:
                    print("WARNING: loot_tables.json está no formato antigo. Usando com fallback.")
                    return {"monsters": data, "exploration": {}, "bosses": {}}
                
                return data
        except Exception as e:
            print(f"ERROR ao carregar loot_tables.json: {e}")
            return {"monsters": {}, "exploration": {}, "bosses": {}}
    
    def calculate_loot(self, monster_id: str, player_luck: float = 1.0) -> List[Dict[str, Any]]:
        """
        Calcula o loot dropado por um monstro com base em sua tabela.
        [SPRINT 5] Agora suporta guaranteed/rare/legendary + fallback genérico.
        
        Args:
            monster_id: ID do monstro (ex: "iron_hide_boar")
            player_luck: Multiplicador de sorte (1.0 = normal, 1.5 = +50% chance)
        
        Returns:
            Lista de itens dropados [{item_id, quantity, rarity}]
        """
        
        # Normalizar nome (lowercase, underscore)
        normalized_id = monster_id.lower().replace("-", "_").replace(" ", "_")
        
        # Tentar buscar na tabela nova (monsters -> monster_id)
        monster_loot_table = self.loot_tables.get("monsters", {}).get(normalized_id)
        
        if not monster_loot_table:
            print(f"WARNING: Loot table para '{monster_id}' não encontrada. Gerando loot genérico.")
            return self._generate_generic_loot(monster_id)
        
        dropped_loot = []
        
        # 1. Guaranteed Drops (100% chance)
        if "guaranteed" in monster_loot_table:
            for item in monster_loot_table["guaranteed"]:
                dropped_loot.append({
                    "item_id": item["item_id"],
                    "quantity": item.get("quantity", 1),
                    "rarity": "guaranteed"
                })
        
        # 2. Rare Drops (chance-based)
        if "rare" in monster_loot_table:
            for item in monster_loot_table["rare"]:
                base_chance = item.get("chance", 0.5)
                effective_chance = base_chance * player_luck
                
                if random.random() < effective_chance:
                    dropped_loot.append({
                        "item_id": item["item_id"],
                        "quantity": item.get("quantity", 1),
                        "rarity": "rare"
                    })
        
        # 3. Legendary Drops (very low chance)
        if "legendary" in monster_loot_table:
            for item in monster_loot_table["legendary"]:
                base_chance = item.get("chance", 0.1)
                effective_chance = base_chance * player_luck
                
                if random.random() < effective_chance:
                    dropped_loot.append({
                        "item_id": item["item_id"],
                        "quantity": item.get("quantity", 1),
                        "rarity": "legendary"
                    })
        
        # [BACKWARD COMPATIBILITY] Formato antigo com "drops"
        if "drops" in monster_loot_table and not dropped_loot:
            for item_info in monster_loot_table["drops"]:
                if random.random() < item_info.get("chance", 0.5) * player_luck:
                    quantity = random.randint(
                        item_info.get("quantity_min", 1), 
                        item_info.get("quantity_max", 1)
                    )
                    dropped_loot.append({
                        "item_id": item_info["item_id"], 
                        "quantity": quantity,
                        "rarity": "rare"
                    })
        
        print(f"Loot calculado para {monster_id}: {dropped_loot}")
        return dropped_loot
    
    def _generate_generic_loot(self, monster_name: str) -> List[Dict[str, Any]]:
        """
        Gera loot genérico quando a tabela não existe.
        Baseado nas regras do GDD (cores 100%, sangue 50%, pele 80%, ossos 60%).
        """
        drops = []
        
        # Core (sempre dropa)
        drops.append({
            "item_id": f"{monster_name.lower().replace(' ', '_')}_core",
            "quantity": 1,
            "rarity": "guaranteed"
        })
        
        # Sangue (50% chance)
        if random.random() < 0.5:
            drops.append({
                "item_id": f"{monster_name.lower().replace(' ', '_')}_blood",
                "quantity": random.randint(1, 3),
                "rarity": "rare"
            })
        
        # Pele (80% chance)
        if random.random() < 0.8:
            drops.append({
                "item_id": f"{monster_name.lower().replace(' ', '_')}_hide",
                "quantity": 1,
                "rarity": "rare"
            })
        
        # Ossos (60% chance)
        if random.random() < 0.6:
            drops.append({
                "item_id": f"{monster_name.lower().replace(' ', '_')}_bones",
                "quantity": random.randint(1, 2),
                "rarity": "rare"
            })
        
        return drops
    
    def format_loot_message(self, drops: List[Dict[str, Any]]) -> str:
        """
        Formata a mensagem de loot para exibir ao jogador.
        
        Returns:
            String literária dos drops (ex: "Você encontrou: [Core de Javali] (Garantido), [Sangue de Javali x2] (Raro)")
        """
        
        if not drops:
            return "Nada de valor foi encontrado nos restos."
        
        rarity_emoji = {
            "guaranteed": "⚪",
            "rare": "🔵",
            "legendary": "🟡"
        }
        
        items_str = []
        for drop in drops:
            emoji = rarity_emoji.get(drop.get("rarity", "rare"), "⚪")
            quantity = drop.get("quantity", 1)
            item_name = drop["item_id"].replace("_", " ").title()
            
            if quantity > 1:
                items_str.append(f"{emoji} {item_name} x{quantity}")
            else:
                items_str.append(f"{emoji} {item_name}")
        
        return "🎁 Você encontrou:\n" + "\n".join(items_str)

loot_manager = LootManager(loot_tables_path="ruleset_source/mechanics/loot_tables.json")
