from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field
)  

from uuid import UUID

from app.core.enums import OrgRole


class UserResponse(BaseModel):
    """
    Data serialization schema representing a public or internal profile representation.

    This model strips out sensitive security metadata (like passwords or IP logs) 
    while presenting the core attributes of a system identity to external clients.
    """

    # The unique system-wide identifier for this user.
    id: UUID

    # The primary contact and authenticated email identity.
    email: EmailStr

    # The user's full display or legal name.
    full_name: str

    # The organization partition identifier this profile is isolated within.
    org_id: UUID

    # The organizational access role or hierarchy rank assigned to the profile.
    org_role: OrgRole

    # System status flag indicating whether the profile is active.
    is_active: bool

    # Auditing timestamp tracking when the identity profile was initialized.
    created_at: datetime

    # Configures Pydantic to natively read SQLAlchemy models/ORM attributes
    model_config = ConfigDict(from_attributes=True)


class UserUpdateRequest(BaseModel):
    """
    Data validation schema for updating an existing user profile.

    All properties are optional by default, enabling partial (PATCH-style) updates 
    to the target resource without forcing the client to submit unchanged data fields.
    """

    # Optional profile name update. Constrained to match system creation rules.
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
    )


class UserListResponse(BaseModel):
    """
    Data serialization schema for paginated or collection query responses.

    Wraps a structured array of profile schemas alongside metadata to safely 
    facilitate front-end table navigation and pagination logic.
    """

    # The target page subset array containing specific profile representations.
    users: list[UserResponse]

    # Total matching records count discovered in the data store across all pages.
    total: int