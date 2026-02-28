import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress
from datetime import datetime

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base, engine, get_db_session
from app.ingestion import ingestion_loop
from app.models import NewsAlert


class AlertResponse(BaseModel):
    id: int
    headline: str
    source: str
    url: str
    published_at: datetime
    is_breaking: bool


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    task = asyncio.create_task(ingestion_loop())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(title="Crisis Feed API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/alerts", response_model=list[AlertResponse])
async def list_alerts(
    session: AsyncSession = Depends(get_db_session),
) -> list[AlertResponse]:
    query = select(NewsAlert).order_by(desc(NewsAlert.published_at)).limit(100)
    rows = await session.execute(query)
    alerts = rows.scalars().all()

    return [
        AlertResponse(
            id=alert.id,
            headline=alert.headline,
            source=alert.source,
            url=alert.url,
            published_at=alert.published_at,
            is_breaking=alert.is_breaking,
        )
        for alert in alerts
    ]
