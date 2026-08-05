"""Travel Profiles API — CRUD endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    TravelProfileCreate,
    TravelProfileResponse,
    TravelProfileUpdate,
)
from app.database.session import get_session
from app.services.profile_service import (
    create_profile,
    delete_profile,
    get_profile,
    get_profiles,
    update_profile,
)

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.get("", response_model=list[TravelProfileResponse])
async def list_profiles_endpoint(
    active_only: bool = True,
    session: AsyncSession = Depends(get_session),
) -> list[TravelProfileResponse]:
    """List all travel profiles."""
    profiles = await get_profiles(session, active_only=active_only)
    return [TravelProfileResponse.model_validate(p) for p in profiles]


@router.post("", response_model=TravelProfileResponse, status_code=201)
async def create_profile_endpoint(
    body: TravelProfileCreate,
    session: AsyncSession = Depends(get_session),
) -> TravelProfileResponse:
    """Create a new travel profile."""
    profile = await create_profile(session, **body.model_dump())
    return TravelProfileResponse.model_validate(profile)


@router.get("/{profile_id}", response_model=TravelProfileResponse)
async def get_profile_endpoint(
    profile_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> TravelProfileResponse:
    """Get a single travel profile."""
    profile = await get_profile(profile_id, session)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return TravelProfileResponse.model_validate(profile)


@router.patch("/{profile_id}", response_model=TravelProfileResponse)
async def update_profile_endpoint(
    profile_id: UUID,
    body: TravelProfileUpdate,
    session: AsyncSession = Depends(get_session),
) -> TravelProfileResponse:
    """Update a travel profile. Only provided fields are changed."""
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    profile = await update_profile(profile_id, session, **fields)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return TravelProfileResponse.model_validate(profile)


@router.delete("/{profile_id}", status_code=204)
async def delete_profile_endpoint(
    profile_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a travel profile."""
    deleted = await delete_profile(profile_id, session)
    if not deleted:
        raise HTTPException(status_code=404, detail="Profile not found")
