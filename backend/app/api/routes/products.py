from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps_auth import get_current_user
from app.api.ids import DbPathId
from app.database import get_db
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services import product_service

router = APIRouter(
    prefix="/products",
    tags=["products"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[ProductRead])
def list_products(db: Session = Depends(get_db)):
    return product_service.list_products(db)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: DbPathId, db: Session = Depends(get_db)):
    product = product_service.get_product(db, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Товар не найден")
    return product


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    try:
        return product_service.create_product(db, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Нарушение уникальности SKU")


@router.patch("/{product_id}", response_model=ProductRead)
def update_product(product_id: DbPathId, payload: ProductUpdate, db: Session = Depends(get_db)):
    try:
        product = product_service.update_product(db, product_id, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Нарушение уникальности SKU")
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Товар не найден")
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: DbPathId, db: Session = Depends(get_db)):
    try:
        if not product_service.delete_product(db, product_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Товар не найден")
    except ValueError as e:
        if e.args and e.args[0] == "product_in_use":
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Товар нельзя удалить: есть ссылки (остатки или заказы)",
            )
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid")
