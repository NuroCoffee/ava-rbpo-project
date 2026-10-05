from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError

from club_service import __version__
from club_service.api.errors import application_error_handler, database_error_handler
from club_service.api.router import api_router
from club_service.core.errors import ApplicationError
from club_service.core.settings import get_settings


def create_application() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=__version__,
        debug=settings.debug,
    )
    application.add_exception_handler(ApplicationError, application_error_handler)
    application.add_exception_handler(SQLAlchemyError, database_error_handler)
    application.include_router(api_router, prefix=settings.api_prefix)
    return application


app = create_application()
