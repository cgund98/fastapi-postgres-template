"""User API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.domain.exceptions import NotFoundError
from app.domain.user.service import UserService
from app.presentation.mapper import to_optional_or_unset, to_required_or_unset
from app.presentation.pagination import create_paginated_response, page_to_limit_offset
from app.presentation.schemas import PaginatedResponse
from app.presentation.user.deps import get_user_service
from app.presentation.user.schema import UserCreateRequest, UserPatchRequest, UserResponse

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
                age=user.age,
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

    user = await service.create_user(email=request.email, name=request.name, age=request.age)

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        age=user.age,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Get user by ID."""

    user = await service.get_user(user_id)

    if user is None:
        raise NotFoundError(entity_type="User", identifier=str(user_id))

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        age=user.age,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def patch_user(
    user_id: UUID,
    request: UserPatchRequest,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Patch user with sparse updates."""

    # Map presentation layer values to domain layer sentinels
    email = to_required_or_unset(request.email)
    name = to_required_or_unset(request.name)
    age = to_optional_or_unset(request.age)

    user = await service.patch_user(user_id, email=email, name=name, age=age)

    if user is None:
        raise NotFoundError(entity_type="User", identifier=str(user_id))

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        age=user.age,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
) -> None:
    """Delete a user and their associated invoices."""

    await service.delete_user(user_id)
