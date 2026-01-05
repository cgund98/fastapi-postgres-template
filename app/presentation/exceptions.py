"""Exception handling for HTTP responses."""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.domain.exceptions import BusinessRuleError, DomainError, ValidationError
from app.infrastructure.db.exceptions import DatabaseError, DuplicateError, NotFoundError, RepositoryError

# Mapping of exception types to HTTP status codes
EXCEPTION_STATUS_MAP: dict[type[Exception], int] = {
    # Domain exceptions
    ValidationError: status.HTTP_400_BAD_REQUEST,
    BusinessRuleError: status.HTTP_400_BAD_REQUEST,
    DomainError: status.HTTP_400_BAD_REQUEST,
    # Repository exceptions
    NotFoundError: status.HTTP_404_NOT_FOUND,
    DuplicateError: status.HTTP_409_CONFLICT,
    DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    RepositoryError: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


def get_status_code_for_exception(exc: Exception) -> int:
    """Get HTTP status code for an exception."""
    exc_type = type(exc)

    # Check exact type match first
    if exc_type in EXCEPTION_STATUS_MAP:
        return EXCEPTION_STATUS_MAP[exc_type]

    # Check base classes
    for base_type, status_code in EXCEPTION_STATUS_MAP.items():
        if isinstance(exc, base_type):
            return status_code

    # Default to 500 for unknown exceptions
    return status.HTTP_500_INTERNAL_SERVER_ERROR


def raise_http_exception(exc: Exception) -> HTTPException:
    """Convert a domain exception to an HTTPException."""
    status_code = get_status_code_for_exception(exc)
    return HTTPException(status_code=status_code, detail=str(exc))


async def handle_domain_exceptions(_request: Request, exc: Exception) -> JSONResponse:
    """FastAPI exception handler for domain exceptions."""
    status_code = get_status_code_for_exception(exc)
    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc)},
    )
