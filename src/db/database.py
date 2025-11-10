from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from src.db.models import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://arxivmind_user:arxivmind_password@localhost:5432/arxivmind_db")

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,   # avoids post-commit lazy loads
    autoflush=False,
    autocommit=False,
)

async def init_db() -> None:
    async with engine.begin() as conn:
        # run sync DDL in the async engine
        await conn.run_sync(Base.metadata.create_all)
