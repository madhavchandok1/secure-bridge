from dataclasses import dataclass
from uuid import UUID
from app.core.enums import OrgRole

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.utils.validators import normalize_email, validate_slug

class MemberRegisterRequest(BaseModel):
    email: EmailStr

    password: str = Field(min_length=8, max_length=128)

    full_name: str = Field(min_length=2, max_length=255)

    org_slug: str

    invite_key: str

    @field_validator("email")
    @classmethod
    def normalize_email_field(cls, value: str) -> str:
        return normalize_email(email=value)


    @field_validator("org_slug")
    @classmethod
    def validate_org_slug(cls, value: str) -> str:
        return validate_slug(slug=value)
    

class MemberLoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email_field(cls, value: str) -> str:
        return normalize_email(email=value)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


@dataclass(frozen=True)
class AuthContext:
    user_id: UUID
    org_id: UUID
    org_role: OrgRole