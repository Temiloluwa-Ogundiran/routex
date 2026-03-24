from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
import settings

DATABASE_URL = settings.DB_URL

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True, pool_pre_ping=True)

# Create async sessionmaker
async_session = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

# Dependency-style session getter
async def get_async_session():
    async with async_session() as session:
        yield session
