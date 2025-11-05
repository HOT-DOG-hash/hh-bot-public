from pydantic import BaseModel
from datetime import datetime

class ResumeOut(BaseModel):
    id: int
    user_id: int
    hh_id: str | None = None
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}
