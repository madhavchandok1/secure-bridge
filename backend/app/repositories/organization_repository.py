from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.repositories.base_repository import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    """
    Data repository handling specialized persistence operations for Organization entities.

    Inherits foundational asynchronous CRUD capabilities from BaseRepository and introduces
    optimized, index-backed tenant resolution mechanics.
    """

    def __init__(self):
        """
        Initializes the repository interface by anchoring it to the Organization model.
        """
        super().__init__(Organization)
    

    async def get_by_slug(self, db: AsyncSession, slug: str) -> Organization | None:
        """
        Resolves an organization workspace using its unique URL path segment string.

        This method acts as the structural gateway for tenant identity context mapping 
        during incoming middleware API evaluations.

        Args:
            db (AsyncSession): The active asynchronous database connection pool session.
            slug (str): The unique string identifier assigned to the targeted tenant workspace.

        Returns:
            Organization | None: The fully hydrated Organization entity instance if a match 
                                 is identified, otherwise cleanly returns None.
        """
        
        # Formulate an optimized SELECT statement leveraging the unique database index on the slug column
        query = select(Organization).where(Organization.slug == slug)

        # Execute the query asynchronously within the provided engine transaction frame
        result = await db.execute(statement=query)

        # Safely extracts the singular matching record row or drops to None without throwing exceptions
        return result.scalar_one_or_none()