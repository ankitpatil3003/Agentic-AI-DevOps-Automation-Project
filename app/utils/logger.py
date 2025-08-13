# app/utils/logger.py

import logging
import sys

def init_logger(level: str = "INFO") -> None:
    """
    Initialize root logger and Uvicorn loggers to output to stdout
    with a consistent timestamped format.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Configure root logger
    root = logging.getLogger()
    root.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))

    # Replace any existing handlers
    root.handlers = [handler]

    # Also route Uvicorn logs through our handler/formatter
    for uv_logger in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(uv_logger)
        logger.handlers = [handler]
        logger.setLevel(log_level)
