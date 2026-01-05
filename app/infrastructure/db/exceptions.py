"""Database and repository exceptions."""


class RepositoryError(Exception):
    """Base exception for repository operations."""

    pass


class NotFoundError(RepositoryError):
    """Raised when an entity is not found in the repository."""

    def __init__(self, entity_type: str, identifier: str | None = None) -> None:
        """Initialize not found error."""
        self.entity_type = entity_type
        self.identifier = identifier
        message = f"{entity_type} not found"
        if identifier:
            message += f" with identifier: {identifier}"
        super().__init__(message)


class DuplicateError(RepositoryError):
    """Raised when attempting to create a duplicate entity."""

    def __init__(self, entity_type: str, field: str, value: str) -> None:
        """Initialize duplicate error."""
        self.entity_type = entity_type
        self.field = field
        self.value = value
        super().__init__(f"{entity_type} with {field} '{value}' already exists")


class DatabaseError(RepositoryError):
    """Raised when a database operation fails."""

    pass
