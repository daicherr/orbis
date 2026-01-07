from typing import Optional, List
from sqlmodel import Field, SQLModel, JSON, Column

class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    rank: int = Field(default=1)
    xp: float = Field(default=0.0)
    
    # Tríade Energética
    quintessential_essence: float = Field(default=100.0)
    shadow_chi: float = Field(default=100.0)
    yuan_qi: float = Field(default=100.0)
    
    # Atributos de Combate
    current_hp: float = Field(default=100.0)
    max_hp: float = Field(default=100.0)
    defense: float = Field(default=10.0)
    
    # Corrupção (Heart Demon)
    corruption: float = Field(default=0.0)
    willpower: float = Field(default=50.0)
    
    constitution: str = Field(default="Mortal Body")
    
    inventory: List[dict] = Field(default=[], sa_column=Column(JSON)) # Ex: [{"item_id": "spirit_stone", "quantity": 10}]
    status_effects: List[dict] = Field(default=[], sa_column=Column(JSON)) # Ex: [{"type": "dot", "turns_left": 2}]
