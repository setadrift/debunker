from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (JSON, Column, DateTime, ForeignKey, Index, Integer,
                        LargeBinary, Table, Text, func)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    repr_cols: List[str] = []  # subclasses may override

    def __repr__(self) -> str:  # noqa: DunderMethod
        cols = ", ".join(
            f"{name}={getattr(self, name)!r}"
            for name in self.repr_cols
            if hasattr(self, name)
        )
        return f"<{self.__class__.__name__} {cols}>"


# Association table for many-to-many relationship between embeddings and clusters
cluster_sources = Table(
    "cluster_sources",
    Base.metadata,
    Column(
        "embedding_id",
        Integer,
        ForeignKey("embeddings.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "cluster_id",
        Integer,
        ForeignKey("clusters.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Index("ix_cluster_sources_embedding_id", "embedding_id"),
    Index("ix_cluster_sources_cluster_id", "cluster_id"),
)


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    meta: Mapped[dict] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    embeddings: Mapped[List["Embedding"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )

    repr_cols = ["id", "platform", "created_at"]


class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vector: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    source: Mapped["Source"] = relationship(back_populates="embeddings")
    clusters: Mapped[List["Cluster"]] = relationship(
        secondary=cluster_sources, back_populates="embeddings"
    )

    repr_cols = ["id", "source_id"]


class Cluster(Base):
    __tablename__ = "clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    narratives: Mapped[List["Narrative"]] = relationship(
        back_populates="cluster", cascade="all, delete-orphan"
    )
    embeddings: Mapped[List["Embedding"]] = relationship(
        secondary=cluster_sources, back_populates="clusters"
    )

    repr_cols = ["id", "created_at"]


class Narrative(Base):
    __tablename__ = "narratives"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cluster_id: Mapped[int] = mapped_column(
        ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    conflicting_with: Mapped[Optional[int]] = mapped_column(
        ForeignKey("narratives.id"), nullable=True
    )

    cluster: Mapped["Cluster"] = relationship(back_populates="narratives")
    conflict: Mapped[Optional["Narrative"]] = relationship(remote_side=[id])

    repr_cols = ["id", "cluster_id"]


# Additional composite / custom indexes
Index("ix_sources_platform_created_at", Source.platform, Source.created_at)
