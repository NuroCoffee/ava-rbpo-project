import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from club_service.infrastructure.database import get_engine
from club_service.schemas.health import (
    HealthResponse,
    ReadinessFailureResponse,
    ReadinessResponse,
)

router = APIRouter(tags=["system"])
logger = logging.getLogger(__name__)


@router.get("/health/live", response_model=HealthResponse)
def liveness_check() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    responses={503: {"model": ReadinessFailureResponse}},
)
def readiness_check(
    engine: Annotated[Engine, Depends(get_engine)],
) -> ReadinessResponse | JSONResponse:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        logger.warning("Database readiness check failed: %s", error)
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "unavailable"},
        )

    return ReadinessResponse(
        status="ready",
        database="ok",
    )
