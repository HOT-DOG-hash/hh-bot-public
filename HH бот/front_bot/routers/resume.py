from aiogram import Router
from aiogram.types import Message
import aiohttp, os

router = Router()
API_BASE = os.getenv("API_BASE", "http://web:8000")

@router.message()
async def catch_resume(message: Message):
    # текст > 400 символов
    if message.text and len(message.text) > 400:
        async with aiohttp.ClientSession() as s:
            form = aiohttp.FormData()
            form.add_field("chat_id", str(message.chat.id))
            form.add_field("text", message.text)
            async with s.post(f"{API_BASE}/api/resumes/", data=form) as r2:
                ok = (await r2.json()).get("ok")
        if ok:
            return await message.answer("Резюме (текст) сохранено.")

    # документ
    if message.document:
        file = await message.bot.get_file(message.document.file_id)
        file_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file.file_path}"
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as s:
            async with s.get(file_url) as r:
                r.raise_for_status()
                content = await r.read()
            form = aiohttp.FormData()
            form.add_field("chat_id", str(message.chat.id))
            form.add_field("file", content,
                           filename=message.document.file_name,
                           content_type=message.document.mime_type or "application/octet-stream")
            async with s.post(f"{API_BASE}/api/resumes/", data=form) as r2:
                ok = (await r2.json()).get("ok")
        if ok:
            return await message.answer("Резюме сохранено.")
