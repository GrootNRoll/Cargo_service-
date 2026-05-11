from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.entities import User, Warehouse, WarehouseMember


def list_members(db: Session, warehouse_id: int) -> list[User]:
    if db.get(Warehouse, warehouse_id) is None:
        return []
    stmt = (
        select(User)
        .join(WarehouseMember, WarehouseMember.user_id == User.id)
        .where(WarehouseMember.warehouse_id == warehouse_id)
        .order_by(User.username)
    )
    return list(db.scalars(stmt).all())


def add_member(db: Session, warehouse_id: int, user_id: int) -> WarehouseMember | None:
    if db.get(Warehouse, warehouse_id) is None or db.get(User, user_id) is None:
        return None
    row = WarehouseMember(warehouse_id=warehouse_id, user_id=user_id)
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None
    db.refresh(row)
    return row


def remove_member(db: Session, warehouse_id: int, user_id: int) -> bool:
    row = db.scalars(
        select(WarehouseMember).where(
            WarehouseMember.warehouse_id == warehouse_id,
            WarehouseMember.user_id == user_id,
        )
    ).first()
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True
