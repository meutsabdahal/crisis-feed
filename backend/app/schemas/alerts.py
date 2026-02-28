from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AlertCreate(BaseModel):
    severity_level: str = Field(min_length=1, max_length=20)
    region: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=5000)
    source: str = Field(min_length=1, max_length=255)


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    severity_level: str
    region: str
    description: str
    timestamp: datetime
    source: str
