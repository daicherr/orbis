from typing import Optional, List
from sqlmodel import Field, SQLModel, JSON, Column

class Faction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    power_level: int = Field(default=100)
    resources: int = Field(default=1000)
    relations: dict = Field(default={}, sa_column=Column(JSON)) # Ex: {"FactionName": "allied/hostile"}

class WorldEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    description: str
    turn_occurred: int
    effects: dict = Field(default={}, sa_column=Column(JSON)) # Ex: {"faction_id": 1, "resource_change": -500}

class GlobalEconomy(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    resource_name: str = Field(unique=True, index=True)
    base_price: float
    current_price: float
    supply: int
    demand: int
