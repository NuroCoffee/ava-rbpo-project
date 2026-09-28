from fastapi import FastAPI

from club_service import __version__
from club_service.api.router import api_router
from club_service.core.settings import get_settings


def create_application() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=__version__,
        debug=settings.debug,
    )
    application.include_router(api_router, prefix=settings.api_prefix)
    return application


app = create_application()
