from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class APIError(BaseModel):
    detail: str


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message: str
