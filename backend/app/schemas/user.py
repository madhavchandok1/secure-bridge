from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr
from pydantic import Field

from app.core.enums import OrgRole


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    org_id: UUID
    org_role: OrgRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
    )


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int