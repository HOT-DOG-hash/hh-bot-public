from datetime import datetime

from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    tg_id: str
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
