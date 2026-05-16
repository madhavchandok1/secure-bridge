from uuid import UUID

from pydantic import (
    BaseModel, 
    ConfigDict, 
    Field, 
    field_validator, 
    EmailStr
)

from app.utils.validators import validate_slug


class SetupOrganizationRequest(BaseModel):
    """
    Data validation schema for the initial platform bootstrapping event.

    This atomic request handles the concurrent creation of a brand new 
    organization tenant alongside its primary administrative owner account.
    """

    # The official display identity of the new tenant workspace.
    organization_name: str = Field(
        min_length=2,
        max_length=255,
    )

    # The URL route segment requested for the workspace partition.
    slug: str = Field(
        min_length=3,
        max_length=50,
    )

    # The display name of the primary administrator account.
    owner_name: str = Field(
        min_length=2,
        max_length=255,
    )

    # The verified contact email address for the account owner.
    owner_email: EmailStr

    # The master plaintext authentication string for the owner profile.
    password: str = Field(
        min_length=8,
        max_length=128,
    )

    @field_validator("slug")
    @classmethod
    def validate_slug_field(cls, value: str) -> str:
        """
        Validates the incoming slug format and confirms it avoids 
        system-reserved internal routing paths.
        """
        return validate_slug(slug=value)


class OrganizationResponse(BaseModel):
    """
    Data serialization schema representing an active system organization.

    Converts internal database structures into clean, scrubbed JSON payloads 
    for consumer application rendering blocks.
    """

    # System-wide identifier mapping the organization node.
    id: UUID

    # The human-readable name of the active tenant workspace.
    name: str

    # The unique URL partition string matching the tenant workspace.
    slug: str

    # The active account identifier of the organization workspace owner.
    owner_id: UUID | None

    # Global runtime access toggle for the tenant partition layout.
    is_active: bool

    # Total member account seats allowed under this partition's constraints.
    max_members: int

    # Directs Pydantic to extract attributes natively from database models.
    model_config = ConfigDict(from_attributes=True)


class SetupOrganizationResponse(BaseModel):
    """
    Data serialization schema returned following a successful platform bootstrap.

    Returns the session authentication credentials along with the newly minted 
    organization metadata to immediately log the owner into the frontend application.
    """

    # Cryptographic JSON Web Token string encoding the owner's immediate session context.
    access_token: str

    # The authentication scheme descriptor (e.g., 'bearer').
    token_type: str

    # Remaining lifetime validity of the access token in seconds.
    expires_in: int

    # The unencrypted representation of the workspace invitation key, 
    # presented exactly once so the administrator can save or share it.
    invite_key: str

    # Nested payload containing the structural details of the workspace.
    organization: OrganizationResponse


class SlugAvailabilityResponse(BaseModel):
    """
    Data serialization schema for workspace identifier lookup validations.

    Used by public onboarding endpoints to provide real-time UI/UX feedback 
    on whether a preferred workspace URL segment is open or taken.
    """

    # The targeted path segment checked during the database lookup block.
    slug: str

    # Flag indicating if the requested path is free for registration.
    available: bool


class InviteKeyResponse(BaseModel):
    """
    Data serialization schema for invitation key generation and rotation utilities.

    Secures workspace boundaries by providing a dedicated structure for 
    transporting the workspace's entry credentials.
    """

    # The plaintext secret string required for new users to register under this tenant.
    invite_key: str