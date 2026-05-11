from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    actor_username: str | None
    action: str
    entity_type: str
    entity_id: int | None = None
    warehouse_id: int | None = None
    detail: dict | None = None


class WarehouseMemberAdd(BaseModel):
    user_id: int = Field(..., ge=1)
