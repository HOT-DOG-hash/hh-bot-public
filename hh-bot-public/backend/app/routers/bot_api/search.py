from fastapi import APIRouter
from pydantic import BaseModel, AnyUrl

router = APIRouter()

class ParseLinkIn(BaseModel):
    url: AnyUrl

class ParseLinkOut(BaseModel):
    vacancy_id: str | None
    employer_id: str | None
    raw: str

@router.post("/search/parse_link", response_model=ParseLinkOut)
async def parse_link(payload: ParseLinkIn):
    u = str(payload.url)
    # TODO: реальный парсинг HH URL
    return ParseLinkOut(vacancy_id=None, employer_id=None, raw=u)
