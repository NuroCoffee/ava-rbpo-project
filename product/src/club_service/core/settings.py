import os
from dataclasses import dataclass
from functools import lru_cache


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "AVA Club Service"
    app_env: str = "local"
    debug: bool = False
    api_prefix: str = "/api/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "AVA Club Service"),
        app_env=os.getenv("APP_ENV", "local"),
        debug=_as_bool(os.getenv("APP_DEBUG", "false")),
    )
