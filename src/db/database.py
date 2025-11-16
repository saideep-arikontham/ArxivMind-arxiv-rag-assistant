import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from src.db.models import Base

# Expect DATABASE_URL from Docker/Compose envs.
# Example: postgresql+asyncpg://user:pass@db:5432/arxivmind_db
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Make sure it's provided via Docker Compose/.env")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,  # healthier long-running connections
)

AsyncSessionLocal: sessionmaker[AsyncSession] = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def init_db() -> None:
    """Run DDL once on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
