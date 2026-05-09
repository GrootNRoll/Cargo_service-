from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Product, StockItem, Warehouse
from app.schemas.stock import StockCreate, StockUpdate


def list_stock(
    db: Session,
    *,
    warehouse_id: int | None = None,
    product_id: int | None = None,
) -> list[StockItem]:
    q = select(StockItem).order_by(StockItem.id)
    if warehouse_id is not None:
        q = q.where(StockItem.warehouse_id == warehouse_id)
    if product_id is not None:
        q = q.where(StockItem.product_id == product_id)
    return list(db.scalars(q).all())


def get_stock_item(db: Session, stock_id: int) -> StockItem | None:
    return db.get(StockItem, stock_id)


def create_stock(db: Session, data: StockCreate) -> StockItem:
    if db.get(Warehouse, data.warehouse_id) is None:
        raise ValueError("warehouse_not_found")
    if db.get(Product, data.product_id) is None:
        raise ValueError("product_not_found")
    existing = db.scalars(
        select(StockItem).where(
            StockItem.warehouse_id == data.warehouse_id,
            StockItem.product_id == data.product_id,
        )
    ).first()
    if existing is not None:
        raise ValueError("duplicate_stock_row")
    row = StockItem(**data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_stock(db: Session, stock_id: int, data: StockUpdate) -> StockItem | None:
    row = db.get(StockItem, stock_id)
    if row is None:
        return None
    row.quantity = data.quantity
    db.commit()
    db.refresh(row)
    return row


def delete_stock(db: Session, stock_id: int) -> bool:
    row = db.get(StockItem, stock_id)
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True
