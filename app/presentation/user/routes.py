"""User API routes."""

from fastapi import APIRouter, Depends, Query, status

from app.domain.exceptions import NotFoundError
from app.domain.user.service import UserService
from app.presentation.pagination import create_paginated_response, page_to_limit_offset
from app.presentation.schemas import PaginatedResponse
from app.presentation.user.deps import get_user_service
from app.presentation.user.schema import UserCreateRequest, UserResponse, UserUpdateRequest

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Number of items per page"),
    service: UserService = Depends(get_user_service),
) -> PaginatedResponse[UserResponse]:
    """List users with pagination."""
    limit, offset = page_to_limit_offset(page, page_size)
    users, total = await service.list_users(limit=limit, offset=offset)

    return create_paginated_response(
        items=[
            UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
            for user in users
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreateRequest,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Create a new user."""

    user = await service.create_user(email=request.email, name=request.name)

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Get user by ID."""

    user = await service.get_user(user_id)

    if user is None:
        raise NotFoundError(entity_type="User", identifier=user_id)

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Update user name."""

    user = await service.update_user_name(user_id, request.name)

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
) -> None:
    """Delete a user and their associated invoices."""

    await service.delete_user(user_id)
