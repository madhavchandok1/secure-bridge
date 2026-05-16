import uuid

from sqlalchemy import (
    Boolean,
    ForeignKey, 
    Integer, 
    String
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column, 
    relationship
)

from app.db.base import (
    Base, 
    TimestampMixin, 
    UUIDMixin
)
from app.models.user import User

class Organization(Base, UUIDMixin, TimestampMixin):
    """
    Represents an isolated tenant (Organization) within the system.

    This model serves as the top-level container for all users and resources.
    It handles unique branding (via slugs), security (via encrypted invite keys),
    and subscription-like constraints (via max_members).
    """
    __tablename__ = "organizations"

    # The display name of the organization (e.g., "Acme Corp")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # A unique URL-friendly identifier used for subdomains or routing paths.
    # Indexed for high-performance lookups during request context setup.
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    # The Fernet-encrypted version of the organization's invite key.
    # Stored as a large string to accommodate encryption overhead.
    encrypted_invite_key: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Reference to the user who created/owns the organization.
    # Initially nullable to handle specific onboarding edge cases.
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Administrative toggle to disable an organization's access globally.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Soft limit on the number of users that can belong to this tenant.
    max_members: Mapped[int] = mapped_column(Integer, default=50, nullable=False)

    # Relationships
    # One-to-Many: An organization can have multiple users.
    # lazy="selectin" is optimized for async loading, preventing N+1 query issues.
    users = relationship(
        argument="User",
        back_populates="organization",
        foreign_keys=lambda: User.org_id,
        lazy="selectin"
    )

    owner = relationship(
        argument="User",
        foreign_keys=[owner_id],
        lazy="selectin"
    )