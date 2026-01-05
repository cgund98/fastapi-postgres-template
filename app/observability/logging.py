"""Centralized logging setup."""

import logging
import sys

import structlog

from app.config.settings import Settings
from app.observability.environment import is_development


def setup_logging(settings: Settings | None = None) -> None:
    """Configure structured logging."""
    log_level = logging.INFO
    if settings and settings.log_level:
        log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    dev_mode = is_development(settings)

    # Configure standard library logging
    # Use a plain formatter since structlog handles the rendering
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)

    # Choose renderer based on environment
    renderer = structlog.dev.ConsoleRenderer() if dev_mode else structlog.processors.JSONRenderer()

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            renderer,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)  # type: ignore[no-any-return]
