from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.dialects.postgresql import insert as pg_insert
from ...backend.app.database import SessionLocal
from ...backend.app.models import SearchQuery, User
from ..hh_client import HHClient
import httpx

router = Router()

async def save_activity(chat_id: int, query: str | None = None):
    async with SessionLocal() as db:
        stmt = pg_insert(User).values(chat_id=chat_id)
        stmt = stmt.on_conflict_do_update(
            index_elements=[User.chat_id],
            set_={"last_activity": None}
        )
        await db.execute(stmt)
        if query:
            await db.execute(pg_insert(SearchQuery).values(chat_id=chat_id, query=query))
        await db.commit()

@router.message(Command("search"))
async def cmd_search(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.answer("Использование: /search {текст}")
    query = parts[1].strip()
    await save_activity(message.chat.id, query)

    try:
        async with HHClient() as client:
            data = await client.search(query, per_page=5)
    except httpx.HTTPError:
        return await message.answer("HH API сейчас недоступен. Попробуйте позже.")

    items = data.get("items", [])
    if not items:
        return await message.answer("Ничего не найдено.")

    lines = []
    for v in items:
        name = v.get("name", "Без названия")
        emp = (v.get("employer") or {}).get("name", "")
        salary = v.get("salary")
        salary_str = "зарплата не указана"
        if salary:
            _from = salary.get("from")
            _to = salary.get("to")
            cur = salary.get("currency", "")
            if _from or _to:
                salary_str = f"{_from or ''}-{_to or ''} {cur}".strip("- ").strip()
        url = v.get("alternate_url", "")
        lines.append(f"• {name} — {emp}\n  {salary_str}\n  {url}")

    await message.answer("\n\n".join(lines))

@router.message(Command("vacancy"))
async def cmd_vacancy(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.answer("Использование: /vacancy {id}")
    vid = parts[1].strip()
    await save_activity(message.chat.id, None)

    try:
        async with HHClient() as client:
            data = await client.vacancy(vid)
    except httpx.HTTPError:
        return await message.answer("Не удалось получить вакансию (HH API недоступен).")

    name = data.get("name", "")
    emp = (data.get("employer") or {}).get("name", "")
    desc = data.get("description", "")
    url = data.get("alternate_url", "")
    if desc and len(desc) > 1500:
        desc = desc[:1500] + "..."
    await message.answer(f"{name}\n{emp}\n\n{url}\n\n{desc}")
