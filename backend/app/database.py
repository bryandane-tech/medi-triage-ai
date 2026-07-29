import asyncpg
from app.core.config import settings

async def create_db_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(
        dsn=settings.DATABASE_URL,
        min_size=settings.DB_MIN_POOL,
        max_size=settings.DB_MAX_POOL
    )
