"""
NPC Population Manager - Sprint 11
Gerencia densidade e tipos de NPCs por localização.

Regras de Densidade:
- Cidades Grandes: 3-5 NPCs visíveis por cena
- Vilas Médias: 2-3 NPCs
- Wilderness/Dungeons: 0-2 NPCs (hostis)
- Locais Sagrados: 1-2 NPCs (neutros)
- Estabelecimentos (taverna, loja): 1-3 NPCs específicos do tipo
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import random


@dataclass
class LocationProfile:
    """Perfil de uma localização para spawning de NPCs"""
    location_type: str  # settlement, wilderness, dungeon, sacred, establishment
    size: str  # small, medium, large
    npc_min: int
    npc_max: int
    hostile_chance: float  # 0.0 a 1.0
    npc_roles: List[str]  # Roles possíveis para NPCs neste local


# Configuração de densidade por tipo de localização
LOCATION_PROFILES = {
    # === SETTLEMENTS ===
    "cidade_imperial": LocationProfile(
        location_type="settlement",
        size="large",
        npc_min=3,
        npc_max=5,
        hostile_chance=0.05,  # 5% chance de pickpocket/thief
        npc_roles=["merchant", "guard", "noble", "cultivator", "scholar", "beggar"]
    ),
    "vila": LocationProfile(
        location_type="settlement",
        size="small",
        npc_min=1,
        npc_max=3,
        hostile_chance=0.0,
        npc_roles=["farmer", "elder", "merchant", "healer", "blacksmith"]
    ),
    "porto": LocationProfile(
        location_type="settlement",
        size="medium",
        npc_min=2,
        npc_max=4,
        hostile_chance=0.1,  # Piratas e contrabandistas
        npc_roles=["sailor", "merchant", "fisherman", "smuggler", "tavern_keeper"]
    ),
    
    # === WILDERNESS ===
    "floresta": LocationProfile(
        location_type="wilderness",
        size="medium",
        npc_min=0,
        npc_max=2,
        hostile_chance=0.7,  # 70% monstros/bandidos
        npc_roles=["beast", "bandit", "hermit", "hunter"]
    ),
    "montanha": LocationProfile(
        location_type="wilderness",
        size="large",
        npc_min=0,
        npc_max=2,
        hostile_chance=0.8,
        npc_roles=["beast", "cultivator_rogue", "hermit"]
    ),
    "deserto": LocationProfile(
        location_type="wilderness",
        size="large",
        npc_min=0,
        npc_max=1,
        hostile_chance=0.6,
        npc_roles=["beast", "nomad", "bandit"]
    ),
    "pântano": LocationProfile(
        location_type="wilderness",
        size="medium",
        npc_min=0,
        npc_max=2,
        hostile_chance=0.9,  # Muito perigoso
        npc_roles=["beast", "poison_creature", "witch"]
    ),
    
    # === DUNGEONS ===
    "caverna": LocationProfile(
        location_type="dungeon",
        size="medium",
        npc_min=1,
        npc_max=3,
        hostile_chance=0.95,
        npc_roles=["beast", "undead", "golem", "treasure_guardian"]
    ),
    "ruínas": LocationProfile(
        location_type="dungeon",
        size="medium",
        npc_min=1,
        npc_max=2,
        hostile_chance=0.85,
        npc_roles=["undead", "spirit", "golem", "rogue_cultivator"]
    ),
    "abismo": LocationProfile(
        location_type="dungeon",
        size="large",
        npc_min=1,
        npc_max=4,
        hostile_chance=1.0,  # Sempre hostil
        npc_roles=["demon", "ancient_beast", "corrupted_cultivator"]
    ),
    
    # === SACRED ===
    "templo": LocationProfile(
        location_type="sacred",
        size="medium",
        npc_min=1,
        npc_max=3,
        hostile_chance=0.0,
        npc_roles=["monk", "priest", "guardian", "pilgrim", "scholar"]
    ),
    "monastério": LocationProfile(
        location_type="sacred",
        size="medium",
        npc_min=2,
        npc_max=4,
        hostile_chance=0.0,
        npc_roles=["monk", "master", "disciple", "librarian"]
    ),
    "santuário": LocationProfile(
        location_type="sacred",
        size="small",
        npc_min=0,
        npc_max=2,
        hostile_chance=0.1,  # Pode ter guardian spirit
        npc_roles=["spirit", "guardian", "hermit"]
    ),
    
    # === ESTABLISHMENTS (sub-locais) ===
    "taverna": LocationProfile(
        location_type="establishment",
        size="small",
        npc_min=2,
        npc_max=4,
        hostile_chance=0.1,  # Bêbados agressivos
        npc_roles=["tavern_keeper", "bard", "drunk", "traveler", "informant", "bounty_hunter"]
    ),
    "loja": LocationProfile(
        location_type="establishment",
        size="small",
        npc_min=1,
        npc_max=2,
        hostile_chance=0.0,
        npc_roles=["merchant", "apprentice", "customer"]
    ),
    "forja": LocationProfile(
        location_type="establishment",
        size="small",
        npc_min=1,
        npc_max=2,
        hostile_chance=0.0,
        npc_roles=["blacksmith", "apprentice"]
    ),
    "arena": LocationProfile(
        location_type="establishment",
        size="large",
        npc_min=3,
        npc_max=6,
        hostile_chance=0.3,  # Lutadores desafiantes
        npc_roles=["fighter", "announcer", "gambler", "noble", "champion"]
    ),
    "mercado": LocationProfile(
        location_type="establishment",
        size="medium",
        npc_min=3,
        npc_max=5,
        hostile_chance=0.05,
        npc_roles=["merchant", "customer", "guard", "pickpocket", "performer"]
    ),
}

# Mapeamento de palavras-chave para profiles
KEYWORD_TO_PROFILE = {
    # Settlements
    "cidade imperial": "cidade_imperial",
    "cidade": "cidade_imperial",
    "vila": "vila",
    "aldeia": "vila",
    "vilarejo": "vila",
    "porto": "porto",
    "cais": "porto",
    
    # Wilderness
    "floresta": "floresta",
    "bosque": "floresta",
    "selva": "floresta",
    "montanha": "montanha",
    "pico": "montanha",
    "vale": "montanha",
    "deserto": "deserto",
    "oásis": "deserto",
    "pântano": "pântano",
    "brejo": "pântano",
    "planície": "floresta",  # Fallback
    
    # Dungeons
    "caverna": "caverna",
    "gruta": "caverna",
    "mina": "caverna",
    "ruínas": "ruínas",
    "tumba": "ruínas",
    "abismo": "abismo",
    "submundo": "abismo",
    
    # Sacred
    "templo": "templo",
    "altar": "templo",
    "santuário": "santuário",
    "monastério": "monastério",
    "mosteiro": "monastério",
    
    # Establishments (sub-locais em cidades)
    "taverna": "taverna",
    "estalagem": "taverna",
    "hospedaria": "taverna",
    "caldeirão": "taverna",  # Nome comum de tavernas
    "bar": "taverna",
    "taberna": "taverna",
    "balcão": "taverna",  # Balcão de taverna
    "loja": "loja",
    "boticário": "loja",
    "alquimista": "loja",
    "forja": "forja",
    "ferreiro": "forja",
    "arena": "arena",
    "coliseu": "arena",
    "mercado": "mercado",
    "feira": "mercado",
    "praça": "mercado",  # Praças geralmente têm comércio
}


class NPCPopulationManager:
    """
    Gerencia a população de NPCs dinamicamente por localização.
    """
    
    def __init__(self):
        self.spawn_cooldowns: Dict[str, int] = {}  # location -> turns until next spawn
    
    def get_location_profile(self, location: str) -> LocationProfile:
        """
        Determina o perfil da localização baseado no nome.
        Usa matching de palavras-chave com fallback inteligente.
        """
        location_lower = location.lower()
        
        # Tentar match direto primeiro
        for keyword, profile_key in KEYWORD_TO_PROFILE.items():
            if keyword in location_lower:
                return LOCATION_PROFILES[profile_key]
        
        # Fallback inteligente: detectar contexto por palavras comuns
        # Indicadores de estabelecimento/interior civilizado
        establishment_hints = [
            "viajante", "atendimento", "salão", "quarto", "cozinha",
            "recepção", "hall", "corredor", "escritório", "sala",
            "jardim interno", "pátio"
        ]
        if any(hint in location_lower for hint in establishment_hints):
            return LOCATION_PROFILES["taverna"]  # Fallback para estabelecimento
        
        # Indicadores de local sagrado
        sacred_hints = ["sagrado", "altar", "oração", "meditação", "ancestral"]
        if any(hint in location_lower for hint in sacred_hints):
            return LOCATION_PROFILES["templo"]
        
        # Indicadores de dungeon
        dungeon_hints = ["profundo", "escuro", "antigo", "perdido", "esquecido"]
        if any(hint in location_lower for hint in dungeon_hints):
            return LOCATION_PROFILES["ruínas"]
        
        # Fallback final: wilderness genérico
        return LocationProfile(
            location_type="wilderness",
            size="medium",
            npc_min=0,
            npc_max=1,
            hostile_chance=0.5,
            npc_roles=["beast", "wanderer"]
        )
    
    def calculate_spawn_count(
        self, 
        location: str, 
        current_npcs: int,
        time_of_day: str = "day"
    ) -> Tuple[int, List[str]]:
        """
        Calcula quantos NPCs devem ser spawnados e seus tipos.
        
        Returns:
            (count, roles) - Número de NPCs a spawnar e lista de roles
        """
        profile = self.get_location_profile(location)
        
        # Ajustar por hora do dia
        time_modifier = 1.0
        if time_of_day in ["night", "midnight"]:
            if profile.location_type in ["settlement", "establishment"]:
                time_modifier = 0.3  # Menos NPCs à noite em áreas civilizadas
            else:
                time_modifier = 1.2  # Mais monstros à noite em wilderness
        elif time_of_day == "dawn":
            time_modifier = 0.7
        
        # Calcular quantidade ideal
        ideal_min = int(profile.npc_min * time_modifier)
        ideal_max = int(profile.npc_max * time_modifier)
        
        # Quantos precisamos spawnar?
        target = random.randint(max(0, ideal_min), max(1, ideal_max))
        to_spawn = max(0, target - current_npcs)
        
        if to_spawn == 0:
            return (0, [])
        
        # Determinar roles para cada spawn
        roles = []
        for _ in range(to_spawn):
            # Decidir se hostil ou não
            if random.random() < profile.hostile_chance:
                hostile_roles = [r for r in profile.npc_roles if r in 
                    ["beast", "bandit", "demon", "undead", "golem", "spirit", 
                     "poison_creature", "corrupted_cultivator", "rogue_cultivator",
                     "ancient_beast", "treasure_guardian", "drunk", "pickpocket",
                     "fighter", "witch"]]
                if hostile_roles:
                    roles.append(("hostile", random.choice(hostile_roles)))
                else:
                    roles.append(("hostile", "beast"))
            else:
                friendly_roles = [r for r in profile.npc_roles if r not in 
                    ["beast", "bandit", "demon", "undead", "golem", 
                     "poison_creature", "corrupted_cultivator"]]
                if friendly_roles:
                    roles.append(("friendly", random.choice(friendly_roles)))
                else:
                    roles.append(("neutral", "wanderer"))
        
        return (to_spawn, roles)
    
    def should_spawn_quest_giver(self, location: str, player_has_quest: bool) -> bool:
        """
        Determina se devemos spawnar um NPC com quest.
        Mais provável em settlements, menos em wilderness.
        """
        if player_has_quest:
            return False  # Já tem quest ativa
        
        profile = self.get_location_profile(location)
        
        quest_chance = {
            "settlement": 0.3,
            "establishment": 0.4,
            "sacred": 0.5,
            "wilderness": 0.1,
            "dungeon": 0.05,
        }.get(profile.location_type, 0.1)
        
        return random.random() < quest_chance


# Instância global
npc_population_manager = NPCPopulationManager()
