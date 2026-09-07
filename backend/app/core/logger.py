import logging
import contextvars
import uuid
from typing import Optional

correlation_id_ctx_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default="SYSTEM"
)

def get_correlation_id() -> str:
    return correlation_id_ctx_var.get()

def set_correlation_id(cid: Optional[str] = None) -> str:
    if not cid:
        cid = str(uuid.uuid4())
    correlation_id_ctx_var.set(cid)
    return cid

class CorrelationFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = get_correlation_id()
        return True

def setup_logger(name="epias_platform"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - [%(correlation_id)s] - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.addFilter(CorrelationFilter())
    return logger

log = setup_logger()
