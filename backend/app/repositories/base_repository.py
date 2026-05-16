from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from typing import (
    Generic, 
    TypeVar
)

from app.db.base import Base

# Declare a type variable bounded by your SQLAlchemy Declarative Base.
# This ensures that any class interacting with this repository is a valid database model,
# allowing static analysis tools and IDEs to provide accurate autocomplete features.
ModelType = TypeVar(
    name="ModelType",
    bound=Base    
)

class BaseRepository(Generic[ModelType]):
    """
    Abstract base class implementing the Generic Repository Pattern.

    Encapsulates standard asynchronous CRUD operations for SQLAlchemy models.
    This design isolates structural query mechanics from higher-level business services.
    """

    def __init__(self, model: type[ModelType]):
        """
        Initializes the generic repository interface.

        Args:
            model (type[ModelType]): The targeted SQLAlchemy model class (e.g., User, Organization).
        """
        self.model = model
    
    
    async def get_by_id(self, db: AsyncSession, entity_id) -> ModelType | None:
        """
        Retrieves a single model record matching the specified primary key ID.

        Args:
            db (AsyncSession): The active database transaction session instance.
            entity_id: The primary key value used to isolate the unique row.

        Returns:
            ModelType | None: The instantiated model instance if found, otherwise None.
        """

        # Formulate a safe, parametrized query to fetch the model by primary identifier
        query = select(self.model).where(self.model.id == entity_id)
        # Execute the query asynchronously within the provided engine session context
        result = await db.execute(statement=query)
        # Returns the single object or cleanly drops back to None if the record doesn't exist
        return result.scalar_one_or_none()
    
    
    async def get_all(self, db: AsyncSession) -> list[ModelType]:
        """
        Retrieves all database rows corresponding to the target model configuration.

        Args:
            db (AsyncSession): The active database transaction session instance.

        Returns:
            list[ModelType]: An array containing all matching instantiated entity records.
        """
        query = select(self.model)

        result = await db.execute(statement=query)

        # scalars().all() flattens the query tuple results directly into a clean Python list
        return list(result.scalars().all())
    

    async def create(self, db: AsyncSession, data: dict) -> ModelType:
        """
        Instantiates and persists a brand-new model entry into the database.

        Args:
            db (AsyncSession): The active database transaction session instance PERSISTING changes.
            data (dict): Key-value pairs containing model-matching instantiation parameters.

        Returns:
            ModelType: The newly created model entity containing system-generated tracking attributes.
        """

        # Unpack the dictionary parameters directly into the model's initialization signature
        entity = self.model(**data)

        # Place the entity under the session unit-of-work tracking registry
        db.add(instance=entity)

        # Flush changes to the database pool to trigger constraints and sequence assignments (IDs) 
        # without closing or committing the overarching transaction prematurely.
        await db.flush()

        # Re-sync state with database values to fill tracking variables (like auto-generated UUIDs/timestamps)
        await db.refresh(instance=entity)

        return entity


    async def update(self, db: AsyncSession, entity: ModelType, data: dict) -> ModelType:
        """
        Applies a delta modifications payload directly to an active, tracked model entity.

        Args:
            db (AsyncSession): The active database transaction session instance.
            entity (ModelType): The current live SQLAlchemy model object instance being altered.
            data (dict): The target attribute changes to map onto the entity object.

        Returns:
            ModelType: The updated model entity following state synchronization.
        """

        # Dynamically set provided attributes over the target model instance
        for field, value in data.items():
            setattr(entity, field, value)

        # Send structural column updates down the open database wire
        await db.flush()

        # Update tracking references to match latest row modifications
        await db.refresh(instance=entity)

        return entity


    async def hard_delete(self, db: AsyncSession, entity: ModelType) -> None:
        """
        Permanently expunges an existing record row from the database tables.

        Args:
            db (AsyncSession): The active database transaction session instance.
            entity (ModelType): The tracked model object instance slated for deletion.
        """

        # Issue an immediate DELETE statement targeting the entity record row
        await db.delete(instance=entity)

        # Push the row removal operational command down the network pool block
        await db.flush()