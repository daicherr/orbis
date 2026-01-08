"""
GameLog Model - Persistent Turn History
Stores every game turn with embeddings for semantic search
"""
from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, Column, JSON
from pgvector.sqlalchemy import Vector


class GameLog(SQLModel, table=True):
    """
    Persistent storage for game turns
    Replaces volatile game_state dict
    """
    __tablename__ = "game_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(index=True)  # Removed foreign key constraint for simpler migration
    turn_number: int = Field(index=True)
    
    # Turn Data
    player_input: str  # What the player typed
    scene_description: str  # Narrator's output
    action_result: Optional[str] = None  # Combat/skill results
    
    # Context
    location: str  # Where it happened
    npcs_present: list = Field(default_factory=list, sa_column=Column(JSON))  # NPC IDs in scene
    world_time: str  # Chronos timestamp
    
    # Vector Search (128D embeddings)
    embedding: Optional[list] = Field(
        default=None, 
        sa_column=Column(Vector(128))
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True
