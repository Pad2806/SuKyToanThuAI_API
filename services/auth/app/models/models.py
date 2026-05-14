"""Auth Service — models: users, audit_log."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.core.database import Base


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

def _now() -> Mapped[datetime]:
    return mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

def _nullable_ts() -> Mapped[datetime | None]:
    return mapped_column(TIMESTAMP(timezone=True), nullable=True)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _uuid_pk()
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'viewer'"))
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = _now()
    last_login_at: Mapped[datetime | None] = _nullable_ts()

    __table_args__ = (
        CheckConstraint("role IN ('admin','editor','viewer')", name="users_role_check"),
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = _uuid_pk()
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    diff: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = _now()

    __table_args__ = (
        Index("idx_audit_log_entity", "entity_type", "entity_id", "created_at"),
        Index("idx_audit_log_actor", "actor_id", "created_at"),
    )
