from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.entities import Product
from app.schemas.product import ProductCreate, ProductUpdate


def list_products(db: Session) -> list[Product]:
    return list(db.scalars(select(Product).order_by(Product.id)).all())


def get_product(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def create_product(db: Session, data: ProductCreate) -> Product:
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product | None:
    product = db.get(Product, product_id)
    if product is None:
        return None
    patch = data.model_dump(exclude_unset=True)
    for key, value in patch.items():
        if value is None and key in {"sku", "name", "unit"}:
            continue
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> bool:
    product = db.get(Product, product_id)
    if product is None:
        return False
    try:
        db.delete(product)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("product_in_use") from None
    return True
