"""
Pytest configuration and fixtures for testing
"""
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import ASGITransport, AsyncClient
from typing import AsyncGenerator

from database.models import Base
from database.session import get_async_session
from main import app

# Test database URL (use SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def async_engine():
    """Create async engine for testing"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async session for testing"""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
async def client(async_session):
    """Create test client"""
    app.dependency_overrides[get_async_session] = lambda: async_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_merchant(async_session):
    """Create a test merchant"""
    from database.models.Merchant import Merchant

    merchant = Merchant(
        id="m_test_merchant",
        name="Test Merchant",
        email="test@merchant.com",
        is_verified=True
    )
    async_session.add(merchant)
    await async_session.commit()
    await async_session.refresh(merchant)

    return merchant


@pytest.fixture
async def test_user(async_session):
    """Create a test user"""
    from database.models.User import User
    from services import bcryptService

    hashed_password = await bcryptService.make_password("testpassword123")

    user = User(
        id="u_test001",
        email="test@user.com",
        name="Test User",
        password=hashed_password
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    return user


@pytest.fixture
async def test_wallet(async_session, test_merchant):
    """Create a test wallet"""
    from database.models.Wallet import Wallet

    wallet = Wallet(
        merchant_id=test_merchant.id,
        currency="NGN",
        mode="test",
        balance=10000.0,
        percentage_charge=1.5,
        flat_charge=100.0,
        payout_percentage_charge=1.0,
        payout_flat_charge=50.0,
        is_active=True
    )
    async_session.add(wallet)
    await async_session.commit()
    await async_session.refresh(wallet)

    return wallet


@pytest.fixture
async def test_customer(async_session, test_merchant):
    """Create a test customer"""
    from database.models.Customer import Customer

    customer = Customer(
        email="customer@test.com",
        name="Test Customer",
    )
    customer.merchants.append(test_merchant)
    async_session.add(customer)
    await async_session.commit()
    await async_session.refresh(customer)

    return customer
