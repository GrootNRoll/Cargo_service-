from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps_auth import get_current_user, require_admin
from app.api.ids import DbPathId
from app.database import get_db
from app.models.entities import User
from app.schemas.warehouse import WarehouseCreate, WarehouseRead, WarehouseUpdate
from app.services import warehouse_service

router = APIRouter(prefix="/warehouses", tags=["warehouses"])


@router.get("", response_model=list[WarehouseRead])
def list_warehouses(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return warehouse_service.list_warehouses(db)


@router.get("/{warehouse_id}", response_model=WarehouseRead)
def get_warehouse(
    warehouse_id: DbPathId,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    wh = warehouse_service.get_warehouse(db, warehouse_id)
    if wh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Склад не найден")
    return wh


@router.post("", response_model=WarehouseRead, status_code=status.HTTP_201_CREATED)
def create_warehouse(
    payload: WarehouseCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    try:
        return warehouse_service.create_warehouse(db, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Склад с таким именем уже есть")


@router.patch("/{warehouse_id}", response_model=WarehouseRead)
def update_warehouse(
    warehouse_id: DbPathId,
    payload: WarehouseUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    try:
        wh = warehouse_service.update_warehouse(db, warehouse_id, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Склад с таким именем уже есть")
    if wh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Склад не найден")
    return wh


@router.delete("/{warehouse_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_warehouse(
    warehouse_id: DbPathId,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    try:
        if not warehouse_service.delete_warehouse(db, warehouse_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Склад не найден")
    except ValueError as e:
        if e.args and e.args[0] == "warehouse_in_use":
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Склад нельзя удалить: есть заказы или остатки",
            )
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid")
