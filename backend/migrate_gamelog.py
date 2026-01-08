"""
Migration: Add GameLog table for persistent turn history
Run this after starting the database
"""
import asyncio
from sqlmodel import SQLModel
from app.database.db_connection import engine
from app.database.models.logs import GameLog
from app.database.models.player import Player  # Import Player for foreign key


async def migrate_add_gamelog():
    print("Creating GameLog table...")
    async with engine.begin() as conn:
        # Create all tables (will skip existing ones)
        await conn.run_sync(SQLModel.metadata.create_all)
    print("✅ GameLog table created successfully!")


if __name__ == "__main__":
    asyncio.run(migrate_add_gamelog())
