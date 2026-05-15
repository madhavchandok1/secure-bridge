import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import OrgRole
from app.db.base import Base, TimestampMixin, UUIDMixin

class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    supabase_uid: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    org_role: Mapped[OrgRole] = mapped_column(String(20), default=OrgRole.MEMBER.value, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    last_login_ip: Mapped[str | None] = mapped_column(String(100), nullable=True)

    organization = relationship(
        "Organization",
        foreign_keys=[org_id],
        back_populates="users",
        lazy="selectin",
    )
