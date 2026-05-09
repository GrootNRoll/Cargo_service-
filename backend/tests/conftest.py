import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["CORS_ORIGINS"] = "http://testserver"
os.environ["SEED_DEMO_DATA"] = "false"

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.api.deps_auth import get_current_user
from app.main import app
from app.models.entities import User, UserRole


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    fake = User(
        id=1,
        username="test_admin",
        password_hash="x",
        role=UserRole.admin,
        is_active=True,
    )
    app.dependency_overrides[get_current_user] = lambda: fake
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture()
def client_worker(client: TestClient) -> Generator[TestClient, None, None]:
    fake = User(
        id=2,
        username="test_worker",
        password_hash="x",
        role=UserRole.worker,
        is_active=True,
    )
    app.dependency_overrides[get_current_user] = lambda: fake
    try:
        yield client
    finally:
        app.dependency_overrides.pop(get_current_user, None)
