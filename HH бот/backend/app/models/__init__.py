# app/models/__init__.py
from .base import Base
# Важно импортировать модели, чтобы они зарегистрировались в Base.metadata
from .user import User
from .resume import Resume

__all__ = ["Base", "User", "Resume"]
