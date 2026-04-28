"""
utils/logger.py — structured logging with request-ID support.
"""
import logging
import uuid
import time
from contextvars import ContextVar

# ── context var holds the current request ID ──────────────────────────────────
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    return request_id_var.get()


def new_request_id() -> str:
    rid = str(uuid.uuid4())[:8]
    request_id_var.set(rid)
    return rid


# ── custom formatter ───────────────────────────────────────────────────────────
class RequestIDFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        record.request_id = get_request_id()
        return super().format(record)


# ── module-level logger ────────────────────────────────────────────────────────
def get_logger(name: str = "sentinel") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = RequestIDFormatter(
            fmt="%(asctime)s [%(request_id)s] %(levelname)s %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


logger = get_logger()
