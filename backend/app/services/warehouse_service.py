from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.entities import Warehouse
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate


def list_warehouses(db: Session) -> list[Warehouse]:
    return list(db.scalars(select(Warehouse).order_by(Warehouse.id)).all())


def get_warehouse(db: Session, warehouse_id: int) -> Warehouse | None:
    return db.get(Warehouse, warehouse_id)


def create_warehouse(db: Session, data: WarehouseCreate) -> Warehouse:
    warehouse = Warehouse(**data.model_dump())
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return warehouse


def update_warehouse(db: Session, warehouse_id: int, data: WarehouseUpdate) -> Warehouse | None:
    warehouse = db.get(Warehouse, warehouse_id)
    if warehouse is None:
        return None
    patch = data.model_dump(exclude_unset=True)
    for key, value in patch.items():
        if value is None and key == "name":
            continue
        setattr(warehouse, key, value)
    db.commit()
    db.refresh(warehouse)
    return warehouse


def delete_warehouse(db: Session, warehouse_id: int) -> bool:
    warehouse = db.get(Warehouse, warehouse_id)
    if warehouse is None:
        return False
    try:
        db.delete(warehouse)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("warehouse_in_use") from None
    return True
