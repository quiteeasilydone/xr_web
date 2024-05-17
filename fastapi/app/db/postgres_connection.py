import asyncpg
import os


# postgresDB 연결
async def connect_db():
    conn = await asyncpg.connect(os.environ['DATABASE_URL'])
    return conn