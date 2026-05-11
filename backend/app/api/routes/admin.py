from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps_auth import require_admin
from app.api.ids import DbPathId
from app.constants import MAX_DB_INTEGER
from app.database import get_db
from app.models.entities import AuditLog, User
from app.schemas.audit import AuditLogRead
from app.schemas.auth import UserAdminRead, UserCreate
from app.services import audit_service, user_service


def _audit_to_read(log: AuditLog) -> AuditLogRead:
    return AuditLogRead(
        id=log.id,
        created_at=log.created_at,
        actor_username=log.actor.username if log.actor else None,
        action=log.action,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        warehouse_id=log.warehouse_id,
        detail=log.detail,
    )


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


@router.get("/users", response_model=list[UserAdminRead])
def list_users(
    db: Session = Depends(get_db),
    active_only: bool = False,
):
    return user_service.list_users_admin(db, active_only=active_only)


@router.post("/users", response_model=UserAdminRead, status_code=status.HTTP_201_CREATED)
def create_user_admin(
    payload: UserCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin),
):
    name = payload.username.strip()
    if not name:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Логин не может быть пустым")
    try:
        u = user_service.create_user(
            db,
            username=name,
            password=payload.password,
            role=payload.role,
        )
    except ValueError as e:
        if e.args and e.args[0] == "username_taken":
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Пользователь с таким логином уже есть",
            ) from e
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid") from e
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Пользователь с таким логином уже есть",
        ) from None
    audit_service.record(
        db,
        actor=actor,
        action="user.create",
        entity_type="user",
        entity_id=u.id,
        detail={"username": u.username, "role": u.role.value},
    )
    return u


@router.post("/users/{user_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user_admin(
    user_id: DbPathId,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin),
):
    if user_id == actor.id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Нельзя отключить свою учётную запись",
        )
    target = user_service.get_by_id(db, user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    snapshot = target.username
    try:
        user_service.deactivate_user(db, user_id)
    except ValueError as e:
        code = e.args[0] if e.args else ""
        if code == "already_inactive":
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Учётная запись уже отключена") from e
        if code == "sole_admin":
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Нельзя отключить последнего администратора",
            ) from e
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid") from e
    audit_service.record(
        db,
        actor=actor,
        action="user.deactivate",
        entity_type="user",
        entity_id=user_id,
        detail={"username": snapshot},
    )


@router.post("/users/{user_id}/activate", response_model=UserAdminRead)
def activate_user_admin(
    user_id: DbPathId,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin),
):
    target = user_service.get_by_id(db, user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    snapshot = target.username
    try:
        user_service.activate_user(db, user_id)
    except ValueError as e:
        code = e.args[0] if e.args else ""
        if code == "already_active":
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Учётная запись уже активна") from e
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid") from e
    u = user_service.get_by_id(db, user_id)
    assert u is not None
    audit_service.record(
        db,
        actor=actor,
        action="user.activate",
        entity_type="user",
        entity_id=user_id,
        detail={"username": snapshot},
    )
    return u


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_permanent_admin(
    user_id: DbPathId,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin),
):
    if user_id == actor.id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить свою учётную запись",
        )
    target = user_service.get_by_id(db, user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    snapshot = {"username": target.username, "role": target.role.value}
    try:
        user_service.delete_user_permanent(db, user_id)
    except ValueError as e:
        code = e.args[0] if e.args else ""
        if code == "sole_admin":
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Нельзя удалить последнего администратора",
            ) from e
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid") from e
    audit_service.record(
        db,
        actor=actor,
        action="user.delete",
        entity_type="user",
        entity_id=user_id,
        detail=snapshot,
    )


@router.get("/audit-log", response_model=list[AuditLogRead])
def get_audit_log(
    db: Session = Depends(get_db),
    warehouse_id: Annotated[int | None, Query(ge=1, le=MAX_DB_INTEGER)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    rows = audit_service.list_logs(db, warehouse_id=warehouse_id, limit=limit, offset=offset)
    return [_audit_to_read(r) for r in rows]
