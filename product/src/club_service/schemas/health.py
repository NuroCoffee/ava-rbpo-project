from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ReadinessResponse(BaseModel):
    status: Literal["ready"]
    database: Literal["ok"]


class ReadinessFailureResponse(BaseModel):
    status: Literal["not_ready"]
    database: Literal["unavailable"]
