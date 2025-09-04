from __future__ import annotations

import logging
import os
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

# Управляем ответами сами -> единый формат и realm
_security = HTTPBasic(auto_error=False)
_log = logging.getLogger("security")


def _get_admin_creds() -> tuple[str, str]:
    """
    Основные имена: ADMIN_USER / ADMIN_PASS.
    Легаси-фолбэк: ADMIN_PASSWORD (с предупреждением в логах).
    """
    user = (os.getenv("ADMIN_USER") or "").strip()

    pwd: Optional[str] = os.getenv("ADMIN_PASS")
    if not pwd:
        legacy = os.getenv("ADMIN_PASSWORD")
        if legacy:
            _log.warning(
                "Using legacy env var ADMIN_PASSWORD — please migrate to ADMIN_PASS."
            )
            pwd = legacy

    return user, (pwd or "").strip()


def _cred_error(detail: str = "Unauthorized") -> HTTPException:
    realm = os.getenv("ADMIN_BASIC_REALM", "Restricted")
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": f'Basic realm="{realm}"'},
    )


def require_admin(credentials: HTTPBasicCredentials | None = Depends(_security)) -> str:
    """
    Зависимость для админ-роутов. Возвращает username при успехе
    или поднимает 401 с WWW-Authenticate: Basic.
    """
    admin_user, admin_pass = _get_admin_creds()

    # Конфиг не задан — никого не пускаем (снаружи не раскрываем причину)
    if not admin_user or not admin_pass:
        _log.error("Admin credentials are not set (ADMIN_USER/ADMIN_PASS).")
        raise _cred_error("Not authenticated")

    # Нет заголовка Authorization вообще
    if credentials is None:
        raise _cred_error("Not authenticated")

    if not (
        secrets.compare_digest(credentials.username, admin_user)
        and secrets.compare_digest(credentials.password, admin_pass)
    ):
        # Намеренно не уточняем, что именно не так
        raise _cred_error("Unauthorized")

    return credentials.username


__all__ = ["require_admin"]
