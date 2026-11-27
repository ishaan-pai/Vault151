"""Response models for the health endpoint."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """What ``GET /health`` returns, whether or not the database answered."""

    status: Literal["ok", "degraded"]
    database: Literal["ok", "unreachable"]
