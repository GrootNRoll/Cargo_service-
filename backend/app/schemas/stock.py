from app.constants import MAX_DB_INTEGER
from pydantic import BaseModel, ConfigDict, Field


class StockBase(BaseModel):
    warehouse_id: int = Field(..., ge=1, le=MAX_DB_INTEGER)
    product_id: int = Field(..., ge=1, le=MAX_DB_INTEGER)
    quantity: int = Field(default=0, ge=0)


class StockCreate(StockBase):
    pass


class StockUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: int = Field(..., ge=0, strict=True)

class StockRead(StockBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
