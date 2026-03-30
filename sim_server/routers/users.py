from fastapi import APIRouter, Depends, HTTPException, status

from sim_server.models.user import OAuthAccount, User, UserProfile
from sim_server.schemas import (
    OAuthAccountRead,
    UserProfileRead,
    UserProfileUpdate,
    UserReadWithProfile,
)

from ..deps import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserReadWithProfile)
async def get_me(current_user: User = Depends(get_current_user)):
    await current_user.fetch_related("profile")
    return current_user


@router.get("/me/profile", response_model=UserProfileRead)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    profile = await UserProfile.get_or_none(user=current_user)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )
    return profile


@router.patch("/me/profile", response_model=UserProfileRead)
async def update_my_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
):
    profile = await UserProfile.get_or_none(user=current_user)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    await profile.save()

    return profile


@router.get("/me/oauth-accounts", response_model=list[OAuthAccountRead])
async def get_my_oauth_accounts(current_user: User = Depends(get_current_user)):
    return await OAuthAccount.filter(user=current_user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(current_user: User = Depends(get_current_user)):
    await current_user.delete()
