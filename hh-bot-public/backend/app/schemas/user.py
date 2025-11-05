from pydantic import BaseModel
from datetime import datetime

class UserOut(BaseModel):
    id: int
    tg_id: str
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
