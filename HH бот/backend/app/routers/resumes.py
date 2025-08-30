from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import os, aiofiles
from ..database import get_db
from ..models import Resume

router = APIRouter(prefix="/api/resumes", tags=["resumes"])
MEDIA_DIR = "/app/media/resumes"

@router.post("/")
async def upload_resume(chat_id: int = Form(...), text: str | None = Form(None),
                        file: UploadFile | None = File(None),
                        db: AsyncSession = Depends(get_db)):
    file_path = None
    if file is not None:
        os.makedirs(MEDIA_DIR, exist_ok=True)
        safe_name = file.filename.replace("/", "_").replace("\\", "_")
        file_path = os.path.join(MEDIA_DIR, f"{chat_id}_{safe_name}")
        async with aiofiles.open(file_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                await f.write(chunk)

    res = Resume(chat_id=chat_id, text=text, file_path=file_path)
    db.add(res)
    await db.commit()
    return {"ok": True}
