import logging
import structlog
from app.core.config import settings
from pathlib import Path


def setup_logging():
    log_file = Path(settings.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(settings.log_level)),
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
        ]
    )

    return structlog.get_logger()


logger = setup_logging()
