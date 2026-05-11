from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.entities import AuditLog, User


def record(
    db: Session,
    *,
    actor: User,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    warehouse_id: int | None = None,
    detail: dict | None = None,
) -> None:
    row = AuditLog(
        actor_id=actor.id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        warehouse_id=warehouse_id,
        detail=detail,
    )
    db.add(row)
    db.commit()


def list_logs(
    db: Session,
    *,
    warehouse_id: int | None,
    limit: int,
    offset: int,
) -> list[AuditLog]:
    q = select(AuditLog).options(joinedload(AuditLog.actor)).order_by(AuditLog.id.desc())
    if warehouse_id is not None:
        q = q.where(AuditLog.warehouse_id == warehouse_id)
    return list(db.scalars(q.offset(offset).limit(limit)).unique().all())
