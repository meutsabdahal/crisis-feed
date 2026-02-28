from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NewsAlert(Base):
    __tablename__ = "news_alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    headline: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(
        String(1024), unique=True, index=True, nullable=False
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), index=True, nullable=False
    )
    is_breaking: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
