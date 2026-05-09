def test_products_crud(client):
    r = client.get("/api/products")
    assert r.status_code == 200
    assert r.json() == []

    r = client.post("/api/products", json={"sku": "A-1", "name": "Товар 1", "unit": "шт"})
    assert r.status_code == 201
    pid = r.json()["id"]

    r = client.get(f"/api/products/{pid}")
    assert r.status_code == 200
    assert r.json()["sku"] == "A-1"

    r = client.patch("/api/products/999", json={"name": "x"})
    assert r.status_code == 404

    r = client.patch(f"/api/products/{pid}", json={"name": "Обновлено"})
    assert r.status_code == 200
    assert r.json()["name"] == "Обновлено"

    r = client.delete(f"/api/products/{pid}")
    assert r.status_code == 204


def test_warehouses_crud(client):
    r = client.post("/api/warehouses", json={"name": "Склад 1", "address": "Улица 1"})
    assert r.status_code == 201
    wid = r.json()["id"]

    r = client.get("/api/warehouses")
    assert len(r.json()) == 1

    r = client.patch(f"/api/warehouses/{wid}", json={"address": None})
    assert r.status_code == 200
    assert r.json()["address"] is None

    r = client.delete(f"/api/warehouses/{wid}")
    assert r.status_code == 204


def test_stock_crud(client):
    p = client.post("/api/products", json={"sku": "S-1", "name": "X", "unit": "шт"}).json()
    w = client.post("/api/warehouses", json={"name": "W1"}).json()

    r = client.post(
        "/api/stock",
        json={"warehouse_id": w["id"], "product_id": p["id"], "quantity": 5},
    )
    assert r.status_code == 201
    sid = r.json()["id"]
    assert r.json()["quantity"] == 5

    r = client.post(
        "/api/stock",
        json={"warehouse_id": w["id"], "product_id": p["id"], "quantity": 1},
    )
    assert r.status_code == 409

    r = client.patch(f"/api/stock/{sid}", json={"quantity": 10})
    assert r.status_code == 200
    assert r.json()["quantity"] == 10

    r = client.delete(f"/api/stock/{sid}")
    assert r.status_code == 204
