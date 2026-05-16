import uuid

from datetime import (
    datetime, 
    timezone
)

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    DeclarativeBase, 
    Mapped, 
    mapped_column
)

class Base(DeclarativeBase):
    """
    The core declarative base for all database models.

    All application models should inherit from this class to be picked up
    by the SQLAlchemy registry and Alembic migrations.
    """
    pass

class TimestampMixin:
    """
    Provides automatic 'created_at' and 'updated_at' audit fields.

    This mixin ensures that every record tracks its own lifecycle. The 
    timestamps are timezone-aware to prevent issues across different 
    server regions.
    """

    # Captures the initial insertion time.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Captures the initial insertion time and refreshes on every subsequent update.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

class UUIDMixin:
    """
    Provides a universally unique identifier (UUID) as the primary key.

    Using UUIDs instead of auto-incrementing integers prevents ID enumeration 
    attacks and makes it safer to merge data across distributed databases.
    """

    # Primary key using the native PostgreSQL UUID type.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )