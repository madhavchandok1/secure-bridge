from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar(
    name="ModelType",
    bound=Base    
)

class BaseRepository(Generic[ModelType]):
    """
    Generic repository with reusable CRUD operations.
    """

    def __init__(self, model: type[ModelType]):
        self.model = model
    
    
    async def get_by_id(self, db: AsyncSession, entity_id) -> ModelType | None:
        query = select(self.model).where(self.model.id == entity_id)

        result = await db.execute(query)

        return result.scalar_one_or_none()
    
    
    async def get_all(self, db: AsyncSession) -> list[ModelType]:
        query = select(self.model)

        result = await db.execute(query)

        return list(result.scalars().all())
    

    async def create(self, db: AsyncSession, data: dict) -> ModelType:
        entity = self.model(**data)

        db.add(entity)

        await db.flush()

        await db.refresh(entity)

        return entity


    async def update(self, db: AsyncSession, entity: ModelType, data: dict) -> ModelType:
        for field, value in data.items():
            setattr(entity, field, value)

        await db.flush()

        await db.refresh(entity)

        return entity


    async def hard_delete(self, db: AsyncSession, entity: ModelType) -> None:
        await db.delete(entity)

        await db.flush()