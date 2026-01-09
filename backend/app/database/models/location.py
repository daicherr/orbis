"""
Location Models - Sistema de Localizações do Mundo
GEM RPG ORBIS - Arquitetura Cognitiva

Dois tipos de localizações:
1. Location: Locais estruturados do mapa do mundo (cidades, florestas, montanhas)
2. DynamicLocation: Locais criados narrativamente (casas, lojas, dungeons)
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from sqlmodel import Field, SQLModel, Column, JSON


class LocationType(str, Enum):
    """Tipos de localização do mundo."""
    CITY = "city"               # Cidades e vilas
    VILLAGE = "village"         # Pequenas comunidades
    FOREST = "forest"           # Florestas
    MOUNTAIN = "mountain"       # Montanhas
    CAVE = "cave"               # Cavernas
    RUINS = "ruins"             # Ruínas antigas
    TEMPLE = "temple"           # Templos e santuários
    SECT = "sect"               # Seitas de cultivo
    DUNGEON = "dungeon"         # Masmorras
    WILDERNESS = "wilderness"   # Áreas selvagens
    LAKE = "lake"               # Lagos e rios
    DESERT = "desert"           # Desertos
    SWAMP = "swamp"             # Pântanos
    PLAINS = "plains"           # Planícies
    COAST = "coast"             # Áreas costeiras
    POCKET_REALM = "pocket_realm"  # Reinos de bolso (dimensões alternativas)


class BiomeType(str, Enum):
    """Tipos de bioma para mecânicas de clima e criaturas."""
    TEMPERATE = "temperate"     # Clima temperado
    TROPICAL = "tropical"       # Tropical/Úmido
    ARCTIC = "arctic"           # Gélido
    VOLCANIC = "volcanic"       # Vulcânico
    SPIRITUAL = "spiritual"     # Rico em Qi
    CORRUPTED = "corrupted"     # Corrompido por energia demoníaca
    CELESTIAL = "celestial"     # Abençoado por energia celestial
    ABYSSAL = "abyssal"         # Influenciado pelo Abismo


class DangerLevel(str, Enum):
    """Níveis de perigo para uma localização."""
    SAFE = "safe"               # Seguro (vilas protegidas) - Tier 0
    LOW = "low"                 # Perigo baixo - Tier 1-2
    MODERATE = "moderate"       # Perigo moderado - Tier 3-4
    HIGH = "high"               # Perigo alto - Tier 5-6
    EXTREME = "extreme"         # Extremamente perigoso - Tier 7-8
    FORBIDDEN = "forbidden"     # Proibido/Letal - Tier 9+


class Location(SQLModel, table=True):
    """
    Localização estruturada do mapa do mundo.
    Representa cidades, florestas, montanhas, etc.
    """
    __tablename__ = "locations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # ==================== IDENTIFICAÇÃO ====================
    name: str = Field(index=True, unique=True)  # "Floresta Nublada"
    display_name: str = Field(default="")  # "A Misteriosa Floresta Nublada"
    location_type: str = Field(default=LocationType.WILDERNESS)
    
    # ==================== DESCRIÇÃO ====================
    description: str = Field(default="")  # Descrição narrativa
    short_description: str = Field(default="")  # Descrição curta para listagens
    atmosphere: str = Field(default="neutral")  # peaceful, tense, mysterious, dangerous, sacred
    
    # ==================== GEOGRAFIA ====================
    # Região pai (hierarquia): Location pode estar dentro de outra
    parent_region: Optional[str] = Field(default=None, index=True)  # "Continente Leste"
    
    # Conexões com outras localizações (grafo de navegação)
    # {"Floresta Nublada": {"distance": 1, "travel_time": "2 hours", "danger": "low"}}
    connections: Dict[str, Dict[str, Any]] = Field(default={}, sa_column=Column(JSON))
    
    # Sublocais dentro desta localização
    sub_locations: List[str] = Field(default=[], sa_column=Column(JSON))
    
    # Coordenadas abstratas para mapa (opcional)
    x: Optional[float] = Field(default=None)
    y: Optional[float] = Field(default=None)
    
    # ==================== BIOMA E PERIGO ====================
    biome: str = Field(default=BiomeType.TEMPERATE)
    danger_level: str = Field(default=DangerLevel.SAFE)
    recommended_tier: int = Field(default=1)  # Tier mínimo recomendado
    max_tier: int = Field(default=3)  # Tier máximo de inimigos que aparecem
    
    # ==================== RECURSOS E ECONOMIA ====================
    # Recursos disponíveis: {"herb": ["Ginseng Espiritual", "Raiz de Lótus"], "ore": ["Ferro Celeste"]}
    resources: Dict[str, List[str]] = Field(default={}, sa_column=Column(JSON))
    
    # Preços locais (modificadores): {"food": 1.2, "weapons": 0.8} = comida 20% mais cara
    price_modifiers: Dict[str, float] = Field(default={}, sa_column=Column(JSON))
    
    # ==================== FACÇÃO E CONTROLE ====================
    controlling_faction: Optional[str] = Field(default=None, index=True)
    faction_influence: float = Field(default=0.0)  # 0-100
    
    # ==================== CLIMA E TEMPO ====================
    weather_pattern: str = Field(default="normal")  # normal, rainy, snowy, foggy, stormy
    current_weather: str = Field(default="clear")
    
    # Eventos especiais que podem ocorrer: ["beast_tide", "spiritual_treasure_appears"]
    possible_events: List[str] = Field(default=[], sa_column=Column(JSON))
    
    # ==================== POPULAÇÃO ====================
    population: int = Field(default=0)  # 0 para áreas selvagens
    npc_spawn_types: List[str] = Field(default=[], sa_column=Column(JSON))  # ["beast", "bandit", "cultivator"]
    max_npc_count: int = Field(default=10)
    
    # ==================== LORE ====================
    history: str = Field(default="")  # História do local
    secrets: List[str] = Field(default=[], sa_column=Column(JSON))  # Segredos escondidos
    legend: Optional[str] = Field(default=None)  # Lenda associada
    
    # ==================== FLAGS ====================
    is_safe_zone: bool = Field(default=False)  # PvP desabilitado, sem combate
    is_pvp_zone: bool = Field(default=False)  # PvP habilitado
    is_hidden: bool = Field(default=False)  # Precisa descobrir para visitar
    is_locked: bool = Field(default=False)  # Precisa de chave/requisito
    lock_requirement: Optional[str] = Field(default=None)  # "tier >= 5" ou "has_key: ancient_key"
    
    # ==================== TIMESTAMPS ====================
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    def get_danger_tier_range(self) -> tuple[int, int]:
        """Retorna range de tier baseado no nível de perigo."""
        ranges = {
            DangerLevel.SAFE: (0, 0),
            DangerLevel.LOW: (1, 2),
            DangerLevel.MODERATE: (3, 4),
            DangerLevel.HIGH: (5, 6),
            DangerLevel.EXTREME: (7, 8),
            DangerLevel.FORBIDDEN: (9, 9),
        }
        return ranges.get(self.danger_level, (1, 3))
    
    def can_player_enter(self, player_tier: int) -> bool:
        """Verifica se um player pode entrar baseado no tier."""
        if self.is_locked:
            return False  # Precisa verificar lock_requirement separadamente
        
        # Em locais perigosos, alertar mas não bloquear
        return True
    
    def get_tier_warning(self, player_tier: int) -> Optional[str]:
        """Retorna aviso se o local for perigoso demais."""
        min_tier, max_tier = self.get_danger_tier_range()
        
        if player_tier < min_tier:
            diff = min_tier - player_tier
            if diff >= 3:
                return f"⚠️ PERIGO MORTAL: Este local requer Tier {min_tier}+. Você provavelmente morrerá."
            elif diff >= 2:
                return f"⚠️ MUITO PERIGOSO: Este local requer Tier {min_tier}+. Prossiga com extrema cautela."
            else:
                return f"⚡ DESAFIADOR: Este local é um pouco acima do seu nível atual."
        
        return None
    
    def get_connected_locations(self) -> List[str]:
        """Retorna lista de localizações conectadas."""
        return list(self.connections.keys())
    
    def get_travel_info(self, destination: str) -> Optional[Dict[str, Any]]:
        """Retorna informações de viagem para um destino."""
        return self.connections.get(destination)
    
    def to_context_string(self) -> str:
        """Retorna string de contexto para prompts de IA."""
        parts = [
            f"Local: {self.display_name or self.name}",
            f"Tipo: {self.location_type}",
            f"Bioma: {self.biome}",
            f"Perigo: {self.danger_level} (Tier {self.recommended_tier}-{self.max_tier})",
        ]
        
        if self.controlling_faction:
            parts.append(f"Controlado por: {self.controlling_faction}")
        
        if self.atmosphere != "neutral":
            parts.append(f"Atmosfera: {self.atmosphere}")
        
        if self.short_description:
            parts.append(f"Descrição: {self.short_description}")
        
        return " | ".join(parts)


class DynamicLocation(SQLModel, table=True):
    """
    Locais dinâmicos criados pelo Mestre ou por ações do player.
    
    Exemplos:
    - "Casa do Wei Lin" (criada no Session Zero)
    - "Cabana Abandonada na Floresta" (criada durante narrativa)
    - "Loja do Alquimista Chen" (criada quando player pediu para comprar algo)
    """
    __tablename__ = "dynamic_locations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Identificação
    name: str = Field(index=True)  # "Casa do Wei Lin"
    location_type: str = Field(default="generic")  # residence, shop, dungeon, ruins, temple
    
    # Hierarquia Geográfica
    parent_location: str = Field(index=True)  # "Floresta Nublada" (localização macro)
    parent_location_id: Optional[int] = Field(default=None, foreign_key="locations.id")
    
    # Propriedade
    owner_player_id: Optional[int] = Field(default=None, index=True)  # Se for casa de um player
    owner_npc_id: Optional[int] = Field(default=None)  # Se pertencer a um NPC
    owner_name: Optional[str] = Field(default=None)  # Nome do dono para referência
    
    # Descrição Narrativa
    description: str  # Descrição rica gerada pela IA
    interior_description: Optional[str] = None  # Como é por dentro
    atmosphere: str = Field(default="neutral")  # peaceful, cozy, dark, mysterious
    
    # Metadados
    created_by: str = Field(default="narrative")  # "session_zero" | "narrative" | "player_request"
    creation_context: Optional[str] = None  # "Player pediu para comprar casa"
    
    # Estado
    is_destroyed: bool = Field(default=False)
    destruction_event_id: Optional[int] = Field(default=None)
    is_public: bool = Field(default=True)  # Outros players podem encontrar?
    is_hidden: bool = Field(default=False)  # Precisa descobrir para visitar?
    is_locked: bool = Field(default=False)  # Precisa de permissão do dono
    
    # Conteúdo
    npcs_present: List[int] = Field(default=[], sa_column=Column(JSON))
    items_available: List[dict] = Field(default=[], sa_column=Column(JSON))  # Se for loja
    stored_items: List[dict] = Field(default=[], sa_column=Column(JSON))  # Itens guardados
    
    # Modificadores
    qi_density: float = Field(default=1.0)  # Multiplicador de cultivo (1.0 = normal)
    safety_level: str = Field(default="normal")  # safe, normal, dangerous
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_visited_at: Optional[datetime] = None
    
    def to_context_string(self) -> str:
        """Retorna string de contexto para prompts de IA."""
        parts = [
            f"Local: {self.name}",
            f"Tipo: {self.location_type}",
            f"Em: {self.parent_location}",
        ]
        
        if self.owner_name:
            parts.append(f"Dono: {self.owner_name}")
        
        if self.atmosphere != "neutral":
            parts.append(f"Atmosfera: {self.atmosphere}")
        
        return " | ".join(parts)


class LocationAlias(SQLModel, table=True):
    """
    Aliases para locais - permite "casa", "lar", "minha cabana" apontar para o mesmo lugar.
    """
    __tablename__ = "location_aliases"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    alias: str = Field(index=True)  # "casa", "lar", "minha cabana"
    location_id: Optional[int] = Field(default=None, foreign_key="dynamic_locations.id")
    player_id: int = Field(index=True)  # Alias é pessoal por player
    
    # Para locais estáticos (que não estão em dynamic_locations)
    static_location_name: Optional[str] = None  # "Floresta Nublada"
    static_location_id: Optional[int] = Field(default=None, foreign_key="locations.id")


class LocationVisit(SQLModel, table=True):
    """
    Histórico de visitas a locais para tracking e descoberta.
    """
    __tablename__ = "location_visits"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(index=True)
    
    # Pode ser location estática ou dinâmica
    location_name: str = Field(index=True)
    location_id: Optional[int] = Field(default=None)
    dynamic_location_id: Optional[int] = Field(default=None)
    
    # Tracking
    first_visit: datetime = Field(default_factory=datetime.utcnow)
    last_visit: datetime = Field(default_factory=datetime.utcnow)
    visit_count: int = Field(default=1)
    
    # Descobertas neste local
    secrets_found: List[str] = Field(default=[], sa_column=Column(JSON))
    npcs_met: List[str] = Field(default=[], sa_column=Column(JSON))
    items_found: List[str] = Field(default=[], sa_column=Column(JSON))
