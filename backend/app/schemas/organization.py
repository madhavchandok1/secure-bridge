from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, EmailStr

from app.utils.validators import validate_slug


class SetupOrganizationRequest(BaseModel):
    organization_name: str = Field(
        min_length=2,
        max_length=255,
    )

    slug: str = Field(
        min_length=3,
        max_length=50,
    )

    owner_name: str = Field(
        min_length=2,
        max_length=255,
    )

    owner_email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    @field_validator("slug")
    @classmethod
    def validate_slug_field(
        cls,
        value: str,
    ) -> str:
        return validate_slug(value)


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    owner_id: UUID | None
    is_active: bool
    max_members: int

    model_config = ConfigDict(from_attributes=True)


class SetupOrganizationResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

    invite_key: str

    organization: OrganizationResponse


class SlugAvailabilityResponse(BaseModel):
    slug: str
    available: bool


class InviteKeyResponse(BaseModel):
    invite_key: str