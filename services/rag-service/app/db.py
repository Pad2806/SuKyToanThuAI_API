"""RAG service DB session — schema: rag."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import config
from shared.database import Base, make_engine, make_session_factory

engine = make_engine(config.DATABASE_URL, config.DEBUG)
AsyncSessionLocal = make_session_factory(engine)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
