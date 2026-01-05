"""Domain-level exceptions."""

from app.infrastructure.db.exceptions import NotFoundError, RepositoryError


class DomainError(Exception):
    """Base exception for domain operations."""

    pass


class ValidationError(DomainError):
    """Raised when domain validation fails."""

    def __init__(self, message: str, field: str | None = None) -> None:
        """Initialize validation error."""
        self.field = field
        super().__init__(message)


class BusinessRuleError(DomainError):
    """Raised when a business rule is violated."""

    pass


# Re-export repository exceptions for convenience
__all__ = [
    "DomainError",
    "ValidationError",
    "BusinessRuleError",
    "NotFoundError",
    "RepositoryError",
]
