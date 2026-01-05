"""Presentation layer mappers for converting to domain layer types."""

from typing import TypeVar, cast

from app.domain.types import UNSET, UNSET_STR, OptionalOrUnset, RequiredOrUnset

T = TypeVar("T")


def to_optional_or_unset[T](value: T | None | str) -> OptionalOrUnset[T]:
    """
    Map a presentation layer value to domain layer OptionalOrUnset.

    Maps UNSET_STR to UNSET sentinel, passes through None or actual values.

    Args:
        value: The value from presentation layer (can be None, UNSET_STR, or actual value)

    Returns:
        UNSET if value is UNSET_STR, None if value is None, otherwise returns the value cast to T

    Examples:
        >>> to_optional_or_unset(None)
        None
        >>> to_optional_or_unset("__UNSET__")
        Unset
        >>> to_optional_or_unset("test@example.com")
        'test@example.com'
    """
    if value == UNSET_STR:
        return UNSET

    # After checking for UNSET_STR, value must be T | None
    # Cast to T to satisfy type checker when returning non-None values
    # This is safe because we've already handled the UNSET_STR case
    return cast(T, value)


def to_required_or_unset[T](value: T | str) -> RequiredOrUnset[T]:
    """
    Map a presentation layer value to domain layer RequiredOrUnset.

    Maps UNSET_STR to UNSET sentinel, passes through None or actual values.

    Args:
        value: The value from presentation layer (can be None, UNSET_STR, or actual value)

    Returns:
        UNSET if value is UNSET_STR, None if value is None, otherwise returns the value cast to T

    """

    if value == UNSET_STR:
        return UNSET

    return cast(T, value)
