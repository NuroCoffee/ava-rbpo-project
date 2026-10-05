import os
from dataclasses import dataclass, field
from functools import lru_cache


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "AVA Club Service"
    app_env: str = "local"
    debug: bool = False
    api_prefix: str = "/api/v1"
    database_url: str = field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/ava_club",
        repr=False,
    )
    jwt_secret_key: str = field(
        default="dev-only-change-me-32-characters-minimum",
        repr=False,
    )
    jwt_access_token_ttl_minutes: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "AVA Club Service"),
        app_env=os.getenv("APP_ENV", "local"),
        debug=_as_bool(os.getenv("APP_DEBUG", "false")),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://postgres:postgres@localhost:5432/ava_club",
        ),
        jwt_secret_key=os.getenv(
            "JWT_SECRET_KEY",
            "dev-only-change-me-32-characters-minimum",
        ),
        jwt_access_token_ttl_minutes=int(os.getenv("JWT_ACCESS_TOKEN_TTL_MINUTES", "30")),
    )
