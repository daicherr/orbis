"""Verifica logs brutos no banco"""
import asyncio
from sqlmodel import select
from app.main import get_session
from app.database.models.logs import GameLog

async def main():
    async for session in get_session():
        result = await session.execute(
            select(GameLog).where(GameLog.player_id == 18).order_by(GameLog.turn_number)
        )
        logs = result.scalars().all()
        print(f"Total logs para player 18: {len(logs)}")
        for log in logs:
            print(f"\n=== TURNO {log.turn_number} ===")
            print(f"ID: {log.id}")
            print(f"player_input: {repr(log.player_input)[:100]}")
            scene_desc = log.scene_description
            if scene_desc:
                print(f"scene_description: {repr(scene_desc)[:300]}...")
            else:
                print("scene_description: NONE/NULL")
            if log.action_result:
                print(f"action_result: {repr(log.action_result)[:150]}...")
            else:
                print("action_result: NONE/NULL")
            print(f"world_time: {log.world_time}")
        break

asyncio.run(main())
