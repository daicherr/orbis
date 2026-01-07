from typing import Dict, Any
from app.services.gemini_client import GeminiClient
from app.core.data_manager import data_manager

class Architect:
    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client
        self.items_path = "ruleset_source/mechanics/items.json"
        self.loot_tables_path = "ruleset_source/mechanics/loot_tables.json"
        self.bestiary_path = "lore_library/bestiary.json" # Novo bestiário para dados estruturados

    def _ensure_item_exists(self, item_name: str):
        """Verifica se um item existe e o cria se não existir."""
        all_items = data_manager._read_json_file(self.items_path)
        item_exists = any(item['name'] == item_name for item in all_items)

        if not item_exists:
            print(f"Item dinâmico '{item_name}' não encontrado. Criando...")
            new_item = {
                "id": item_name.lower().replace(" ", "_"),
                "name": item_name,
                "type": "material",
                "description": f"Um material raro dropado por uma criatura: {item_name}.",
                "value": 100 # Valor padrão alto para itens raros
            }
            data_manager.append_to_list_json(self.items_path, new_item)
            return new_item["id"]
        
        return next(item['id'] for item in all_items if item['name'] == item_name)


    def generate_enemy(self, tier: int, biome: str) -> Dict[str, Any]:
        """Gera um novo inimigo, seus drops e os persiste nos arquivos JSON."""
        
        prompt = (
            f"Você é um gerador de conteúdo para um RPG de Cultivo (Wuxia/Xianxia). "
            f"Crie um monstro que se encaixe no seguinte contexto:\n"
            f"- **Tier de Poder:** {tier} (Escala de 1 a 9, onde 1 é um animal aprimorado e 9 pode destruir montanhas).\n"
            f"- **Bioma:** {biome}.\n\n"
            f"Sua resposta DEVE ser um único objeto JSON estrito com as seguintes chaves:\n"
            f"- `name` (string): Nome evocativo do monstro (ex: 'Serpente da Névoa Fantasma').\n"
            f"- `description` (string): Descrição literária curta da aparência e aura do monstro.\n"
            f"- `stats` (object): Contendo `hp` (number), `defense` (number), e `rank` (number, igual ao tier).\n"
            f"- `drops` (array of objects): Uma lista de 1 a 3 itens que o monstro pode dropar. Cada objeto deve ter:\n"
            f"  - `itemName` (string): O nome do item (ex: 'Núcleo da Serpente Nebulosa').\n"
            f"  - `chance` (number): Probabilidade de drop (0.0 a 1.0).\n"
            f"  - `quantity_min` (number).\n"
            f"  - `quantity_max` (number).\n\n"
            f"JSON de Saída:"
        )

        print(f"--- Gerando inimigo para Tier {tier} no bioma {biome} via Gemini ---")
        enemy_data = self.gemini_client.generate_json(prompt)
        if "error" in enemy_data:
            return enemy_data # Retorna o erro se a geração falhar

        # Gerenciamento de Loot Dinâmico
        processed_drops = []
        for drop in enemy_data.get("drops", []):
            item_id = self._ensure_item_exists(drop["itemName"])
            processed_drops.append({
                "item_id": item_id,
                "chance": drop["chance"],
                "quantity_min": drop["quantity_min"],
                "quantity_max": drop["quantity_max"]
            })
        
        # Persistência
        monster_id = enemy_data["name"].lower().replace(" ", "_")
        
        # 1. Adicionar à loot_table
        loot_table_entry = {monster_id: {"name": enemy_data["name"], "drops": processed_drops}}
        data_manager.update_dict_json(self.loot_tables_path, "monsters", loot_table_entry)

        # 2. Adicionar ao bestiário
        bestiary_entry = {
            "id": monster_id,
            "name": enemy_data["name"],
            "description": enemy_data["description"],
            "stats": enemy_data["stats"]
        }
        data_manager.append_to_list_json(self.bestiary_path, bestiary_entry)
        
        print(f"Inimigo '{enemy_data['name']}' e seus itens foram criados e salvos.")
        return bestiary_entry
