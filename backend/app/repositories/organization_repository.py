from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.repositories.base_repository import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self):
        super().__init__(Organization)
    

    async def get_by_slug(self, db: AsyncSession, slug: str) -> Organization | None:
        result = await db.execute(select(Organization).where(Organization.slug == slug))

        return result.scalar_one_or_none()