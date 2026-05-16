from dataclasses import dataclass

from uuid import UUID

from pydantic import (
    BaseModel, 
    EmailStr, 
    Field, 
    field_validator
)

from app.core.enums import OrgRole
from app.utils.validators import (
    normalize_email, 
    validate_slug
)

class MemberRegisterRequest(BaseModel):
    """
    Data validation schema for new member registration requests.

    Enforces strict structural boundaries for onboarding new team members into an 
    existing organization workspace via an invitation workflow.
    """

    # Validates input matches correct RFC email formatting.
    email: EmailStr

    # Password length boundary checking to prevent overly weak or massive buffer inputs.
    password: str = Field(min_length=8, max_length=128)

    # Human-readable name validation limits to keep profile views predictable.
    full_name: str = Field(min_length=2, max_length=255)

    # Target tenant identifier path (e.g., 'acme-corp').
    org_slug: str

    # Secret cryptographic invitation string assigned to the tenant workspace.
    invite_key: str

    @field_validator("email")
    @classmethod
    def normalize_email_field(cls, value: str) -> str:
        """
        Sanitizes the incoming email address into a uniform 
        lowercase format.
        """
        return normalize_email(email=value)


    @field_validator("org_slug")
    @classmethod
    def validate_org_slug(cls, value: str) -> str:
        """
        Validates the format of the organization slug and filters out 
        system-reserved routing keywords.
        """
        return validate_slug(slug=value)
    

class MemberLoginRequest(BaseModel):
    """
    Data validation schema for user authentication requests.

    Handles credentials required to generate authorization contexts for users.
    """

    # Identity address of the account holder.
    email: EmailStr
    # Plaintext password string passed downstream to the verification hashing machine.
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email_field(cls, value: str) -> str:
        """
        Ensures email lookups remain casing-insensitive during 
        authentication blocks.
        """
        return normalize_email(email=value)


class TokenResponse(BaseModel):
    """
    API serialization schema representing a successful authentication token pair.

    Adheres strictly to the OAuth 2.0 bearer specification format.
    """

    # The cryptographic JSON Web Token string encoding session details.
    access_token: str

    # The authorization schema scheme used (typically 'bearer').
    token_type: str

    # Remaining lifespan of the access token in seconds.
    expires_in: int


@dataclass(frozen=True)
class AuthContext:
    """
    An immutable application-internal representation of a verified session.

    Constructed dynamically by security guards and access dependencies *after* 
    token signatures have been securely validated. Passed down to service layers 
    to provide multi-tenant resource access boundaries.
    """

    # The resolved localized primary key id of the caller.
    user_id: UUID

    # The localized tenant partition id mapping the caller's organizational space.
    org_id: UUID

    # Explicit privilege assignment dictating administrative or read-only scope boundaries.
    org_role: OrgRole