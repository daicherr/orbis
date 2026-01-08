# -*- coding: utf-8 -*-
import asyncio
import asyncpg

async def migrate():
    conn = await asyncpg.connect(
        host='localhost',
        port=5433,
        user='postgres',
        password='admin',
        database='rpg_cultivo'
    )
    await conn.execute('ALTER TABLE player ADD COLUMN IF NOT EXISTS kill_count INTEGER DEFAULT 0')
    await conn.execute("ALTER TABLE player ADD COLUMN IF NOT EXISTS kill_history JSON DEFAULT '[]'::json")
    print('Colunas kill_count e kill_history adicionadas')
    await conn.close()

asyncio.run(migrate())
