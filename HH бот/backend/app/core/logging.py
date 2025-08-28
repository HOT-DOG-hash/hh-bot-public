import logging
import structlog
from pathlib import Path
from app.core.config import settings

def setup_logging():
    level_name = str(settings.log_level).upper()
    level = logging._nameToLevel.get(level_name, logging.INFO)

    log_file = Path(settings.log_file or "/var/log/app/web.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(log_file, encoding="utf-8")],
    )

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(level),
        processors=[structlog.processors.TimeStamper(fmt="iso"), structlog.dev.ConsoleRenderer()],
    )
    return structlog.get_logger()

logger = setup_logging()
