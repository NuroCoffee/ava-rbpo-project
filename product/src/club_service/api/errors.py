import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from club_service.core.errors import ApplicationError

logger = logging.getLogger(__name__)


def application_error_handler(_: Request, error: ApplicationError) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if error.status_code == 401 else None
    return JSONResponse(
        status_code=error.status_code,
        content={"detail": error.detail},
        headers=headers,
    )


def database_error_handler(_: Request, error: SQLAlchemyError) -> JSONResponse:
    logger.error("Database operation failed: %s", type(error).__name__)
    return JSONResponse(
        status_code=503,
        content={"detail": "Database is unavailable"},
    )
