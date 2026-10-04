import asyncio
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from club_service.core.security import create_access_token, hash_password
from club_service.domain.enums import UserRole
from club_service.infrastructure.database import get_session
from club_service.infrastructure.models import Base, User
from club_service.main import app


@dataclass
class ApiClient:
    def request(self, method: str, path: str, **kwargs: Any) -> Response:
        async def send() -> Response:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.request(method, path, **kwargs)

        return asyncio.run(send())

    def get(self, path: str, **kwargs: Any) -> Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Response:
        return self.request("POST", path, **kwargs)


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_session() -> Iterator[Session]:
        with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        yield factory
    finally:
        app.dependency_overrides.pop(get_session, None)
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def api_client(session_factory: sessionmaker[Session]) -> ApiClient:
    return ApiClient()


@pytest.fixture
def user_factory(
    session_factory: sessionmaker[Session],
) -> Callable[[str, UserRole], User]:
    def create_user(email: str, role: UserRole = UserRole.CLIENT) -> User:
        with session_factory() as session:
            user = User(
                email=email,
                password_hash=hash_password("secure-password"),
                role=role,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    return create_user


@pytest.fixture
def auth_headers() -> Callable[[User], dict[str, str]]:
    def build_headers(user: User) -> dict[str, str]:
        return {"Authorization": f"Bearer {create_access_token(user.id)}"}

    return build_headers
