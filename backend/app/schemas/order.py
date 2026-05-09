from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.constants import MAX_DB_INTEGER
from app.models.entities import OrderStatus


class OrderLineCreate(BaseModel):
    product_id: int = Field(..., ge=1, le=MAX_DB_INTEGER)
    quantity: int = Field(..., ge=1)
    unit_price: Decimal = Field(default=Decimal("0.00"), ge=0)


class OrderCreate(BaseModel):
    warehouse_id: int = Field(..., ge=1, le=MAX_DB_INTEGER)
    status: OrderStatus = OrderStatus.draft
    lines: list[OrderLineCreate] = Field(default_factory=list)


class OrderLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    unit_price: Decimal


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    warehouse_id: int
    status: OrderStatus
    created_at: datetime
    lines: list[OrderLineRead]

    @field_serializer("created_at")
    def _ser_created_at(self, v: datetime) -> str:
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class OrderTransition(BaseModel):
    """Смена статуса заказа (draft→confirmed→fulfilled или cancelled)."""

    to_status: OrderStatus
