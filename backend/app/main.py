import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress
from datetime import datetime

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session, init_db
from app.ingestion import ingestion_loop
from app.models import NewsAlert


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    headline: str
    description: str | None
    source: str
    url: str
    published_at: datetime
    is_breaking: bool


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()

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
    try:
        query = select(NewsAlert).order_by(desc(NewsAlert.published_at)).limit(100)
        rows = await session.execute(query)
        alerts = rows.scalars().all()
    except SQLAlchemyError:
        return []

    return [AlertResponse.model_validate(alert) for alert in alerts]
