import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from app.core import settings
from app.db import engine as app_engine
from app.main import app
from app.db import init_db


@pytest.fixture(autouse=True)
def reset_db():
    SQLModel.metadata.drop_all(app_engine)
    SQLModel.metadata.create_all(app_engine)
    yield
    SQLModel.metadata.drop_all(app_engine)
    SQLModel.metadata.create_all(app_engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_refresh_token_flow_and_profile_management(client):
    register = client.post("/auth/register", json={"username": "alice", "password": "StrongPass123!", "email": "alice@example.com"})
    assert register.status_code == 200

    login = client.post("/auth/token", data={"username": "alice", "password": "StrongPass123!"})
    assert login.status_code == 200
    payload = login.json()
    assert "access_token" in payload
    assert "refresh_token" in payload

    refresh = client.post("/auth/refresh", json={"refresh_token": payload["refresh_token"]})
    assert refresh.status_code == 200
    refreshed = refresh.json()
    assert refreshed["access_token"]
    assert refreshed["refresh_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {payload['access_token']}"})
    assert me.status_code == 200

    profile = client.patch(
        "/auth/me",
        json={"email": "new@example.com"},
        headers={"Authorization": f"Bearer {payload['access_token']}"},
    )
    assert profile.status_code == 200
    assert profile.json()["email"] == "new@example.com"

    password_change = client.post(
        "/auth/change-password",
        json={"current_password": "StrongPass123!", "new_password": "EvenStronger123!"},
        headers={"Authorization": f"Bearer {payload['access_token']}"},
    )
    assert password_change.status_code == 200


def test_password_reset_and_admin_access(client):
    client.post("/auth/register", json={"username": "bob", "password": "StrongPass123!", "email": "bob@example.com"})

    forgot = client.post("/auth/forgot-password", json={"email": "bob@example.com"})
    assert forgot.status_code == 200

    reset = client.post("/auth/reset-password", json={"token": "invalid-token", "new_password": "NewPass123!"})
    assert reset.status_code == 400

    admin_login = client.post("/auth/token", data={"username": "bob", "password": "StrongPass123!"})
    assert admin_login.status_code == 200
    access_token = admin_login.json()["access_token"]

    admin_users = client.get("/admin/users", headers={"Authorization": f"Bearer {access_token}"})
    assert admin_users.status_code == 403
