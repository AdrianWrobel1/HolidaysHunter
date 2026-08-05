"""Pytest fixtures for HolidaysHunter test suite."""

import pytest_asyncio
from app.database.session import async_session_factory


@pytest_asyncio.fixture
async def db_session():
    """Yield an async database session connected to configured DB."""
    from app.database.session import engine
    async with async_session_factory() as session:
        yield session
    await engine.dispose()

