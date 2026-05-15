from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    
    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))

        return result.scalar_one_or_none()
    
    
    async def get_by_supabase_uid(self, db: AsyncSession, uid: str) -> User | None:
        result = await db.execute(select(User).where(User.supabase_uid == uid))

        return result.scalar_one_or_none()