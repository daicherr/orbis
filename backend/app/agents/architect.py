"""
Architect Agent - Gerador de Conteúdo Dinâmico
GEM RPG ORBIS - Arquitetura Cognitiva

Responsável por:
- Gerar inimigos com stats e drops
- Gerar NPCs amigáveis e neutros
- Gerar bestas (com can_speak=False por padrão)
- Persistir conteúdo gerado nos JSONs
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from app.services.gemini_client import GeminiClient
from app.core.data_manager import data_manager

# Mapeamento de espécies para valores padrão
SPECIES_DEFAULTS = {
    "human": {"can_speak": True, "aggression": 30, "courage": 50},
    "beast": {"can_speak": False, "aggression": 70, "courage": 40},
    "spirit": {"can_speak": True, "aggression": 20, "courage": 60},
    "demon": {"can_speak": True, "aggression": 80, "courage": 70},
    "undead": {"can_speak": False, "aggression": 90, "courage": 100},
    "construct": {"can_speak": False, "aggression": 50, "courage": 100},
}

# Mapeamento de roles para schedules típicos
ROLE_SCHEDULES = {
    "merchant": {
        "dawn": "home",
        "morning": "market",
        "noon": "market",
        "afternoon": "market",
        "evening": "tavern",
        "night": "home"
    },
    "guard": {
        "dawn": "barracks",
        "morning": "gate",
        "noon": "gate",
        "afternoon": "patrol",
        "evening": "gate",
        "night": "barracks"
    },
    "elder": {
        "dawn": "home",
        "morning": "council_hall",
        "noon": "council_hall",
        "afternoon": "home",
        "evening": "tavern",
        "night": "home"
    },
    "healer": {
        "dawn": "clinic",
        "morning": "clinic",
        "noon": "clinic",
        "afternoon": "clinic",
        "evening": "home",
        "night": "home"
    },
    "trainer": {
        "dawn": "training_grounds",
        "morning": "training_grounds",
        "noon": "tavern",
        "afternoon": "training_grounds",
        "evening": "home",
        "night": "home"
    },
}


class Architect:
    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client
        repo_root = Path(__file__).resolve().parents[3]
        self.items_path = str((repo_root / "ruleset_source/mechanics/items.json").resolve())
        self.loot_tables_path = str((repo_root / "ruleset_source/mechanics/loot_tables.json").resolve())
        self.bestiary_path = str((repo_root / "lore_library/bestiary.json").resolve())

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
                "value": 100
            }
            data_manager.append_to_list_json(self.items_path, new_item)
            return new_item["id"]
        
        return next(item['id'] for item in all_items if item['name'] == item_name)

    def _apply_species_defaults(self, npc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica valores padrão baseados na espécie."""
        species = npc_data.get("species", "human")
        defaults = SPECIES_DEFAULTS.get(species, SPECIES_DEFAULTS["human"])
        
        for key, value in defaults.items():
            if key not in npc_data:
                npc_data[key] = value
        
        return npc_data

    def _apply_role_schedule(self, npc_data: Dict[str, Any], location: str) -> Dict[str, Any]:
        """Aplica rotina padrão baseada no papel do NPC."""
        role = npc_data.get("role", "civilian")
        
        if role in ROLE_SCHEDULES:
            # Criar schedule adaptado à localização
            base_schedule = ROLE_SCHEDULES[role]
            adapted_schedule = {}
            
            for time_of_day, activity in base_schedule.items():
                if activity == "home":
                    adapted_schedule[time_of_day] = npc_data.get("home_location", location)
                else:
                    adapted_schedule[time_of_day] = f"{location}_{activity}"
            
            npc_data["daily_schedule"] = adapted_schedule
        
        return npc_data

    def generate_enemy(self, tier: int, biome: str, species: str = "beast") -> Dict[str, Any]:
        """
        Gera um inimigo completo com todos os novos campos.
        
        Args:
            tier: Nível de poder (1-9)
            biome: Ambiente onde vive
            species: Espécie (beast, demon, undead, spirit)
        """
        
        species_prompt_map = {
            "beast": "uma besta selvagem (animal mágico) que NÃO fala",
            "demon": "um demônio que pode falar e é inteligente",
            "undead": "um morto-vivo sem fala (zumbi, esqueleto, etc)",
            "spirit": "um espírito elemental que pode ou não falar",
        }
        species_desc = species_prompt_map.get(species, "uma criatura mágica")
        
        prompt = (
            f"Você é um gerador de conteúdo para um RPG de Cultivo (Wuxia/Xianxia).\n"
            f"Crie {species_desc} que habita o seguinte ambiente:\n"
            f"- **Tier de Poder:** {tier} (1 = animal melhorado, 9 = pode destruir montanhas)\n"
            f"- **Bioma:** {biome}\n"
            f"- **Espécie:** {species}\n\n"
            f"Responda APENAS com um objeto JSON com estas chaves:\n"
            f"- `name` (string): Nome evocativo (ex: 'Serpente da Névoa Fantasma')\n"
            f"- `gender` (string): 'male', 'female', ou 'unknown' para bestas\n"
            f"- `description` (string): Descrição literária da aparência (50-80 palavras)\n"
            f"- `personality` (array of strings): 2-3 traços comportamentais (ex: ['territorial', 'cunning'])\n"
            f"- `stats` (object): `hp`, `defense`, `attack`, `speed`, `rank` (= tier)\n"
            f"- `aggression` (number): 0-100, quão agressivo é\n"
            f"- `courage` (number): 0-100, quão corajoso (0=foge fácil, 100=nunca foge)\n"
            f"- `drops` (array of objects): 1-3 itens com `itemName`, `chance` (0.0-1.0), `quantity_min`, `quantity_max`\n\n"
            f"JSON de Saída:"
        )

        print(f"--- Gerando inimigo {species} Tier {tier} em {biome} ---")
        enemy_data = self.gemini_client.generate_json(prompt, task="story")
        
        if "error" in enemy_data:
            return enemy_data

        # Aplicar espécie e valores padrão
        enemy_data["species"] = species
        enemy_data = self._apply_species_defaults(enemy_data)
        enemy_data["role"] = "enemy"
        enemy_data["emotional_state"] = "hostile"
        enemy_data["is_alive"] = True
        enemy_data["is_active"] = True

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
        stats = enemy_data.get("stats", {})
        bestiary_entry = {
            "id": monster_id,
            "name": enemy_data["name"],
            "species": species,
            "gender": enemy_data.get("gender", "unknown"),
            "can_speak": enemy_data.get("can_speak", False),
            "description": enemy_data["description"],
            "personality": enemy_data.get("personality", []),
            "stats": {
                "hp": stats.get("hp", 100),
                "defense": stats.get("defense", 10),
                "attack": stats.get("attack", 10),
                "speed": stats.get("speed", 10),
                "rank": stats.get("rank", tier)
            },
            "aggression": enemy_data.get("aggression", 70),
            "courage": enemy_data.get("courage", 50)
        }
        data_manager.append_to_list_json(self.bestiary_path, bestiary_entry)
        
        print(f"✅ Inimigo '{enemy_data['name']}' ({species}) criado e salvo.")
        return {**bestiary_entry, "drops": processed_drops}
    
    def generate_friendly_npc(
        self, 
        location: str, 
        role: str = "merchant",
        faction_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gera um NPC amigável com todos os novos campos.
        
        Args:
            location: Onde o NPC está
            role: merchant, quest_giver, elder, healer, trainer, informant
            faction_id: Facção a que pertence (opcional)
        """
        prompt = (
            f"Você é um gerador de NPCs para um RPG de Cultivo Wuxia/Xianxia.\n"
            f"Crie um NPC HUMANO AMIGÁVEL:\n"
            f"- **Localização:** {location}\n"
            f"- **Papel:** {role}\n"
            f"- **Facção:** {faction_id or 'Nenhuma'}\n\n"
            f"Responda APENAS com um objeto JSON com estas chaves:\n"
            f"- `name` (string): Nome completo (ex: 'Mestre Feng, o Ferreiro')\n"
            f"- `gender` (string): 'male' ou 'female'\n"
            f"- `description` (string): Aparência física e vestimenta (50-80 palavras)\n"
            f"- `personality` (array of strings): 3-5 traços (ex: ['wise', 'patient', 'greedy'])\n"
            f"- `backstory` (string): História breve (30-50 palavras)\n"
            f"- `dialogue_style` (string): Como ele fala (ex: 'formal e respeitoso')\n"
            f"- `stats` (object): hp, defense, attack, speed, rank (1-9)\n"
            f"- `inventory` (array): Se for merchant, lista de 3-5 itens com `name`, `price`, `type`\n\n"
            f"JSON de Saída:"
        )
        
        print(f"--- Gerando NPC amigável ({role}) em {location} ---")
        npc_data = self.gemini_client.generate_json(prompt, task="story")
        
        if "error" in npc_data:
            return npc_data
        
        # Aplicar metadados
        npc_data["species"] = "human"
        npc_data["can_speak"] = True
        npc_data["role"] = role
        npc_data["emotional_state"] = "friendly"
        npc_data["current_location"] = location
        npc_data["home_location"] = location
        npc_data["is_alive"] = True
        npc_data["is_active"] = True
        
        # Aplicar valores padrão de espécie
        npc_data = self._apply_species_defaults(npc_data)
        
        # Aplicar schedule baseado no role
        npc_data = self._apply_role_schedule(npc_data, location)
        
        # Adicionar facção se especificada
        if faction_id:
            npc_data["faction_id"] = faction_id
            npc_data["faction_role"] = "member"
        
        # Inicializar relacionamentos vazio
        npc_data["relationships"] = {}
        
        print(f"✅ NPC amigável '{npc_data.get('name', 'Desconhecido')}' ({role}) criado.")
        return npc_data
    
    def generate_neutral_npc(
        self, 
        location: str, 
        occupation: str = "traveler",
        faction_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gera um NPC neutro que pode se tornar amigável ou hostil.
        
        Args:
            location: Onde o NPC está
            occupation: traveler, guard, scholar, farmer, artisan, etc
            faction_id: Facção a que pertence (opcional)
        """
        prompt = (
            f"Você é um gerador de NPCs para um RPG de Cultivo Wuxia/Xianxia.\n"
            f"Crie um NPC HUMANO NEUTRO (nem amigável, nem hostil inicialmente):\n"
            f"- **Localização:** {location}\n"
            f"- **Ocupação:** {occupation}\n"
            f"- **Facção:** {faction_id or 'Independente'}\n\n"
            f"Responda APENAS com um objeto JSON com estas chaves:\n"
            f"- `name` (string): Nome completo\n"
            f"- `gender` (string): 'male' ou 'female'\n"
            f"- `description` (string): Aparência física (30-50 palavras)\n"
            f"- `personality` (array of strings): 3 traços de personalidade\n"
            f"- `motivation` (string): O que ele quer ou busca\n"
            f"- `secret` (string): Um segredo que ele esconde (opcional, para hooks narrativos)\n"
            f"- `stats` (object): hp, defense, attack, speed, rank (1-9)\n\n"
            f"JSON de Saída:"
        )
        
        print(f"--- Gerando NPC neutro ({occupation}) em {location} ---")
        npc_data = self.gemini_client.generate_json(prompt, task="story")
        
        if "error" in npc_data:
            return npc_data
        
        # Aplicar metadados
        npc_data["species"] = "human"
        npc_data["can_speak"] = True
        npc_data["role"] = "civilian"
        npc_data["occupation"] = occupation
        npc_data["emotional_state"] = "neutral"
        npc_data["current_location"] = location
        npc_data["home_location"] = location
        npc_data["is_alive"] = True
        npc_data["is_active"] = True
        
        # Aplicar valores padrão
        npc_data = self._apply_species_defaults(npc_data)
        npc_data["aggression"] = 30  # Neutros são menos agressivos
        
        # Adicionar facção se especificada
        if faction_id:
            npc_data["faction_id"] = faction_id
            npc_data["faction_role"] = "member"
        
        # Inicializar relacionamentos vazio
        npc_data["relationships"] = {}
        
        print(f"✅ NPC neutro '{npc_data.get('name', 'Desconhecido')}' ({occupation}) criado.")
        return npc_data

    def generate_beast(self, tier: int, biome: str, is_spiritual: bool = False) -> Dict[str, Any]:
        """
        Gera uma besta (animal mágico).
        
        Args:
            tier: Nível de poder (1-9)
            biome: Ambiente onde vive
            is_spiritual: Se True, a besta pode falar e é mais inteligente
        """
        species_type = "spiritual_beast" if is_spiritual else "beast"
        can_speak = is_spiritual
        
        prompt = (
            f"Você é um gerador de conteúdo para um RPG de Cultivo (Wuxia/Xianxia).\n"
            f"Crie uma {'BESTA ESPIRITUAL (inteligente, pode falar)' if is_spiritual else 'BESTA SELVAGEM (animal, NÃO fala)'}:\n"
            f"- **Tier de Poder:** {tier}\n"
            f"- **Bioma:** {biome}\n\n"
            f"Responda APENAS com um objeto JSON com estas chaves:\n"
            f"- `name` (string): Nome da espécie (ex: 'Tigre da Aurora Escarlate')\n"
            f"- `gender` (string): 'male', 'female', ou 'unknown'\n"
            f"- `description` (string): Aparência física e aura (50-80 palavras)\n"
            f"- `behavior` (array of strings): 2-3 comportamentos típicos (ex: ['nocturnal', 'pack_hunter'])\n"
            f"- `habitat` (string): Onde especificamente vive no bioma\n"
            f"- `diet` (string): O que come\n"
            f"- `stats` (object): hp, defense, attack, speed, rank (= tier)\n"
            f"- `aggression` (number): 0-100\n"
            f"- `courage` (number): 0-100\n"
            f"- `drops` (array): 1-3 itens com itemName, chance, quantity_min, quantity_max\n\n"
            f"JSON de Saída:"
        )
        
        print(f"--- Gerando {'besta espiritual' if is_spiritual else 'besta selvagem'} Tier {tier} em {biome} ---")
        beast_data = self.gemini_client.generate_json(prompt, task="story")
        
        if "error" in beast_data:
            return beast_data
        
        # Aplicar metadados
        beast_data["species"] = "spirit" if is_spiritual else "beast"
        beast_data["can_speak"] = can_speak
        beast_data["role"] = "enemy"
        beast_data["emotional_state"] = "neutral"  # Bestas são neutras até provocadas
        beast_data["is_alive"] = True
        beast_data["is_active"] = True
        
        # Converter behavior para personality_traits
        beast_data["personality_traits"] = beast_data.get("behavior", [])
        
        # Processar drops
        processed_drops = []
        for drop in beast_data.get("drops", []):
            item_id = self._ensure_item_exists(drop["itemName"])
            processed_drops.append({
                "item_id": item_id,
                "chance": drop["chance"],
                "quantity_min": drop["quantity_min"],
                "quantity_max": drop["quantity_max"]
            })
        
        # Persistir no bestiário
        monster_id = beast_data["name"].lower().replace(" ", "_")
        stats = beast_data.get("stats", {})
        
        bestiary_entry = {
            "id": monster_id,
            "name": beast_data["name"],
            "species": beast_data["species"],
            "gender": beast_data.get("gender", "unknown"),
            "can_speak": can_speak,
            "description": beast_data["description"],
            "behavior": beast_data.get("behavior", []),
            "habitat": beast_data.get("habitat", biome),
            "diet": beast_data.get("diet", "unknown"),
            "stats": {
                "hp": stats.get("hp", 100),
                "defense": stats.get("defense", 10),
                "attack": stats.get("attack", 10),
                "speed": stats.get("speed", 10),
                "rank": stats.get("rank", tier)
            },
            "aggression": beast_data.get("aggression", 50),
            "courage": beast_data.get("courage", 40)
        }
        
        # Adicionar à loot_table
        loot_table_entry = {monster_id: {"name": beast_data["name"], "drops": processed_drops}}
        data_manager.update_dict_json(self.loot_tables_path, "monsters", loot_table_entry)
        
        # Adicionar ao bestiário
        data_manager.append_to_list_json(self.bestiary_path, bestiary_entry)
        
        print(f"✅ Besta '{beast_data['name']}' criada e salva.")
        return {**bestiary_entry, "drops": processed_drops}

    def generate_villain(
        self,
        tier: int,
        archetype: str,
        faction_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gera um vilão recorrente (antagonista com personalidade complexa).
        
        Args:
            tier: Nível de poder (1-9)
            archetype: rival, tyrant, mastermind, betrayer, fanatic
            faction_id: Facção que lidera ou pertence
        """
        archetype_desc = {
            "rival": "um rival arrogante que compete com o jogador por recursos e glória",
            "tyrant": "um tirano cruel que oprime os mais fracos",
            "mastermind": "um manipulador que move peças nas sombras",
            "betrayer": "alguém que parece amigável mas secretamente planeja traição",
            "fanatic": "um devoto de uma causa maligna que acredita estar certo"
        }.get(archetype, "um antagonista")
        
        prompt = (
            f"Você é um gerador de vilões para um RPG de Cultivo Wuxia/Xianxia.\n"
            f"Crie um VILÃO memorável:\n"
            f"- **Tier de Poder:** {tier}\n"
            f"- **Arquétipo:** {archetype_desc}\n"
            f"- **Facção:** {faction_id or 'Independente'}\n\n"
            f"Responda APENAS com um objeto JSON com estas chaves:\n"
            f"- `name` (string): Nome completo com título (ex: 'Lorde Shen, a Serpente Dourada')\n"
            f"- `title` (string): Título ou apelido\n"
            f"- `gender` (string): 'male' ou 'female'\n"
            f"- `description` (string): Aparência física imponente (60-100 palavras)\n"
            f"- `personality` (array of strings): 4-5 traços (ex: ['ruthless', 'patient', 'proud'])\n"
            f"- `motivation` (string): O que ele realmente quer (30-50 palavras)\n"
            f"- `backstory` (string): Origem e trauma que moldou seu caráter (50-80 palavras)\n"
            f"- `signature_technique` (string): Nome de sua técnica mais famosa\n"
            f"- `weakness` (string): Uma fraqueza explorável (física, emocional ou social)\n"
            f"- `stats` (object): hp, defense, attack, speed, rank (= tier)\n\n"
            f"JSON de Saída:"
        )
        
        print(f"--- Gerando vilão ({archetype}) Tier {tier} ---")
        villain_data = self.gemini_client.generate_json(prompt, task="story")
        
        if "error" in villain_data:
            return villain_data
        
        # Aplicar metadados
        villain_data["species"] = "human"
        villain_data["can_speak"] = True
        villain_data["role"] = "enemy"
        villain_data["emotional_state"] = "hostile"
        villain_data["is_alive"] = True
        villain_data["is_active"] = True
        villain_data["archetype"] = archetype
        
        # Vilões têm alta coragem e agressão variável
        villain_data["courage"] = 80 + (tier * 2)  # Mais forte = mais corajoso
        villain_data["aggression"] = {
            "rival": 60,
            "tyrant": 80,
            "mastermind": 40,  # Mastermind evita combate direto
            "betrayer": 30,   # Betrayer finge ser amigo
            "fanatic": 90
        }.get(archetype, 70)
        
        # Adicionar facção se especificada
        if faction_id:
            villain_data["faction_id"] = faction_id
            villain_data["faction_role"] = "leader"
        
        # Relacionamentos iniciais
        villain_data["relationships"] = {}
        
        print(f"✅ Vilão '{villain_data.get('name', 'Desconhecido')}' ({archetype}) criado.")
        return villain_data

    def create_npc_from_data(self, npc_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte dados do Architect para formato do modelo NPC do banco.
        Usado para criar NPCs no banco de dados a partir de dados gerados.
        """
        stats = npc_data.get("stats", {})
        
        return {
            "name": npc_data.get("name", "Desconhecido"),
            "rank": stats.get("rank", 1),
            
            # Identidade
            "species": npc_data.get("species", "human"),
            "gender": npc_data.get("gender", "unknown"),
            "can_speak": npc_data.get("can_speak", True),
            "description": npc_data.get("description"),
            
            # Combate
            "max_hp": stats.get("hp", 100),
            "current_hp": stats.get("hp", 100),
            "defense": stats.get("defense", 10),
            "attack_power": stats.get("attack", 10),
            "speed": stats.get("speed", 10),
            
            # Personalidade
            "personality_traits": npc_data.get("personality", npc_data.get("personality_traits", [])),
            "emotional_state": npc_data.get("emotional_state", "neutral"),
            "aggression": npc_data.get("aggression", 50),
            "courage": npc_data.get("courage", 50),
            
            # Localização
            "current_location": npc_data.get("current_location", "Unknown"),
            "home_location": npc_data.get("home_location"),
            "daily_schedule": npc_data.get("daily_schedule", {}),
            
            # Social
            "faction_id": npc_data.get("faction_id"),
            "faction_role": npc_data.get("faction_role"),
            "relationships": npc_data.get("relationships", {}),
            
            # Funcionalidade
            "role": npc_data.get("role", "civilian"),
            "inventory": npc_data.get("inventory", []),
            "dialogue_options": npc_data.get("dialogue_options", []),
            
            # Status
            "is_alive": npc_data.get("is_alive", True),
            "is_active": npc_data.get("is_active", True),
        }
