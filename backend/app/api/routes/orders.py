from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps_auth import get_current_user
from app.api.ids import DbPathId
from app.database import get_db
from app.models.entities import User
from app.schemas.order import OrderCreate, OrderRead, OrderTransition
from app.services import audit_service, order_service

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
    dependencies=[Depends(get_current_user)],
)


def _map_transition_error(code: str) -> HTTPException:
    if code == "not_found":
        return HTTPException(status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
    if code == "invalid_transition":
        return HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Недопустимый переход статуса",
        )
    if code == "insufficient_stock":
        return HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Недостаточно товара на складе для отгрузки",
        )
    return HTTPException(status.HTTP_400_BAD_REQUEST, detail=code)


@router.get("", response_model=list[OrderRead])
def list_orders(db: Session = Depends(get_db)):
    return order_service.list_orders(db)


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: DbPathId, db: Session = Depends(get_db)):
    order = order_service.get_order(db, order_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
    return order


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    try:
        order = order_service.create_order(db, payload)
    except ValueError as e:
        code = str(e.args[0]) if e.args else "invalid"
        if code == "warehouse_not_found":
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Склад не найден")
        if code == "product_not_found":
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Товар не найден")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=code)
    audit_service.record(
        db,
        actor=actor,
        action="order.create",
        entity_type="order",
        entity_id=order.id,
        warehouse_id=order.warehouse_id,
        detail={"status": order.status.value, "lines": len(order.lines)},
    )
    return order


@router.post("/{order_id}/transition", response_model=OrderRead)
def transition_order(
    order_id: DbPathId,
    payload: OrderTransition,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    prev = order_service.get_order(db, order_id)
    prev_status = prev.status.value if prev else None
    order, err = order_service.transition_order(db, order_id, payload.to_status)
    if err:
        raise _map_transition_error(err)
    assert order is not None
    audit_service.record(
        db,
        actor=actor,
        action="order.transition",
        entity_type="order",
        entity_id=order.id,
        warehouse_id=order.warehouse_id,
        detail={"from": prev_status, "to": order.status.value},
    )
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: DbPathId,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    existing = order_service.get_order(db, order_id)
    if existing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
    snap = {
        "warehouse_id": existing.warehouse_id,
        "status": existing.status.value,
    }
    try:
        ok = order_service.delete_order(db, order_id)
    except ValueError as e:
        if e.args and e.args[0] == "order_not_deletable":
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Удалить можно только заказы в статусе draft или cancelled",
            )
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid")
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
    audit_service.record(
        db,
        actor=actor,
        action="order.delete",
        entity_type="order",
        entity_id=order_id,
        warehouse_id=snap["warehouse_id"],
        detail=snap,
    )
