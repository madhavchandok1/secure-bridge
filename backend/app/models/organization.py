import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Organization(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    encrypted_invite_key: Mapped[str] = mapped_column(String(500), nullable=False)
    
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    max_members: Mapped[int] = mapped_column(Integer, default=50, nullable=False)

    users = relationship(
        argument="User",
        back_populates="organization",
        lazy="selectin"
    )