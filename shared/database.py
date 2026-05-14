"""Shared async database engine factory.

Each service calls get_engine(database_url) once at startup.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def make_engine(database_url: str, debug: bool = False):
    return create_async_engine(
        database_url,
        echo=debug,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )


def make_session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
