"""Админ: журнал аудита и участники складов."""

import uuid

from fastapi.testclient import TestClient

from app.api.deps_auth import get_current_user
from app.main import app
from app.models.entities import User, UserRole


def test_admin_users_and_audit(client: TestClient):
    r = client.get("/api/admin/users")
    assert r.status_code == 200
    usernames = {u["username"] for u in r.json()}
    assert "admin" in usernames
    first = r.json()[0]
    assert "is_active" in first

    r = client.get("/api/admin/audit-log")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_admin_create_user(client: TestClient):
    login = f"nuser_{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/admin/users",
        json={"username": login, "password": "secret12", "role": "worker"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["username"] == login
    assert body["role"] == "worker"
    assert body["is_active"] is True

    r = client.post(
        "/api/admin/users",
        json={"username": login, "password": "otherpass1", "role": "worker"},
    )
    assert r.status_code == 409

    r = client.get("/api/admin/users?active_only=true")
    assert r.status_code == 200
    assert login in {u["username"] for u in r.json()}


def test_admin_deactivate_activate_cycle(client: TestClient):
    login = f"off_{uuid.uuid4().hex[:8]}"
    rid = client.post(
        "/api/admin/users",
        json={"username": login, "password": "secret12", "role": "worker"},
    ).json()["id"]

    r = client.post(f"/api/admin/users/{rid}/deactivate")
    assert r.status_code == 204
    row = next(x for x in client.get("/api/admin/users").json() if x["id"] == rid)
    assert row["is_active"] is False
    assert login not in {u["username"] for u in client.get("/api/admin/users?active_only=true").json()}

    r = client.post(f"/api/admin/users/{rid}/deactivate")
    assert r.status_code == 409

    r = client.post(f"/api/admin/users/{rid}/activate")
    assert r.status_code == 200
    assert r.json()["is_active"] is True

    r = client.post(f"/api/admin/users/{rid}/activate")
    assert r.status_code == 409

    assert client.post("/api/admin/users/1/deactivate").status_code == 400


def test_admin_permanent_delete(client: TestClient):
    login = f"del_{uuid.uuid4().hex[:8]}"
    rid = client.post(
        "/api/admin/users",
        json={"username": login, "password": "secret12", "role": "worker"},
    ).json()["id"]
    assert client.delete(f"/api/admin/users/{rid}").status_code == 204
    ids = {u["id"] for u in client.get("/api/admin/users").json()}
    assert rid not in ids


def test_sole_active_admin_cannot_be_deactivated():
    fake = User(
        id=99_999,
        username="test_actor_admin",
        password_hash="x",
        role=UserRole.admin,
        is_active=True,
    )
    app.dependency_overrides[get_current_user] = lambda: fake
    try:
        with TestClient(app) as c:
            lst = c.get("/api/admin/users").json()
            default_admin_id = next(u["id"] for u in lst if u["username"] == "admin" and u["is_active"])
            extra = c.post(
                "/api/admin/users",
                json={"username": f"adm_extra_{uuid.uuid4().hex[:8]}", "password": "secret12", "role": "admin"},
            ).json()["id"]
            assert c.post(f"/api/admin/users/{extra}/deactivate").status_code == 204
            assert c.post(f"/api/admin/users/{default_admin_id}/deactivate").status_code == 409
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_cannot_delete_self(client: TestClient):
    assert client.delete("/api/admin/users/1").status_code == 400


def test_warehouse_members_flow(client: TestClient):
    name = f"Уч-Members-{uuid.uuid4().hex[:6]}"
    w = client.post("/api/warehouses", json={"name": name, "address": None}).json()
    wid = w["id"]

    r = client.get(f"/api/warehouses/{wid}/members")
    assert r.status_code == 200
    assert r.json() == []

    r = client.get("/api/admin/users")
    worker = next(u for u in r.json() if u["username"] == "worker")

    r = client.post(f"/api/warehouses/{wid}/members", json={"user_id": worker["id"]})
    assert r.status_code == 201
    assert r.json()["username"] == "worker"

    r = client.get("/api/warehouses")
    row = next(x for x in r.json() if x["id"] == wid)
    assert row["member_count"] == 1

    r = client.delete(f"/api/warehouses/{wid}/members/{worker['id']}")
    assert r.status_code == 204

    r = client.get(f"/api/warehouses/{wid}/members")
    assert r.json() == []


def test_worker_cannot_admin_audit_or_members():
    app.dependency_overrides.pop(get_current_user, None)
    try:
        with TestClient(app) as c:
            admin_tok = c.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).json()[
                "access_token"
            ]
            ah = {"Authorization": f"Bearer {admin_tok}"}
            w = c.post("/api/warehouses", json={"name": f"RBAC-M-{uuid.uuid4().hex[:6]}", "address": None}, headers=ah).json()
            wid = w["id"]

            wt = c.post("/api/auth/login", json={"username": "worker", "password": "worker123"}).json()[
                "access_token"
            ]
            wh = {"Authorization": f"Bearer {wt}"}
            assert c.get("/api/admin/users", headers=wh).status_code == 403
            assert (
                c.post(
                    "/api/admin/users",
                    json={"username": "x", "password": "secret12"},
                    headers=wh,
                ).status_code
                == 403
            )
            assert c.delete("/api/admin/users/1", headers=wh).status_code == 403
            assert c.post("/api/admin/users/1/deactivate", headers=wh).status_code == 403
            assert c.post("/api/admin/users/1/activate", headers=wh).status_code == 403
            assert c.get("/api/admin/audit-log", headers=wh).status_code == 403
            assert c.get(f"/api/warehouses/{wid}/members", headers=wh).status_code == 403
    finally:
        pass


def test_audit_after_product_mutation(client: TestClient):
    sku = f"AUD-{uuid.uuid4().hex[:8]}"
    r = client.post("/api/products", json={"sku": sku, "name": "A", "unit": "шт"})
    assert r.status_code == 201
    pid = r.json()["id"]

    r = client.get("/api/admin/audit-log?limit=50")
    assert r.status_code == 200
    acts = [x["action"] for x in r.json()]
    assert "product.create" in acts

    client.delete(f"/api/products/{pid}")

    r = client.get("/api/admin/audit-log?limit=80")
    acts = [x["action"] for x in r.json()]
    assert "product.delete" in acts
