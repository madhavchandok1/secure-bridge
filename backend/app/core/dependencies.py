from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.db.session import AsyncSessionLocal

security_scheme = HTTPBearer()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides database session dependency.
    """

    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    """
    Returns authenticated user placeholder.
    """

    if not credentials.credentials:
        raise UnauthorizedError("Authentication credentials missing")
    
    return {
        "access_token": credentials.credentials
    }

async def get_current_active_user(current_user = Depends(get_current_user)):
    """
    Return active authenticated user.
    """

    return current_user