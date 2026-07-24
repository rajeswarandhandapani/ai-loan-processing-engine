"""Centralized logging setup: console + rotating file handler."""

import logging
import logging.handlers
from pathlib import Path

from app.core.config import get_settings


def setup_logging() -> None:
    """Configure the root logger. Called once at application startup."""
    settings = get_settings()
    log_dir = Path(__file__).resolve().parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    level = logging.DEBUG if settings.debug else logging.INFO
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(level)
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # Quiet noisy third-party loggers
    for noisy in ("azure", "openai", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger(__name__).info("Logging configured (level=%s)", logging.getLevelName(level))


def get_logger(name: str) -> logging.Logger:
    """Return a module logger (pass __name__)."""
    return logging.getLogger(name)
