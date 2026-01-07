import json
import os
import random
from typing import Dict, Any, List

class LootManager:
    def __init__(self, loot_tables_path: str):
        self.loot_tables = self._load_loot_tables(loot_tables_path)

    def _load_loot_tables(self, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            return {}
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def calculate_loot(self, monster_id: str) -> List[Dict[str, Any]]:
        """Calcula o loot dropado por um monstro com base em sua tabela."""
        monster_loot_table = self.loot_tables.get("monsters", {}).get(monster_id)
        if not monster_loot_table:
            return []

        dropped_loot = []
        for item_info in monster_loot_table["drops"]:
            if random.random() < item_info["chance"]:
                quantity = random.randint(item_info["quantity_min"], item_info["quantity_max"])
                dropped_loot.append({"item_id": item_info["item_id"], "quantity": quantity})
        
        print(f"Loot calculado para {monster_id}: {dropped_loot}")
        return dropped_loot

loot_manager = LootManager(loot_tables_path="ruleset_source/mechanics/loot_tables.json")
