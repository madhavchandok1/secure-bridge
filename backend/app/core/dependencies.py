from uuid import UUID
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import OrgRole
from app.core.security import decode_access_token
from app.db.session import AsyncSessionLocal
from app.schemas.auth import AuthContext

security_scheme = HTTPBearer()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides database session dependency.
    """

    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> AuthContext:
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    try:
        return AuthContext(
            user_id=UUID(payload["sub"]),
            org_id=UUID(payload["org_id"]),
            org_role=OrgRole(payload["org_role"]),
        )
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    

def require_org_role(*allowed_roles: OrgRole):
    async def role_guard(
        auth_context: AuthContext = Depends(get_current_user),
    ) -> AuthContext:
        if auth_context.org_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        return auth_context

    return role_guard