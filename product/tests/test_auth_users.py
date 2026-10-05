from collections.abc import Callable

from club_service.domain.enums import UserRole
from club_service.infrastructure.models import User
from tests.conftest import ApiClient


def test_successful_registration(api_client: ApiClient) -> None:
    response = api_client.post(
        "/api/v1/auth/register",
        json={"email": "Client@Example.com", "password": "secure-password"},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "client@example.com"
    assert response.json()["role"] == "CLIENT"
    assert "password" not in response.json()
    assert "password_hash" not in response.json()


def test_duplicate_email_is_rejected(api_client: ApiClient) -> None:
    payload = {"email": "client@example.com", "password": "secure-password"}
    assert api_client.post("/api/v1/auth/register", json=payload).status_code == 201

    response = api_client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 409


def test_registration_cannot_set_role(api_client: ApiClient) -> None:
    response = api_client.post(
        "/api/v1/auth/register",
        json={
            "email": "client@example.com",
            "password": "secure-password",
            "role": "ADMIN",
        },
    )

    assert response.status_code == 422


def test_successful_login_and_current_user(api_client: ApiClient) -> None:
    api_client.post(
        "/api/v1/auth/register",
        json={"email": "client@example.com", "password": "secure-password"},
    )

    login = api_client.post(
        "/api/v1/auth/login",
        json={"email": "client@example.com", "password": "secure-password"},
    )
    token = login.json()["access_token"]
    current_user = api_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"
    assert current_user.status_code == 200
    assert current_user.json()["email"] == "client@example.com"
    assert "password_hash" not in current_user.json()


def test_wrong_password_is_rejected(api_client: ApiClient) -> None:
    api_client.post(
        "/api/v1/auth/register",
        json={"email": "client@example.com", "password": "secure-password"},
    )

    response = api_client.post(
        "/api/v1/auth/login",
        json={"email": "client@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_protected_endpoint_requires_token(api_client: ApiClient) -> None:
    assert api_client.get("/api/v1/users/me").status_code == 401


def test_client_cannot_access_another_user_via_employee_api(
    api_client: ApiClient,
    user_factory: Callable[[str, UserRole], User],
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    client_a = user_factory("a@example.com", UserRole.CLIENT)
    client_b = user_factory("b@example.com", UserRole.CLIENT)

    own_response = api_client.get("/api/v1/users/me", headers=auth_headers(client_a))
    other_response = api_client.get(
        f"/api/v1/users/{client_b.id}",
        headers=auth_headers(client_a),
    )

    assert own_response.status_code == 200
    assert own_response.json()["id"] == client_a.id
    assert other_response.status_code == 403


def test_employee_can_view_client_without_password_hash(
    api_client: ApiClient,
    user_factory: Callable[[str, UserRole], User],
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    employee = user_factory("employee@example.com", UserRole.EMPLOYEE)
    client = user_factory("client@example.com", UserRole.CLIENT)

    response = api_client.get(
        f"/api/v1/users/{client.id}",
        headers=auth_headers(employee),
    )

    assert response.status_code == 200
    assert "password_hash" not in response.json()
