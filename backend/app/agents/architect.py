from typing import Dict, Any
from pathlib import Path
from app.services.gemini_client import GeminiClient
from app.core.data_manager import data_manager

class Architect:
    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client
        repo_root = Path(__file__).resolve().parents[3]
        self.items_path = str((repo_root / "ruleset_source/mechanics/items.json").resolve())
        self.loot_tables_path = str((repo_root / "ruleset_source/mechanics/loot_tables.json").resolve())
        self.bestiary_path = str((repo_root / "lore_library/bestiary.json").resolve())  # Novo bestiário para dados estruturados

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
        enemy_data = self.gemini_client.generate_json(prompt, task="story")
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
    
    def generate_friendly_npc(self, location: str, role: str = "merchant") -> Dict[str, Any]:
        """
        Gera um NPC amigável (merchant, quest_giver, elder, healer, etc)
        Role: merchant, quest_giver, elder, healer, trainer, informant
        """
        prompt = (
            f"Você é um gerador de NPCs para um RPG de Cultivo Wuxia/Xianxia.\n"
            f"Crie um NPC AMIGÁVEL com as seguintes características:\n"
            f"- **Localização:** {location}\n"
            f"- **Papel/Profissão:** {role}\n\n"
            f"Responda APENAS com um objeto JSON com estas chaves:\n"
            f"- `name` (string): Nome do NPC (ex: 'Mestre Feng, o Ferreiro')\n"
            f"- `description` (string): Aparência e aura (50-100 palavras)\n"
            f"- `personality` (array of strings): 3-5 traços (ex: ['wise', 'patient', 'greedy'])\n"
            f"- `backstory` (string): História curta (30-50 palavras)\n"
            f"- `dialogue_style` (string): Como ele fala (ex: 'formal e respeitoso', 'brincalhão')\n"
            f"- `stats` (object): hp (number), defense (number), rank (number 1-9)\n\n"
            f"JSON de Saída:"
        )
        
        print(f"--- Gerando NPC amigável ({role}) para {location} ---")
        npc_data = self.gemini_client.generate_json(prompt, task="story")
        
        if "error" in npc_data:
            return npc_data
        
        # Add metadata
        npc_data["role"] = role
        npc_data["emotional_state"] = "friendly"
        npc_data["current_location"] = location
        
        return npc_data
    
    def generate_neutral_npc(self, location: str, occupation: str = "traveler") -> Dict[str, Any]:
        """
        Gera um NPC neutro (traveler, guard, scholar, farmer, etc)
        Pode se tornar amigável ou hostil baseado em ações do player
        """
        prompt = (
            f"Você é um gerador de NPCs para um RPG de Cultivo Wuxia/Xianxia.\n"
            f"Crie um NPC NEUTRO (nem amigável, nem hostil inicialmente):\n"
            f"- **Localização:** {location}\n"
            f"- **Ocupação:** {occupation}\n\n"
            f"Responda APENAS com um objeto JSON com estas chaves:\n"
            f"- `name` (string): Nome completo\n"
            f"- `description` (string): Aparência (30-50 palavras)\n"
            f"- `personality` (array of strings): 3 traços de personalidade\n"
            f"- `motivation` (string): O que ele quer (ex: 'proteger sua família')\n"
            f"- `stats` (object): hp, defense, rank (1-9)\n\n"
            f"JSON de Saída:"
        )
        
        print(f"--- Gerando NPC neutro ({occupation}) para {location} ---")
        npc_data = self.gemini_client.generate_json(prompt, task="story")
        
        if "error" in npc_data:
            return npc_data
        
        # Add metadata
        npc_data["occupation"] = occupation
        npc_data["emotional_state"] = "neutral"
        npc_data["current_location"] = location
        
        return npc_data
