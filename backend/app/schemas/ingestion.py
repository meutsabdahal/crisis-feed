from __future__ import annotations

from pydantic import BaseModel, Field


class AlertIngestionRequest(BaseModel):
    severity_level: str = Field(min_length=1, max_length=20)
    region: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=5000)
    source: str = Field(min_length=1, max_length=255)


class IngestionEnqueueResponse(BaseModel):
    job_id: str
    queue: str
    status: str
