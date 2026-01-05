"""Pagination utilities."""

import math
from typing import TypeVar

from app.presentation.schemas import PaginatedResponse

T = TypeVar("T")


def page_to_limit_offset(page: int, page_size: int) -> tuple[int, int]:
    """
    Convert page and page_size to limit and offset.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Tuple of (limit, offset)
    """
    limit = page_size
    offset = (page - 1) * page_size
    return limit, offset


def create_paginated_response[T](
    items: list[T],
    page: int,
    page_size: int,
    total: int,
) -> PaginatedResponse[T]:
    """
    Create a paginated response from items and pagination metadata.

    Args:
        items: List of items for the current page
        page: Current page number (1-indexed)
        page_size: Number of items per page
        total: Total number of items across all pages

    Returns:
        PaginatedResponse with items and pagination metadata
    """
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return PaginatedResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )
