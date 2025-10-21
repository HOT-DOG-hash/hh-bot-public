import os
from datetime import datetime, timezone

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Resume, User

router = APIRouter(prefix="/api/resumes", tags=["resumes"])
MEDIA_DIR = "/app/media/resumes"


def _sanitize_filename(original: str) -> str:
    safe = original.replace("/", "_").replace("\\", "_")
    return safe or "upload"


async def _ensure_media_dir() -> None:
    os.makedirs(MEDIA_DIR, exist_ok=True)


async def _persist_file(chat_id: int, upload: UploadFile, file_name: str) -> str:
    await _ensure_media_dir()
    path = os.path.join(MEDIA_DIR, f"{chat_id}_{file_name}")
    async with aiofiles.open(path, "wb") as buffer:
        while chunk := await upload.read(1024 * 1024):
            await buffer.write(chunk)
    await upload.close()
    return path


@router.post("/")
async def upload_resume(
    chat_id: int = Form(..., description="Telegram chat id"),
    text: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
):
    if file is None and not text:
        raise HTTPException(status_code=400, detail="Either file or text must be provided")

    result = await db.execute(select(User).where(User.tg_id == str(chat_id)))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(tg_id=str(chat_id))
        db.add(user)
        await db.flush()

    user.last_activity = datetime.now(timezone.utc)

    file_path: str | None = None
    file_name_hint: str | None = file.filename if file and file.filename else None
    if file is not None:
        safe_name = _sanitize_filename(file_name_hint or "file")
        file_path = await _persist_file(chat_id, file, safe_name)

    title_hint = file_name_hint or (text[:255] if text else None)
    resume = Resume(user_id=user.id, title=title_hint, text=text, file_path=file_path)
    db.add(resume)
    await db.commit()

    return {"ok": True, "resume_id": resume.id}
