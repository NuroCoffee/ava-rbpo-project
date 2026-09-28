from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from club_service.core.settings import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_timeout=3,
        connect_args={"connect_timeout": 3},
    )
