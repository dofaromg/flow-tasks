from __future__ import annotations

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Atom(Base):
    __tablename__ = "atoms"

    atom_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    language: Mapped[str] = mapped_column(String(16), nullable=False, default="zh-Hant")
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # trace fields (required)
    event_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    rid: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tick: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    persona_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    merkle_root: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    # context
    world_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    source_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="agent")
    source_ref: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    importance: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    privacy_level: Mapped[str] = mapped_column(String(16), nullable=False, default="internal")

    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
