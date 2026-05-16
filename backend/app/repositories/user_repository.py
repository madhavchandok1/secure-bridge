from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Data repository handling specialized persistence operations for User entities.

    Inherits foundational asynchronous CRUD capabilities from BaseRepository and introduces
    index-backed query mechanics optimized for authentication and identity routing.
    """

    def __init__(self):
        """
        Initializes the repository interface by anchoring it to the User model.
        """
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        """
        Resolves a user account profile matching a normalized email address.

        Primarily utilized during raw authentication handshakes, invitation checks, 
        and administrative duplicate validations.

        Args:
            db (AsyncSession): The active asynchronous database connection pool session.
            email (str): The pre-normalized, lowercase email address of the target account.

        Returns:
            User | None: The fully hydrated User entity instance if found, 
                         otherwise cleanly returns None.
        """
        # Executes an index-backed look up against the unique 'email' column constraint
        query = select(User).where(User.email == email)
        
        result = await db.execute(statement=query)

        return result.scalar_one_or_none()
    
    async def get_by_supabase_uid(self, db: AsyncSession, uid: str) -> User | None:
        """
        Resolves a user account profile matching an authenticated Supabase identifier.

        This method is the vital runtime bridge for authentication middleware, allowing 
        the application to resolve a validated Supabase JSON Web Token (JWT) directly into 
        the local user context, tenant mapping, and resource access roles.

        Args:
            db (AsyncSession): The active asynchronous database connection pool session.
            uid (str): The unique 'auth.users.id' string string passed from Supabase Auth.

        Returns:
            User | None: The fully hydrated User entity instance if found, 
                         otherwise cleanly returns None.
        """
        # Executes a rapid index scan against the unique 'supabase_uid' database column
        query = select(User).where(User.supabase_uid == uid)
        
        result = await db.execute(statement=query)

        return result.scalar_one_or_none()