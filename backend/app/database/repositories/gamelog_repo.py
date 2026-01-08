"""
GameLogRepository - Persistent Turn History Management
"""
from typing import Optional, List
from sqlmodel import Session, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.logs import GameLog
from ...services.embedding_service import EmbeddingService


class GameLogRepository:
    """
    Repository for GameLog CRUD operations
    Replaces volatile game_state dict with database persistence
    """
    
    def __init__(self, session: AsyncSession, embedding_service: Optional[EmbeddingService] = None):
        self.session = session
        self.embedding_service = embedding_service
    
    async def save_turn(
        self,
        player_id: int,
        turn_number: int,
        player_input: str,
        scene_description: str,
        action_result: Optional[str],
        location: str,
        npcs_present: List[int],
        world_time: str
    ) -> GameLog:
        """
        Save a game turn to database with optional embedding
        """
        # Generate embedding for semantic search
        embedding = None
        if self.embedding_service:
            # Combine context for better search
            context = f"{location}. {scene_description}"
            embedding = await self.embedding_service.generate_embedding(context)
        
        log = GameLog(
            player_id=player_id,
            turn_number=turn_number,
            player_input=player_input,
            scene_description=scene_description,
            action_result=action_result,
            location=location,
            npcs_present=npcs_present,
            world_time=world_time,
            embedding=embedding
        )
        
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log
    
    async def get_recent_turns(
        self, 
        player_id: int, 
        limit: int = 3
    ) -> List[GameLog]:
        """
        Get last N turns for a player (for context in Narrator)
        """
        statement = (
            select(GameLog)
            .where(GameLog.player_id == player_id)
            .order_by(desc(GameLog.turn_number))
            .limit(limit)
        )
        result = await self.session.execute(statement)
        logs = result.scalars().all()
        return list(reversed(logs))  # Chronological order
    
    async def get_turn_by_number(
        self, 
        player_id: int, 
        turn_number: int
    ) -> Optional[GameLog]:
        """Get specific turn"""
        statement = (
            select(GameLog)
            .where(GameLog.player_id == player_id)
            .where(GameLog.turn_number == turn_number)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
    
    async def get_turn_count(self, player_id: int) -> int:
        """Get total turns for a player"""
        statement = select(GameLog).where(GameLog.player_id == player_id)
        result = await self.session.execute(statement)
        return len(result.scalars().all())
    
    async def get_turns_by_location(
        self, 
        player_id: int, 
        location: str, 
        limit: int = 10
    ) -> List[GameLog]:
        """Get turns that happened in a specific location"""
        statement = (
            select(GameLog)
            .where(GameLog.player_id == player_id)
            .where(GameLog.location == location)
            .order_by(desc(GameLog.turn_number))
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()
    
    async def search_turns_semantic(
        self, 
        player_id: int, 
        query: str, 
        limit: int = 5
    ) -> List[GameLog]:
        """
        Semantic search using pgvector
        Find turns similar to query text
        """
        if not self.embedding_service:
            return []
        
        query_embedding = await self.embedding_service.generate_embedding(query)
        
        # pgvector cosine similarity search
        statement = (
            select(GameLog)
            .where(GameLog.player_id == player_id)
            .order_by(GameLog.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()
