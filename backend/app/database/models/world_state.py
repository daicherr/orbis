from typing import Optional, List
from sqlmodel import Field, SQLModel, JSON, Column

class Faction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    power_level: int = Field(default=100)
    resources: int = Field(default=1000)
    relations: dict = Field(default={}, sa_column=Column(JSON)) # Ex: {"FactionName": "allied/hostile"}

class WorldEvent(SQLModel, table=True):
    """
    Eventos globais que afetam TODOS os players.
    Destruições, mortes importantes, guerras de facção.
    Players podem investigar para descobrir o autor.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Tipo e descrição
    event_type: str = Field(default="generic")  # destruction, npc_death, faction_war, calamity, player_action
    description: str
    public_description: str = Field(default="")  # O que todos sabem
    secret_description: str = Field(default="")  # O que investigação revela
    
    # Localização afetada
    location_affected: Optional[str] = Field(default=None, index=True)  # Qual local foi impactado
    
    # Autoria (para investigação)
    caused_by_player_id: Optional[int] = Field(default=None, index=True)  # Qual player causou
    caused_by_npc_id: Optional[int] = Field(default=None)  # Ou qual NPC causou
    author_alias: Optional[str] = Field(default=None)  # "Demônio de Olhos Vermelhos" (nome que sobreviventes dão)
    
    # Timing
    turn_occurred: int
    is_active: bool = Field(default=True)  # Evento ainda tem efeitos no mundo?
    
    # Investigação
    investigation_difficulty: int = Field(default=5)  # 1-10, quão difícil descobrir o autor
    clues: List[str] = Field(default=[], sa_column=Column(JSON))  # Pistas deixadas
    
    effects: dict = Field(default={}, sa_column=Column(JSON))  # Ex: {"faction_id": 1, "resource_change": -500}

class GlobalEconomy(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    resource_name: str = Field(unique=True, index=True)
    base_price: float
    current_price: float
    supply: int
    demand: int
