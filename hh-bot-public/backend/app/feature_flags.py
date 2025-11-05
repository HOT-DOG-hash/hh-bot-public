"""Feature flag definitions for ML ranking experiments (docs-first).

Flag: ENABLE_ML_RANKING
-----------------------
- Тип: boolean (строки `1/true/yes` → True, иначе False).
- Источник: переменная окружения `ENABLE_ML_RANKING` или конфигурация
  feature-management сервиса (при интеграции).
- Назначение: переключение трафика на ML-ранжирование в экспериментальных
  группах.
- Сегментация: поддерживается через верхний уровень (hash по owner_id,
  geo, plan). Внутри функции только возвращается текущее значение.

Пример использования::

    from backend.app.feature_flags import is_ml_ranking_enabled

    if is_ml_ranking_enabled():
        # TODO: вызвать ML-ранжирование
        ...

На этапе документации функция заглушка и возвращает логическое значение
из переменной окружения.
"""

from __future__ import annotations

import os


def is_ml_ranking_enabled() -> bool:
    """Возвращает статус фичефлага ENABLE_ML_RANKING."""
    value = os.getenv("ENABLE_ML_RANKING", "false").strip().lower()
    return value in {"1", "true", "yes", "on"}
