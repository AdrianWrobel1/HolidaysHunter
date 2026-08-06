"""SQLAlchemy models for Research Workspace environment."""

from datetime import datetime, timezone
import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ResearchSession(Base):
    """Admin research session (e.g. 'Egipt Wrzesień', 'Turcja Last Minute')."""

    __tablename__ = "research_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    collections: Mapped[list["WorkspaceCollection"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", lazy="selectin"
    )
    items: Mapped[list["WorkspaceItem"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", lazy="selectin"
    )
    snapshots: Mapped[list["WorkspaceSnapshot"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", lazy="selectin"
    )


class WorkspaceCollection(Base):
    """Logical collection grouping within a research session."""

    __tablename__ = "workspace_collections"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(20), nullable=False, default="indigo")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped["ResearchSession"] = relationship(back_populates="collections")
    items: Mapped[list["WorkspaceItem"]] = relationship(back_populates="collection")


class WorkspaceItem(Base):
    """Tracked offer item inside a research session workspace."""

    __tablename__ = "workspace_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False
    )
    collection_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("workspace_collections.id", ondelete="SET NULL"), nullable=True
    )
    offer_url: Mapped[str] = mapped_column(String(2000), nullable=False)
    offer_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    notes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    session: Mapped["ResearchSession"] = relationship(back_populates="items")
    collection: Mapped["WorkspaceCollection | None"] = relationship(back_populates="items")
    analysis_history: Mapped[list["WorkspaceAnalysisHistory"]] = relationship(
        back_populates="item", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_workspace_item_session", "session_id"),
        Index("ix_workspace_item_pinned", "is_pinned"),
    )


class WorkspaceAnalysisHistory(Base):
    """Immutable audit trail of historical analysis runs for a workspace item."""

    __tablename__ = "workspace_analysis_history"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    item_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspace_items.id", ondelete="CASCADE"), nullable=False
    )
    analysis_id: Mapped[str] = mapped_column(String(100), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    report_data: Mapped[dict] = mapped_column(JSON, nullable=False)

    item: Mapped["WorkspaceItem"] = relationship(back_populates="analysis_history")


class WorkspaceSnapshot(Base):
    """Point-in-time snapshot of session state and reports."""

    __tablename__ = "workspace_snapshots"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    snapshot_data: Mapped[dict] = mapped_column(JSON, nullable=False)

    session: Mapped["ResearchSession"] = relationship(back_populates="snapshots")
