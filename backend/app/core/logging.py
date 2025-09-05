"""
Logging configuration for Scorpio AI Agent System
"""

import sys
import logging
from typing import Any, Dict
import structlog
from pythonjsonlogger import jsonlogger


def setup_logging() -> None:
    """Configure structured logging"""

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # Configure structlog
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]

    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure JSON logging for production
    if not getattr(logging.getLogger(), 'has_json_handler', False):
        json_handler = logging.StreamHandler(sys.stdout)
        json_formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        json_handler.setFormatter(json_formatter)
        logging.getLogger().addHandler(json_handler)
        logging.getLogger().has_json_handler = True


def get_logger(name: str) -> Any:
    """Get a configured logger instance"""
    return structlog.get_logger(name)
