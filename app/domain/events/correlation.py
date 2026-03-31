from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar

correlation_id_contextvar: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str | None:
    """Get the correlation ID."""
    return correlation_id_contextvar.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID."""
    correlation_id_contextvar.set(correlation_id)


@contextmanager
def correlation_id_context(correlation_id: str) -> Generator[None, None, None]:
    """Context manager for correlation ID."""
    token = None
    try:
        token = correlation_id_contextvar.set(correlation_id)
        yield
    finally:
        if token is not None:
            correlation_id_contextvar.reset(token)
