from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps_auth import get_current_user
from app.api.ids import DbPathId
from app.constants import MAX_DB_INTEGER
from app.database import get_db
from app.models.entities import User
from app.schemas.stock import StockCreate, StockRead, StockUpdate
from app.services import audit_service, stock_service

router = APIRouter(
    prefix="/stock",
    tags=["stock"],
    dependencies=[Depends(get_current_user)],
)

OptionalId = Annotated[int | None, Query(ge=1, le=MAX_DB_INTEGER)]


@router.get("", response_model=list[StockRead])
def list_stock(
    db: Session = Depends(get_db),
    warehouse_id: OptionalId = None,
    product_id: OptionalId = None,
):
    return stock_service.list_stock(db, warehouse_id=warehouse_id, product_id=product_id)


@router.get("/{stock_id}", response_model=StockRead)
def get_stock_item(stock_id: DbPathId, db: Session = Depends(get_db)):
    row = stock_service.get_stock_item(db, stock_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Запись остатка не найдена")
    return row


@router.post("", response_model=StockRead, status_code=status.HTTP_201_CREATED)
def create_stock(
    payload: StockCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    try:
        row = stock_service.create_stock(db, payload)
    except ValueError as e:
        code = e.args[0] if e.args else ""
        if code == "warehouse_not_found":
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Склад не найден")
        if code == "product_not_found":
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Товар не найден")
        if code == "duplicate_stock_row":
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Для пары склад+товар уже есть запись — измените количество через PATCH",
            )
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=code)
    audit_service.record(
        db,
        actor=actor,
        action="stock.create",
        entity_type="stock_item",
        entity_id=row.id,
        warehouse_id=row.warehouse_id,
        detail={
            "product_id": row.product_id,
            "quantity": row.quantity,
        },
    )
    return row


@router.patch("/{stock_id}", response_model=StockRead)
def update_stock(
    stock_id: DbPathId,
    payload: StockUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    prev = stock_service.get_stock_item(db, stock_id)
    row = stock_service.update_stock(db, stock_id, payload)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Запись остатка не найдена")
    audit_service.record(
        db,
        actor=actor,
        action="stock.update",
        entity_type="stock_item",
        entity_id=row.id,
        warehouse_id=row.warehouse_id,
        detail={
            "before": prev.quantity if prev else None,
            "after": row.quantity,
            "product_id": row.product_id,
        },
    )
    return row


@router.delete("/{stock_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stock(
    stock_id: DbPathId,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    prev = stock_service.get_stock_item(db, stock_id)
    if prev is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Запись остатка не найдена")
    if not stock_service.delete_stock(db, stock_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Запись остатка не найдена")
    audit_service.record(
        db,
        actor=actor,
        action="stock.delete",
        entity_type="stock_item",
        entity_id=stock_id,
        warehouse_id=prev.warehouse_id,
        detail={"product_id": prev.product_id, "quantity": prev.quantity},
    )
