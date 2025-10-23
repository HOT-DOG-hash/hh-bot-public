import logging
import re
from pathlib import Path

import structlog

from backend.app.core.config import settings

SENSITIVE_PATTERN = re.compile(
    r"(TOKEN|PASSWORD|SECRET|KEY|CF_TUNNEL_TOKEN|YOOMONEY|TELEGRAM|DATABASE_URL)",
    re.IGNORECASE,
)


def _mask_value(value: object) -> object:
    if isinstance(value, str):
        return SENSITIVE_PATTERN.sub("***", value)
    return value


class SensitiveDataFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401 - simple filter
        record.msg = _mask_value(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: _mask_value(v) for k, v in record.args.items()}
            else:
                record.args = tuple(_mask_value(arg) for arg in record.args)
        return True


def setup_logging() -> structlog.BoundLogger:
    level_name = str(settings.log_level).upper()
    level = logging._nameToLevel.get(level_name, logging.INFO)

    handlers: list[logging.Handler] = [logging.StreamHandler()]
    log_target = settings.log_file or "/var/log/app/app.log"
    log_path = Path(log_target)
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))
    except Exception:
        logging.getLogger(__name__).warning("logging fallback to stdout only (%s)", log_target)

    filter_ = SensitiveDataFilter()
    for handler in handlers:
        handler.addFilter(filter_)

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(level),
        processors=[structlog.processors.TimeStamper(fmt="iso"), structlog.dev.ConsoleRenderer()],
    )
    return structlog.get_logger()


logger = setup_logging()
