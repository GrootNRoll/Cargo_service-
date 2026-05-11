from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps_auth import get_current_user, require_admin
from app.api.ids import DbPathId
from app.database import get_db
from app.models.entities import User
from app.schemas.audit import WarehouseMemberAdd
from app.schemas.auth import UserPublic
from app.schemas.warehouse import WarehouseCreate, WarehouseRead, WarehouseUpdate
from app.services import audit_service, user_service, warehouse_member_service, warehouse_service

router = APIRouter(prefix="/warehouses", tags=["warehouses"])


@router.get("", response_model=list[WarehouseRead])
def list_warehouses(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return warehouse_service.list_warehouses(db)


@router.get("/{warehouse_id}/members", response_model=list[UserPublic])
def list_warehouse_members(
    warehouse_id: DbPathId,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    if warehouse_service.get_warehouse(db, warehouse_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Склад не найден")
    return warehouse_member_service.list_members(db, warehouse_id)


@router.get("/{warehouse_id}", response_model=WarehouseRead)
def get_warehouse(
    warehouse_id: DbPathId,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    wh = warehouse_service.read_warehouse(db, warehouse_id)
    if wh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Склад не найден")
    return wh


@router.post("/{warehouse_id}/members", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def add_warehouse_member(
    warehouse_id: DbPathId,
    payload: WarehouseMemberAdd,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin),
):
    row = warehouse_member_service.add_member(db, warehouse_id, payload.user_id)
    if row is None:
        if warehouse_service.get_warehouse(db, warehouse_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Склад не найден")
        if user_service.get_by_id(db, payload.user_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Пользователь уже в списке склада")
    user = user_service.get_by_id(db, row.user_id)
    assert user is not None
    audit_service.record(
        db,
        actor=actor,
        action="warehouse.member.add",
        entity_type="warehouse_member",
        entity_id=row.id,
        warehouse_id=warehouse_id,
        detail={"user_id": payload.user_id, "username": user.username},
    )
    return user


@router.delete("/{warehouse_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_warehouse_member(
    warehouse_id: DbPathId,
    user_id: DbPathId,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin),
):
    if warehouse_service.get_warehouse(db, warehouse_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Склад не найден")
    u = user_service.get_by_id(db, user_id)
    if u is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    if not warehouse_member_service.remove_member(db, warehouse_id, user_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Участник не найден")
    audit_service.record(
        db,
        actor=actor,
        action="warehouse.member.remove",
        entity_type="warehouse_member",
        entity_id=user_id,
        warehouse_id=warehouse_id,
        detail={"user_id": user_id, "username": u.username},
    )


@router.post("", response_model=WarehouseRead, status_code=status.HTTP_201_CREATED)
def create_warehouse(
    payload: WarehouseCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin),
):
    try:
        wh = warehouse_service.create_warehouse(db, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Склад с таким именем уже есть")
    audit_service.record(
        db,
        actor=actor,
        action="warehouse.create",
        entity_type="warehouse",
        entity_id=wh.id,
        warehouse_id=wh.id,
        detail={"name": wh.name},
    )
    out = warehouse_service.read_warehouse(db, wh.id)
    assert out is not None
    return out


@router.patch("/{warehouse_id}", response_model=WarehouseRead)
def update_warehouse(
    warehouse_id: DbPathId,
    payload: WarehouseUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin),
):
    try:
        wh = warehouse_service.update_warehouse(db, warehouse_id, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Склад с таким именем уже есть")
    if wh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Склад не найден")
    audit_service.record(
        db,
        actor=actor,
        action="warehouse.update",
        entity_type="warehouse",
        entity_id=wh.id,
        warehouse_id=wh.id,
        detail={"patch": payload.model_dump(exclude_unset=True)},
    )
    out = warehouse_service.read_warehouse(db, warehouse_id)
    assert out is not None
    return out


@router.delete("/{warehouse_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_warehouse(
    warehouse_id: DbPathId,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin),
):
    wh = warehouse_service.get_warehouse(db, warehouse_id)
    if wh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Склад не найден")
    snapshot = {"id": wh.id, "name": wh.name}
    try:
        warehouse_service.delete_warehouse(db, warehouse_id)
    except ValueError as e:
        if e.args and e.args[0] == "warehouse_in_use":
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Склад нельзя удалить: есть заказы или остатки",
            )
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid")
    audit_service.record(
        db,
        actor=actor,
        action="warehouse.delete",
        entity_type="warehouse",
        entity_id=snapshot["id"],
        warehouse_id=None,
        detail=snapshot,
    )
