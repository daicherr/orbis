from typing import Optional, List
from sqlmodel import Field, SQLModel, JSON, Column

class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    rank: int = Field(default=1)
    xp: float = Field(default=0.0)
    
    # Character Creation (Session Zero)
    appearance: Optional[str] = Field(default=None)  # Descrição opcional da aparência
    constitution_type: str = Field(default="Mortal")  # Mortal, Godfiend, Taboo
    origin_location: str = Field(default="Floresta Nublada")  # Local de origem
    backstory: Optional[str] = Field(default=None)  # História gerada pelo Session Zero
    
    # Casa e Contexto Inicial (NOVO)
    home_location: Optional[str] = Field(default=None)  # "casa" aponta para cá
    home_location_id: Optional[int] = Field(default=None)  # FK para DynamicLocation se criado
    first_scene_context: Optional[str] = Field(default=None)  # "Onde sua jornada começa?"
    important_npc_name: Optional[str] = Field(default=None)  # NPC importante definido no Session Zero
    
    # Sistema de Cultivation (GDD)
    cultivation_tier: int = Field(default=1)  # 1-9 tiers do GDD
    can_fly: bool = Field(default=False)  # Desbloqueado no Tier 3+
    physics_type: str = Field(default="newtonian")  # newtonian, malleable, conceptual
    
    # Tríade Energética
    quintessential_essence: float = Field(default=100.0)
    max_quintessential_essence: float = Field(default=100.0)
    shadow_chi: float = Field(default=100.0)
    max_shadow_chi: float = Field(default=100.0)
    yuan_qi: float = Field(default=100.0)
    max_yuan_qi: float = Field(default=100.0)
    
    # Atributos de Combate
    current_hp: float = Field(default=100.0)
    max_hp: float = Field(default=100.0)
    defense: float = Field(default=10.0)
    speed: float = Field(default=10.0)  # Para Lightning Devastator e iniciativa
    strength: float = Field(default=10.0)  # Para Dragon Body
    
    # Corrupção (Heart Demon)
    corruption: float = Field(default=0.0)
    willpower: float = Field(default=50.0)
    betrayals: int = Field(default=0)  # Para fórmula de corrupção
    
    constitution: str = Field(default="Mortal Body")
    
    # Economia
    gold: int = Field(default=100)  # Moeda principal
    
    # Localização e navegação
    current_location: str = Field(default="Início da Jornada")
    
    # Arrays e Alquimia
    active_arrays: List[dict] = Field(default=[], sa_column=Column(JSON))  # Arrays ativos
    spiritual_flames: List[str] = Field(default=[], sa_column=Column(JSON))  # Chamas capturadas
    
    inventory: List[dict] = Field(default=[], sa_column=Column(JSON)) # Ex: [{"item_id": "spirit_stone", "quantity": 10}]
    status_effects: List[dict] = Field(default=[], sa_column=Column(JSON)) # Ex: [{"type": "dot", "turns_left": 2}]
    learned_skills: List[str] = Field(default=["silent_strike"], sa_column=Column(JSON))  # Skills desbloqueadas
    
    # Estatísticas de combate
    kill_count: int = Field(default=0)  # Número de mortes causadas pelo jogador
    kill_history: List[dict] = Field(default=[], sa_column=Column(JSON))  # Histórico de mortes [{victim_name, victim_rank, location}]
