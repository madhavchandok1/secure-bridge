from fastapi import (
    APIRouter,
    Depends,
    Request
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    get_current_user, 
    get_db, 
    require_org_role
)
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


# Router definition for authentication and organization management.
# Prefix is set to /auth to group related endpoints under a single namespace.
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

# Service layer instantiation
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
    
    """
    Checks if a unique organization identifier (slug) is available.

    This is typically used during the onboarding process to ensure 
    no two organizations share the same URL identifier.

    Args:
        slug: The raw string identifier to check.
        db: Database session.

    Returns:
        SlugAvailabilityResponse: Validation result and availability status.
    """
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
    """
    Bootstraps a new organization and its initial administrator.

    This process handles the creation of the organization entity, 
    workspace setup, and owner registration in a single transaction.

    Args:
        request: The FastAPI request object (used to extract client IP).
        data: The organization and owner details.
        db: Database session.
    """

    # IP is captured for audit logging and security monitoring
    ip_address = getattr(request.state, "client_ip", None)

    return await org_service.setup_organization(
        db=db,
        data=data,
        ip_address=ip_address,
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
    """
    Registers a new member to an existing organization via an invite.

    Args:
        data: User registration details, including the invite context.
        db: Database session.

    Returns:
        UserResponse: The newly created user profile.
    """

    user = await auth_service.register_member(
        db=db,
        data=data,
    )

    return UserResponse.model_validate(obj=user)


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    request: Request,
    data: MemberLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticates a user and returns a JWT access token.

    Verifies credentials and generates a secure session token. 
    The client IP is tracked to identify suspicious login patterns.

    Args:
        request: FastAPI request object.
        data: Login credentials (email/password).
        db: Database session.
    """

    # IP is captured for audit logging and security monitoring
    ip_address = getattr(
        request.state,
        "client_ip",
        None,
    )

    return await auth_service.login(
        db=db,
        data=data,
        ip_address=ip_address
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me(
    auth_context=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves the profile of the currently authenticated user.

    Requires a valid Authorization header with a Bearer token.
    """

    user = await auth_service.get_current_user_profile(
        db=db,
        auth_context=auth_context,
    )

    return UserResponse.model_validate(obj=user)


@router.get(
    "/invite-key",
    response_model=InviteKeyResponse,
)
async def get_invite_key(
    auth_context=Depends(require_org_role(OrgRole.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetches the organization's unique invite key.

    Restricted access: Only users with the 'OWNER' role within the 
    organization context can retrieve this key.
    """

    invite_key = await org_service.get_invite_key_for_owner(
        db=db,
        auth_context=auth_context,
    )

    return InviteKeyResponse(
        invite_key=invite_key
    )
