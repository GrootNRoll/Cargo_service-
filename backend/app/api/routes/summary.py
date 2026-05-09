from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from app.api.deps_auth import get_current_user
from app.database import get_db
from app.models.entities import Order, Product, StockItem, User, Warehouse

router = APIRouter(prefix="/summary", tags=["summary"])


@router.get("")
def overview(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict[str, int]:
    return {
        "products": db.scalar(select(func.count()).select_from(Product)) or 0,
        "warehouses": db.scalar(select(func.count()).select_from(Warehouse)) or 0,
        "stock_rows": db.scalar(select(func.count()).select_from(StockItem)) or 0,
        "orders": db.scalar(select(func.count()).select_from(Order)) or 0,
    }
