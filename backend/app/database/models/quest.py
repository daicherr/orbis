from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime

class Quest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    
    quest_giver_id: Optional[int] = Field(default=None, foreign_key="npc.id")
    player_id: Optional[int] = Field(default=None, foreign_key="player.id")
    
    status: str = Field(default="not_started") # not_started, in_progress, completed, failed
    
    objective_type: str # ex: kill, fetch, escort
    objective_target: str # ex: "Serpente Vil", "Sunstone"
    objective_quantity: int = Field(default=1)
    
    reward_xp: int = Field(default=0)
    reward_gold: int = Field(default=0)
    # Adicionar reward_items se houver uma tabela de itens
    
    deadline: Optional[datetime] = Field(default=None)
    
