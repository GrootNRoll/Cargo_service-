from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.entities import Warehouse, WarehouseMember
from app.schemas.warehouse import WarehouseCreate, WarehouseRead, WarehouseUpdate


def list_warehouses(db: Session) -> list[WarehouseRead]:
    rows = db.execute(
        select(Warehouse, func.count(WarehouseMember.id))
        .outerjoin(WarehouseMember, WarehouseMember.warehouse_id == Warehouse.id)
        .group_by(Warehouse.id)
        .order_by(Warehouse.id)
    ).all()
    return [
        WarehouseRead(
            id=w.id,
            name=w.name,
            address=w.address,
            member_count=int(cnt),
        )
        for w, cnt in rows
    ]


def get_warehouse(db: Session, warehouse_id: int) -> Warehouse | None:
    return db.get(Warehouse, warehouse_id)


def read_warehouse(db: Session, warehouse_id: int) -> WarehouseRead | None:
    w = get_warehouse(db, warehouse_id)
    if w is None:
        return None
    cnt = db.scalar(
        select(func.count())
        .select_from(WarehouseMember)
        .where(WarehouseMember.warehouse_id == warehouse_id)
    )
    return WarehouseRead(
        id=w.id,
        name=w.name,
        address=w.address,
        member_count=int(cnt or 0),
    )


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
