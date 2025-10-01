"""Database models using SQLAlchemy 2.0 with async support."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models with async attribute support."""

    pass


class User(Base):
    """User model - synced from Clerk."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)  # Clerk user ID
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    firm_id: Mapped[Optional[str]] = mapped_column(
        String(255), ForeignKey("firms.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    firm: Mapped[Optional["Firm"]] = relationship(back_populates="users")
    projects: Mapped[List["Project"]] = relationship(back_populates="owner")
    chat_messages: Mapped[List["ChatMessage"]] = relationship(back_populates="user")


class Firm(Base):
    """Firm/Organization model."""

    __tablename__ = "firms"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)  # Clerk org ID
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    users: Mapped[List["User"]] = relationship(back_populates="firm")
    projects: Mapped[List["Project"]] = relationship(back_populates="firm")


class Project(Base):
    """Project/Deal model."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    owner_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    firm_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("firms.id", ondelete="CASCADE"), nullable=False
    )
    target_company: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active"
    )  # active, completed, archived
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="projects")
    firm: Mapped["Firm"] = relationship(back_populates="projects")
    chat_messages: Mapped[List["ChatMessage"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    deliverables: Mapped[List["Deliverable"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    """Chat message model for conversation history."""

    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_metadata: Mapped[Optional[str]] = mapped_column(Text)  # JSON string for additional data
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="chat_messages")
    user: Mapped["User"] = relationship(back_populates="chat_messages")


class Deliverable(Base):
    """Deliverable model for generated documents."""

    __tablename__ = "deliverables"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # target_list, trading_comps, info_book
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="generating"
    )  # generating, completed, failed
    file_url: Mapped[Optional[str]] = mapped_column(String(500))  # R2 storage URL
    deliverable_metadata: Mapped[Optional[str]] = mapped_column(Text)  # JSON string for additional data
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="deliverables")


class CompanyCache(Base):
    """Company data cache to avoid redundant API calls."""

    __tablename__ = "company_cache"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_identifier: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )  # Ticker, ISIN, or company name
    data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string of company data
    source: Mapped[str] = mapped_column(String(100), nullable=False)  # yahoo, scraping, etc.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )  # Cache expiration
