from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID as PyUUID

from sqlalchemy import (JSON, Boolean, CheckConstraint, Column, DateTime,
                        Float, ForeignKey, Index, Integer, LargeBinary,
                        Numeric, Table, Text, func)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

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


class AcademicSource(Base):
    """Academic papers, historical documents, and authoritative sources for fact-checking."""

    __tablename__ = "academic_sources"

    id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    title: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    authors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    publication_year: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True
    )
    doi: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, unique=True, index=True
    )
    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    full_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "source_type IN ('academic_paper','historical_document',"
            "'government_report','international_organization','expert_analysis')"
        ),
        nullable=False,
        index=True,
    )
    credibility_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        index=True,
        comment="Score from 0.0 to 1.0 indicating source credibility",
    )
    keywords: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    citation_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    fact_checks: Mapped[List["FactCheck"]] = relationship(
        back_populates="academic_source"
    )

    repr_cols = ["id", "title", "source_type"]


class SourceBias(Base):
    __tablename__ = "source_bias"

    id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    bias_score: Mapped[Optional[float]] = mapped_column(
        Numeric(precision=4, scale=3), nullable=True, index=True
    )
    bias_label: Mapped[Optional[str]] = mapped_column(
        Text,
        CheckConstraint("bias_label IN ('left','center','right','unknown')"),
        nullable=True,
        index=True,
    )
    # Enhanced bias dimensions
    political_bias: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        index=True,
        comment="Political bias from -1.0 (left) to 1.0 (right)",
    )
    factual_accuracy: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        index=True,
        comment="Factual accuracy from 0.0 (low) to 1.0 (high)",
    )
    emotional_tone: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        index=True,
        comment="Emotional tone from -1.0 (negative) to 1.0 (positive)",
    )
    sensationalism_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        index=True,
        comment="Sensationalism from 0.0 (neutral) to 1.0 (highly sensationalized)",
    )
    analysis_method: Mapped[Optional[str]] = mapped_column(
        Text,
        CheckConstraint(
            "analysis_method IN ('manual','llm_automated','hybrid','external_rating')"
        ),
        nullable=True,
        index=True,
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        index=True,
        comment="Confidence in bias assessment from 0.0 to 1.0",
    )
    last_analysis_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    sources: Mapped[List["Source"]] = relationship(back_populates="bias")

    repr_cols = ["id", "name", "bias_label"]


class BiasAnalysis(Base):
    """Individual bias analysis reports for sources or narratives."""

    __tablename__ = "bias_analyses"

    id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    source_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), nullable=True, index=True
    )
    narrative_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("narratives.id", ondelete="CASCADE"), nullable=True, index=True
    )
    analysis_type: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "analysis_type IN ('source_bias','narrative_bias','fact_check','alternative_perspective')"
        ),
        nullable=False,
        index=True,
    )
    bias_indicators: Mapped[dict] = mapped_column(JSON, nullable=True)
    blind_spots: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    missing_context: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    alternative_viewpoints: Mapped[Optional[List[str]]] = mapped_column(
        JSON, nullable=True
    )
    fact_check_results: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    llm_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    analysis_model: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    source: Mapped[Optional["Source"]] = relationship(back_populates="bias_analyses")
    narrative: Mapped[Optional["Narrative"]] = relationship(
        back_populates="bias_analyses"
    )

    repr_cols = ["id", "analysis_type", "confidence_score"]


class FactCheck(Base):
    """Fact-checking results against academic sources."""

    __tablename__ = "fact_checks"

    id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    academic_source_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_sources.id"),
        nullable=False,
        index=True,
    )
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    verification_status: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "verification_status IN ('verified','partially_verified','disputed','false','inconclusive')"
        ),
        nullable=False,
        index=True,
    )
    evidence_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    accuracy_score: Mapped[float] = mapped_column(
        Float, nullable=False, index=True, comment="Accuracy score from 0.0 to 1.0"
    )
    context_provided: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    llm_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    source: Mapped["Source"] = relationship(back_populates="fact_checks")
    academic_source: Mapped["AcademicSource"] = relationship(
        back_populates="fact_checks"
    )

    repr_cols = ["id", "verification_status", "accuracy_score"]


class AlternativePerspective(Base):
    """Generated alternative viewpoints and counter-narratives."""

    __tablename__ = "alternative_perspectives"

    id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    source_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), nullable=True, index=True
    )
    narrative_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("narratives.id", ondelete="CASCADE"), nullable=True, index=True
    )
    perspective_type: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "perspective_type IN ('counter_narrative','missing_context',"
            "'alternative_interpretation','historical_context','opposing_view')"
        ),
        nullable=False,
        index=True,
    )
    perspective_text: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_sources: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    credibility_indicators: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    bias_correction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    generation_model: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    source: Mapped[Optional["Source"]] = relationship(
        back_populates="alternative_perspectives"
    )
    narrative: Mapped[Optional["Narrative"]] = relationship(
        back_populates="alternative_perspectives"
    )

    repr_cols = ["id", "perspective_type", "confidence_score"]


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
    bias_id: Mapped[Optional[PyUUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_bias.id"), nullable=True
    )

    embeddings: Mapped[List["Embedding"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )
    bias: Mapped[Optional["SourceBias"]] = relationship(back_populates="sources")
    bias_analyses: Mapped[List["BiasAnalysis"]] = relationship(back_populates="source")
    fact_checks: Mapped[List["FactCheck"]] = relationship(back_populates="source")
    alternative_perspectives: Mapped[List["AlternativePerspective"]] = relationship(
        back_populates="source"
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
    conflict: Mapped[Optional["Narrative"]] = relationship(remote_side="Narrative.id")
    bias_analyses: Mapped[List["BiasAnalysis"]] = relationship(
        back_populates="narrative"
    )
    alternative_perspectives: Mapped[List["AlternativePerspective"]] = relationship(
        back_populates="narrative"
    )

    repr_cols = ["id", "cluster_id"]


# Import User model so Alembic can detect it
from app.models_user import User  # noqa: F401

# Additional composite / custom indexes
Index("ix_sources_platform_created_at", Source.platform, Source.created_at)


# Pydantic Models for API responses
from pydantic import BaseModel


class SourceBiasOut(BaseModel):
    id: PyUUID
    name: str
    bias_score: Optional[float]
    bias_label: Optional[str]

    class Config:
        from_attributes = True


class SourceOut(BaseModel):
    id: int
    platform: str
    text_excerpt: str
    timestamp: datetime
    url: str
    engagement: int
    bias: Optional[SourceBiasOut]

    class Config:
        from_attributes = True


class NarrativeOut(BaseModel):
    summary: str
    sources: List[SourceOut]

    class Config:
        from_attributes = True
