"""Начальное наполнение примера (если ещё нет товаров)."""

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import (
    Order,
    OrderLine,
    OrderStatus,
    Product,
    StockItem,
    Warehouse,
)
from app.services.order_service import transition_order


def seed_demo_if_empty(db: Session) -> bool:
    cnt = db.scalar(select(func.count()).select_from(Product))
    if cnt:
        return False

    wh_north = Warehouse(name="Склад Север", address="Москва, ул. Складская, 1")
    wh_south = Warehouse(name="Склад Юг", address="Краснодар, промзона «Юг»")
    db.add_all([wh_north, wh_south])
    db.flush()

    p_nbk = Product(sku="NBK-01", name='Ноутбук 15"', unit="шт")
    p_mouse = Product(sku="MSE-02", name="Мышь беспроводная", unit="шт")
    p_cable = Product(sku="CBL-03", name="Кабель USB-C, 2 м", unit="шт")
    db.add_all([p_nbk, p_mouse, p_cable])
    db.flush()

    db.add_all(
        [
            StockItem(warehouse_id=wh_north.id, product_id=p_nbk.id, quantity=15),
            StockItem(warehouse_id=wh_north.id, product_id=p_mouse.id, quantity=240),
            StockItem(warehouse_id=wh_north.id, product_id=p_cable.id, quantity=500),
            StockItem(warehouse_id=wh_south.id, product_id=p_nbk.id, quantity=8),
            StockItem(warehouse_id=wh_south.id, product_id=p_mouse.id, quantity=60),
        ]
    )

    o_draft = Order(warehouse_id=wh_north.id, status=OrderStatus.draft)
    o_draft.lines.extend(
        [
            OrderLine(product_id=p_nbk.id, quantity=3, unit_price=Decimal("54990.00")),
            OrderLine(product_id=p_mouse.id, quantity=10, unit_price=Decimal("1290.00")),
        ]
    )
    db.add(o_draft)

    o_flow = Order(warehouse_id=wh_north.id, status=OrderStatus.draft)
    o_flow.lines.append(
        OrderLine(product_id=p_nbk.id, quantity=2, unit_price=Decimal("54990.00")),
    )
    db.add(o_flow)

    o_cancel = Order(warehouse_id=wh_south.id, status=OrderStatus.draft)
    o_cancel.lines.append(
        OrderLine(product_id=p_cable.id, quantity=100, unit_price=Decimal("450.00")),
    )
    db.add(o_cancel)

    db.flush()
    flow_id = o_flow.id
    cancel_id = o_cancel.id

    db.commit()

    transition_order(db, flow_id, OrderStatus.confirmed)
    transition_order(db, flow_id, OrderStatus.fulfilled)
    transition_order(db, cancel_id, OrderStatus.cancelled)

    return True
