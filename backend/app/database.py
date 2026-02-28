from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "sqlite+aiosqlite:///./crisis_feed.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"timeout": 30},
)
SessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    async with engine.begin() as connection:
        await connection.execute(text("PRAGMA journal_mode=WAL"))
        await connection.execute(text("PRAGMA synchronous=NORMAL"))
        await connection.run_sync(Base.metadata.create_all)

        columns = await connection.execute(text("PRAGMA table_info(news_alerts)"))
        column_names = {str(row[1]) for row in columns.fetchall()}
        if "description" not in column_names:
            await connection.execute(text("ALTER TABLE news_alerts ADD COLUMN description VARCHAR(4000)"))


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
