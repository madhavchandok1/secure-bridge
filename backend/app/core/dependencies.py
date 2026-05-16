from collections.abc import AsyncGenerator

from fastapi import(
    Depends, 
    HTTPException, 
    status
)
from fastapi.security import(
    HTTPAuthorizationCredentials, 
    HTTPBearer
)

from sqlalchemy.ext.asyncio import AsyncSession

from uuid import UUID

from app.core.enums import OrgRole
from app.core.security import decode_access_token
from app.db.session import AsyncSessionLocal
from app.schemas.auth import AuthContext

# Defines the Bearer token security scheme for Swagger UI and header parsing.
security_scheme = HTTPBearer()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides an asynchronous SQLAlchemy session.

    This uses an async context manager to ensure the session is automatically
    closed after the request is finished, preventing connection leaks.

    Yields:
        AsyncSession: A transactional database session.
    """

    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> AuthContext:
    """
    Validates the Bearer token and extracts the user context.

    This dependency verifies the JWT signature and ensures the required 
    claims (user_id, org_id, org_role) are present and valid.

    Args:
        credentials: The extracted Bearer token from the Authorization header.

    Returns:
        AuthContext: An object containing the authenticated user's identity and scope.

    Raises:
        HTTPException: 401 if the token is invalid, expired, or malformed.
    """
    try:
        # Verify signature and expiration
        payload = decode_access_token(credentials.credentials)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    try:
        # Transform payload into a type-safe AuthContext
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
    """
    A parameterized dependency factory for role-based access control (RBAC).

    Usage: Depends(require_org_role(OrgRole.OWNER, OrgRole.ADMIN))

    Args:
        *allowed_roles: One or more OrgRole enums that are permitted to access the route.

    Returns:
        Callable: A dependency function that validates the user's role.
    """
    async def role_guard(
        auth_context: AuthContext = Depends(get_current_user),
    ) -> AuthContext:
        """
        Inner guard function that performs the actual role check.

        Raises:
            HTTPException: 403 if the user's role is not in the allowed list.
        """

        if auth_context.org_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this resource.",
            )

        return auth_context

    return role_guard