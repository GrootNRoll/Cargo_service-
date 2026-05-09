from fastapi.testclient import TestClient

from app.api.deps_auth import get_current_user
from app.main import app


def test_login_admin():
    app.dependency_overrides.pop(get_current_user, None)
    with TestClient(app) as c:
        r = c.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        assert r.status_code == 200
        body = r.json()
        assert body["token_type"] == "bearer"
        assert body["user"]["username"] == "admin"
        assert body["user"]["role"] == "admin"
        assert len(body["access_token"]) > 10


def test_login_invalid_password():
    app.dependency_overrides.pop(get_current_user, None)
    with TestClient(app) as c:
        r = c.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
        assert r.status_code == 401


def test_products_without_token():
    app.dependency_overrides.pop(get_current_user, None)
    with TestClient(app) as c:
        r = c.get("/api/products")
        assert r.status_code == 401


def test_worker_cannot_mutate_warehouse():
    app.dependency_overrides.pop(get_current_user, None)
    with TestClient(app) as c:
        tok = c.post("/api/auth/login", json={"username": "worker", "password": "worker123"}).json()[
            "access_token"
        ]
        hdr = {"Authorization": f"Bearer {tok}"}
        assert (
            c.post(
                "/api/warehouses",
                json={"name": "Новый склад RBAC"},
                headers=hdr,
            ).status_code
            == 403
        )
        assert c.get("/api/warehouses", headers=hdr).status_code == 200
