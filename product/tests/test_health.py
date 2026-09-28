import asyncio
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy.exc import SQLAlchemyError

from club_service.infrastructure.database import get_engine
from club_service.main import app


async def _async_request(path: str) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)


def _request(path: str) -> Response:
    return asyncio.run(_async_request(path))


@contextmanager
def _override_engine(engine: Any) -> Iterator[None]:
    app.dependency_overrides[get_engine] = lambda: engine
    try:
        yield
    finally:
        app.dependency_overrides.clear()


class _AvailableConnection:
    def __enter__(self) -> "_AvailableConnection":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def execute(self, _: object) -> None:
        return None


class _AvailableEngine:
    def connect(self) -> _AvailableConnection:
        return _AvailableConnection()


class _UnavailableEngine:
    def connect(self) -> None:
        raise SQLAlchemyError("database is unavailable")


def test_liveness_check() -> None:
    response = _request("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_check_when_database_is_available() -> None:
    with _override_engine(_AvailableEngine()):
        response = _request("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok"}


def test_readiness_check_when_database_is_unavailable() -> None:
    with _override_engine(_UnavailableEngine()):
        response = _request("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "database": "unavailable",
    }
