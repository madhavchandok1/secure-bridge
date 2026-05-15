from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_org_role
from app.core.enums import OrgRole
from app.schemas import (
    SetupOrganizationRequest,
    SetupOrganizationResponse,
    SlugAvailabilityResponse,
    TokenResponse,
    MemberRegisterRequest,
    MemberLoginRequest,
    UserResponse,
    InviteKeyResponse
)

from app.services.auth_service import AuthService
from app.services.organization_service import OrganizationService

from app.utils.validators import validate_slug


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

auth_service = AuthService()
org_service = OrganizationService()


@router.get(
    "/check-slug/{slug}",
    response_model=SlugAvailabilityResponse,
)
async def check_slug_availability(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    validated_slug = validate_slug(slug)

    available = await org_service.check_slug_availability(
        db=db,
        slug=validated_slug,
    )

    return SlugAvailabilityResponse(
        slug=validated_slug,
        available=available,
    )


@router.post(
    "/setup",
    response_model=SetupOrganizationResponse,
    status_code=200,
)
async def setup_organization(
    request: Request,
    data: SetupOrganizationRequest,
    db: AsyncSession = Depends(get_db),
):
    ip_address = getattr(
        request.state,
        "client_ip",
        None,
    )

    return await org_service.setup_organization(
        db,
        data,
        ip_address,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
)
async def register_user(
    data: MemberRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await auth_service.register_member(
        db,
        data,
    )

    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    request: Request,
    data: MemberLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    ip_address = getattr(
        request.state,
        "client_ip",
        None,
    )

    return await auth_service.login(
        db,
        data,
        ip_address,
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me(
    auth_context=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await auth_service.get_current_user_profile(
        db=db,
        auth_context=auth_context,
    )

    return UserResponse.model_validate(user)


@router.get(
    "/invite-key",
    response_model=InviteKeyResponse,
)
async def get_invite_key(
    auth_context=Depends(require_org_role(OrgRole.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    invite_key = await org_service.get_invite_key_for_owner(
        db=db,
        auth_context=auth_context,
    )

    return InviteKeyResponse(
        invite_key=invite_key
    )
