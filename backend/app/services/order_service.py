from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.entities import Order, OrderLine, OrderStatus, Product, StockItem, Warehouse
from app.schemas.order import OrderCreate

_ALLOWED: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.draft: {OrderStatus.confirmed, OrderStatus.cancelled},
    OrderStatus.confirmed: {OrderStatus.fulfilled, OrderStatus.cancelled},
    OrderStatus.fulfilled: set(),
    OrderStatus.cancelled: set(),
}


def list_orders(db: Session) -> list[Order]:
    return list(
        db.scalars(select(Order).options(selectinload(Order.lines)).order_by(Order.id.desc())).all()
    )


def get_order(db: Session, order_id: int) -> Order | None:
    return db.scalars(
        select(Order).where(Order.id == order_id).options(selectinload(Order.lines))
    ).first()


def create_order(db: Session, data: OrderCreate) -> Order:
    if db.get(Warehouse, data.warehouse_id) is None:
        raise ValueError("warehouse_not_found")
    order = Order(warehouse_id=data.warehouse_id, status=data.status)
    for line in data.lines:
        if db.get(Product, line.product_id) is None:
            raise ValueError("product_not_found")
        order.lines.append(
            OrderLine(
                product_id=line.product_id,
                quantity=line.quantity,
                unit_price=line.unit_price,
            )
        )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def transition_order(
    db: Session, order_id: int, to_status: OrderStatus
) -> tuple[Order | None, str | None]:
    order = get_order(db, order_id)
    if order is None:
        return None, "not_found"
    allowed = _ALLOWED.get(order.status, set())
    if to_status not in allowed:
        return None, "invalid_transition"
    if to_status == OrderStatus.fulfilled:
        err = _deduct_stock_for_order(db, order)
        if err:
            return None, err
    order.status = to_status
    db.commit()
    db.refresh(order)
    return order, None


def _deduct_stock_for_order(db: Session, order: Order) -> str | None:
    wh_id = order.warehouse_id
    for line in order.lines:
        stock = db.scalars(
            select(StockItem).where(
                StockItem.warehouse_id == wh_id,
                StockItem.product_id == line.product_id,
            )
        ).first()
        if stock is None or stock.quantity < line.quantity:
            return "insufficient_stock"
    for line in order.lines:
        stock = db.scalars(
            select(StockItem).where(
                StockItem.warehouse_id == wh_id,
                StockItem.product_id == line.product_id,
            )
        ).first()
        assert stock is not None
        stock.quantity -= line.quantity
    return None


def delete_order(db: Session, order_id: int) -> bool:
    order = get_order(db, order_id)
    if order is None:
        return False
    if order.status not in (OrderStatus.draft, OrderStatus.cancelled):
        raise ValueError("order_not_deletable")
    db.delete(order)
    db.commit()
    return True
