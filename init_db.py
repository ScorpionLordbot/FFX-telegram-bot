import os
import asyncio
import asyncpg

DATABASE_URL = os.environ['DATABASE_URL']

async def create_tables():
    conn = await asyncpg.connect(DATABASE_URL)

    # Example table for storing messages with intervals
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            interval_seconds INTEGER NOT NULL,
            message_text TEXT NOT NULL
        );
    """)

    print("✅ Tables created successfully!")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(create_tables())
