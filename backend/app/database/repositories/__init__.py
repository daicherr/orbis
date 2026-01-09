"""
Database Repositories - Data access layer
GEM RPG ORBIS - Arquitetura Cognitiva
"""

from app.database.repositories.player_repo import PlayerRepository
from app.database.repositories.npc_repo import NpcRepository
from app.database.repositories.gamelog_repo import GameLogRepository
from app.database.repositories.world_event_repo import WorldEventRepository
from app.database.repositories.faction_repo import FactionRepository
from app.database.repositories.economy_repo import GlobalEconomyRepository
from app.database.repositories.location_repo import (
    LocationRepository,
    DynamicLocationRepository,
    LocationAliasRepository,
    LocationVisitRepository
)

__all__ = [
    # Player & NPC
    "PlayerRepository",
    "NpcRepository",
    
    # Game Logs
    "GameLogRepository",
    
    # World State
    "WorldEventRepository",
    "FactionRepository",
    "GlobalEconomyRepository",
    
    # Locations
    "LocationRepository",
    "DynamicLocationRepository",
    "LocationAliasRepository",
    "LocationVisitRepository",
]