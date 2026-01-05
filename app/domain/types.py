"""Shared type definitions for domain layer."""

from typing import TypeVar

T = TypeVar("T")

# String constant used in presentation layer to indicate unset fields
# This gets mapped to the Unset sentinel before passing to domain layer
UNSET_STR = "__UNSET__"


class Unset:
    """Sentinel class for unset fields in sparse updates."""

    _instance: "Unset | None" = None

    def __new__(cls) -> "Unset":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "Unset"

    def __bool__(self) -> bool:
        return False


# Singleton instance of Unset sentinel
UNSET = Unset()

# Type alias for Optional[T] that also allows Unset sentinel value
# Usage: OptionalOrUnset[str] means str | None | Unset
type OptionalOrUnset[T] = T | None | Unset

# Type alias for required fields that can be Unset or the actual type (not None)
# Usage: RequiredOrUnset[str] means str | Unset
# Use this for non-nullable database fields that support sparse updates
type RequiredOrUnset[T] = T | Unset
