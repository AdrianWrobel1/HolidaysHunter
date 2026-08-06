"""Pytest fixtures for HolidaysHunter test suite."""

import pytest_asyncio
from app.database.base import Base
from app.database.session import async_session_factory, engine
import app.models  # Ensure all models are registered in Base.metadata


@pytest_asyncio.fixture
async def db_session():
    """Yield an async database session connected to configured DB."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        yield session
        await session.commit()
