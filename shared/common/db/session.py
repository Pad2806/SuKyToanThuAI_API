from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from common.config.settings import get_settings

settings = get_settings()


def _engine_options(settings):
    if settings.database_pool_size <= 0:
        return {"pool_pre_ping": True, "poolclass": NullPool}
    return {
        "pool_pre_ping": True,
        "pool_size": settings.database_pool_size,
        "max_overflow": settings.database_max_overflow,
        "pool_timeout": settings.database_pool_timeout,
        "pool_recycle": settings.database_pool_recycle_seconds,
    }


engine = create_async_engine(settings.database_url, **_engine_options(settings))
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
