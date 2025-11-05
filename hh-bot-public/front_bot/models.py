from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from telegram import Update


@dataclass(slots=True)
class TelegramIdentity:
    telegram_id: str
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None

    @classmethod
    def from_update(cls, update: Update) -> "TelegramIdentity":
        user = update.effective_user
        if user is None:
            raise ValueError("update without user context")
        return cls(
            telegram_id=str(user.id),
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )

    def to_payload(self) -> dict:
        return {
            "telegram_id": self.telegram_id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
        }


@dataclass(slots=True)
class CampaignDraft:
    resume: str | None = None
    country: str | None = None
    region: str | None = None
    schedule: List[str] = field(default_factory=list)
    employment: List[str] = field(default_factory=list)
    professions: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    target_salary: str | None = None
    search_scope: str | None = None
    cover_letter: str | None = None

    def reset(self) -> None:
        self.resume = None
        self.country = None
        self.region = None
        self.schedule.clear()
        self.employment.clear()
        self.professions.clear()
        self.keywords.clear()
        self.target_salary = None
        self.search_scope = None
        self.cover_letter = None

    def as_lines(self) -> list[str]:
        return [
            f"Резюме: {self.resume}",
            f"Страна/регион: {self.country} / {self.region}",
            f"График: {', '.join(self.schedule) if self.schedule else 'любой'}",
            f"Занятость: {', '.join(self.employment) if self.employment else 'любая'}",
            f"Профобласти: {', '.join(self.professions) if self.professions else 'не выбраны'}",
            f"Ключевые слова: {', '.join(self.keywords) if self.keywords else 'не заданы'}",
            f"Доход: {self.target_salary or 'обсуждается'}",
            f"Искать по: {self.search_scope or 'title+description'}",
            f"Сопроводительное письмо: {self.cover_letter or 'шаблон по умолчанию'}",
        ]
