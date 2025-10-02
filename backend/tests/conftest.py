"""Pytest configuration and fixtures."""

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.db.models import Base, Firm, User


@pytest_asyncio.fixture
async def test_db():
    """Create a test database for each test."""
    # Use in-memory SQLite - must use StaticPool to share the connection
    from sqlalchemy.pool import StaticPool

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # Critical: shares single connection across all sessions
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        # Enable foreign keys for SQLite
        await conn.exec_driver_sql("PRAGMA foreign_keys=ON")
        await conn.run_sync(Base.metadata.create_all)

    # Create session maker
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create session and add test data
    async with async_session_maker() as session:
        # Create test firm and user
        firm = Firm(
            id="org_789",
            name="Test Firm",
        )
        session.add(firm)

        user = User(
            id="user_123",
            email="test@example.com",
            firm_id="org_789",
        )
        session.add(user)

        await session.commit()

        yield session

    await engine.dispose()


@pytest.fixture
def mock_current_user():
    """Mock authenticated user."""
    return {
        "user_id": "user_123",
        "session_id": "session_456",
        "email": "test@example.com",
        "org_id": "org_789",
        "org_role": "admin",
    }
