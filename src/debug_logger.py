import os
import time
import functools
import logging
from logging.handlers import RotatingFileHandler


def debug_enabled() -> bool:
    return os.getenv("DEBUG_MODE", "false").lower() == "true"


def _build_logger() -> logging.Logger:
    logger = logging.getLogger("sara")
    if getattr(logger, "_configured", False):
        return logger

    logger.setLevel(logging.DEBUG)

    # Console handler (INFO+)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO if debug_enabled() else logging.WARNING)
    ch_formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s", "%H:%M:%S")
    ch.setFormatter(ch_formatter)
    logger.addHandler(ch)

    # File handler (DEBUG) with rotation
    if debug_enabled():
        log_file = os.getenv("DEBUG_LOG_FILE", "debug.log")
        fh = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=3, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh_formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s %(funcName)s: %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
        fh.setFormatter(fh_formatter)
        logger.addHandler(fh)

    logger._configured = True  # type: ignore[attr-defined]
    return logger


logger = _build_logger()


def log_timing(operation_name: str):
    """Decorator to log timing and exceptions for any function when DEBUG_MODE is true."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not debug_enabled():
                return func(*args, **kwargs)
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start) * 1000.0
                logger.debug(f"{operation_name} completed in {duration_ms:.2f} ms")
                return result
            except Exception as e:
                duration_ms = (time.perf_counter() - start) * 1000.0
                logger.error(f"{operation_name} failed after {duration_ms:.2f} ms: {type(e).__name__}: {e}")
                raise

        return wrapper

    return decorator


def log_timing_async(operation_name: str):
    """Decorator to log timing for async functions when DEBUG_MODE is true."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not debug_enabled():
                return await func(*args, **kwargs)
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start) * 1000.0
                logger.debug(f"{operation_name} completed in {duration_ms:.2f} ms")
                return result
            except Exception as e:
                duration_ms = (time.perf_counter() - start) * 1000.0
                logger.error(f"{operation_name} failed after {duration_ms:.2f} ms: {type(e).__name__}: {e}")
                raise

        return wrapper

    return decorator


