def test_order_lifecycle_and_stock_deduction(client):
    p = client.post("/api/products", json={"sku": "O-1", "name": "Товар заказа", "unit": "шт"}).json()
    w = client.post("/api/warehouses", json={"name": "Склад заказов"}).json()
    client.post(
        "/api/stock",
        json={"warehouse_id": w["id"], "product_id": p["id"], "quantity": 3},
    )

    r = client.post(
        "/api/orders",
        json={
            "warehouse_id": w["id"],
            "status": "draft",
            "lines": [{"product_id": p["id"], "quantity": 2, "unit_price": "150.00"}],
        },
    )
    assert r.status_code == 201
    order = r.json()
    oid = order["id"]

    r = client.post(f"/api/orders/{oid}/transition", json={"to_status": "confirmed"})
    assert r.status_code == 200

    r = client.post(f"/api/orders/{oid}/transition", json={"to_status": "fulfilled"})
    assert r.status_code == 200

    stock = client.get("/api/stock").json()
    assert stock[0]["quantity"] == 1

    r = client.post(
        "/api/orders",
        json={
            "warehouse_id": w["id"],
            "lines": [{"product_id": p["id"], "quantity": 5, "unit_price": "1"}],
        },
    )
    oid2 = r.json()["id"]
    client.post(f"/api/orders/{oid2}/transition", json={"to_status": "confirmed"})
    r = client.post(f"/api/orders/{oid2}/transition", json={"to_status": "fulfilled"})
    assert r.status_code == 409


def test_order_delete_draft_only(client):
    p = client.post("/api/products", json={"sku": "D-1", "name": "D", "unit": "шт"}).json()
    w = client.post("/api/warehouses", json={"name": "W-d"}).json()
    r = client.post(
        "/api/orders",
        json={"warehouse_id": w["id"], "lines": [{"product_id": p["id"], "quantity": 1, "unit_price": "0"}]},
    )
    oid = r.json()["id"]

    assert client.delete(f"/api/orders/{oid}").status_code == 204

    r = client.post(
        "/api/orders",
        json={"warehouse_id": w["id"], "lines": [{"product_id": p["id"], "quantity": 1, "unit_price": "0"}]},
    )
    oid = r.json()["id"]
    client.post(f"/api/orders/{oid}/transition", json={"to_status": "confirmed"})
    assert client.delete(f"/api/orders/{oid}").status_code == 409
