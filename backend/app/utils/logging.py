"""Logging configuration."""

import logging

def setup_logging():
    """Configure standard structured logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Suppress verbose third-party HTTP and internal engine logs
    noisy_loggers = [
        "httpx",
        "httpcore",
        "urllib3",
        "asyncio",
        "playwright",
        "bs4",
        "sqlalchemy.engine",
        "uvicorn.access",
    ]
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

