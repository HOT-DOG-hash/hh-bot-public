from datetime import datetime
from pydantic import BaseModel


class ResumeOut(BaseModel):
    id: int
    user_id: int
    title: str | None = None
    text: str | None = None
    file_path: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
