import asyncpg
import os
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker

# postgresDB 연결
# async def connect_db():
#     conn = await asyncpg.connect(os.environ['DATABASE_URL'])
#     return conn


# sqlalchemy 설정
meta = MetaData()
# SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://jym:jym1234@localhost:5432/xrweb"
SQLALCHEMY_DATABASE_URL = os.environ['DATABASE_URL']
engine = create_async_engine(SQLALCHEMY_DATABASE_URL)


async_session = async_sessionmaker(engine, autocommit=False, autoflush=False)

# postgresDB 연결
async def connect_db() -> AsyncSession:
    async with engine.begin() as conn:
        await conn.run_sync(meta.create_all)
        
    db = async_session()
    try:
        yield db
    finally:
        await db.close()
