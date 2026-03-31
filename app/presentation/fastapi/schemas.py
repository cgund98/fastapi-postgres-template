"""Shared presentation schemas."""

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Pagination query parameters."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Number of items per page")


class PaginatedResponse[T](BaseModel):
    """Paginated response wrapper."""

    items: list[T] = Field(description="List of items in the current page")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")
    total: int = Field(description="Total number of items")
    total_pages: int = Field(description="Total number of pages")
