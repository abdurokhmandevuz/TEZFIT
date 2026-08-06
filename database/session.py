import os
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from config import settings
from database.base import Base

db_url = settings.DATABASE_URL
if db_url.startswith("sqlite://") and not db_url.startswith("sqlite+aiosqlite://"):
    db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")
elif db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://")
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

# Ensure directory exists for SQLite files (including Railway Volumes)
if "sqlite" in db_url:
    try:
        db_path = db_url.split(":///")[-1]
        if "/" in db_path:
            db_dir = os.path.dirname(db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
    except Exception:
        pass

engine = create_async_engine(db_url, echo=False, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    columns_to_add = [
        ("first_name", "VARCHAR(255)"),
        ("last_name", "VARCHAR(255)"),
        ("phone_number", "VARCHAR(100)"),
        ("photo_url", "VARCHAR(512)"),
        ("dob", "VARCHAR(100) DEFAULT '2003-05-21'"),
        ("points", "INTEGER DEFAULT 100"),
        ("level", "INTEGER DEFAULT 1"),
        ("target_weight_kg", "FLOAT DEFAULT 65.0"),
        ("activity_level", "VARCHAR(100) DEFAULT 'Lightly active'"),
        ("diet_preference", "VARCHAR(100) DEFAULT 'No preference'"),
    ]
    for col_name, col_type in columns_to_add:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
        except Exception:
            pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
