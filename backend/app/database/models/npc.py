from typing import Optional, List
from sqlmodel import Field, SQLModel, JSON, Column

class NPC(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    rank: int = Field(default=1)
    
    # Atributos de Combate (semelhante ao Player)
    current_hp: float = Field(default=100.0)
    max_hp: float = Field(default=100.0)
    defense: float = Field(default=10.0)
    
    # Personalidade e Estado da IA
    personality_traits: List[str] = Field(sa_column=Column(JSON))
    emotional_state: str = Field(default="neutral") # ex: neutral, hostile, friendly
    vendetta_target: Optional[int] = Field(default=None, foreign_key="player.id")
    
    # Localização
    current_location: str = Field(default="Initial Village")
    
    available_quest_ids: List[int] = Field(default=[], sa_column=Column(JSON))
    
    status_effects: List[dict] = Field(default=[], sa_column=Column(JSON))
    
    # Memória Vetorial (será populada pelo pgvector)
    # A coluna de vetores em si será adicionada diretamente via SQL ou em um script de migração,
    # pois o SQLModel não tem suporte nativo para pgvector.
    # memory_vector: Optional[List[float]]
