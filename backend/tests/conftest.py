import pytest_asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models import Base


TEST_DATABASE_URL = (
    "postgresql+asyncpg://tracker:tracker@localhost:5433/geo_tracker_test"
)


@pytest_asyncio.fixture
async def db_session():
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestSessionFactory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with TestSessionFactory() as session:
        await session.execute(
            text("TRUNCATE TABLE entities RESTART IDENTITY CASCADE")
        )
        await session.commit()

        yield session

    await test_engine.dispose()