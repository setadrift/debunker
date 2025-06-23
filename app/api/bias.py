from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_session
from app.models import (AcademicSource, AlternativePerspective, BiasAnalysis,
                        FactCheck, Source, SourceBias)
from app.worker import celery_app

router = APIRouter()


class BiasAnalysisOut(BaseModel):
    id: UUID
    analysis_type: str
    bias_indicators: dict
    blind_spots: Optional[List[str]]
    missing_context: Optional[List[str]]
    confidence_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class AlternativePerspectiveOut(BaseModel):
    id: UUID
    perspective_type: str
    perspective_text: str
    supporting_sources: Optional[List[str]]
    confidence_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class FactCheckOut(BaseModel):
    id: UUID
    verification_status: str
    evidence_text: Optional[str]
    accuracy_score: float
    context_provided: bool
    academic_source_title: str
    created_at: datetime

    class Config:
        from_attributes = True


class SourceBiasDetailOut(BaseModel):
    id: UUID
    name: str
    political_bias: Optional[float]
    factual_accuracy: Optional[float]
    emotional_tone: Optional[float]
    sensationalism_score: Optional[float]
    confidence_score: Optional[float]
    analysis_method: Optional[str]
    last_analysis_date: Optional[datetime]

    class Config:
        from_attributes = True


class SourceDetailOut(BaseModel):
    id: int
    platform: str
    url: str
    created_at: datetime
    bias: Optional[SourceBiasDetailOut]
    bias_analyses: List[BiasAnalysisOut]
    alternative_perspectives: List[AlternativePerspectiveOut]
    fact_checks: List[FactCheckOut]

    class Config:
        from_attributes = True


@router.get("/sources/{source_id}/bias-analysis")
async def get_source_bias_analysis(
    source_id: int, session: AsyncSession = Depends(get_session)
) -> SourceDetailOut:
    """Get comprehensive bias analysis for a source."""

    source = await session.execute(
        select(Source)
        .options(
            selectinload(Source.bias),
            selectinload(Source.bias_analyses),
            selectinload(Source.alternative_perspectives),
            selectinload(Source.fact_checks).selectinload(FactCheck.academic_source),
        )
        .where(Source.id == source_id)
    )
    source = source.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # Format fact checks with academic source titles
    fact_checks = []
    for fc in source.fact_checks:
        fact_checks.append(
            FactCheckOut(
                id=fc.id,
                verification_status=fc.verification_status,
                evidence_text=fc.evidence_text,
                accuracy_score=fc.accuracy_score,
                context_provided=fc.context_provided,
                academic_source_title=fc.academic_source.title,
                created_at=fc.created_at,
            )
        )

    return SourceDetailOut(
        id=source.id,
        platform=source.platform,
        url=source.url,
        created_at=source.created_at,
        bias=SourceBiasDetailOut.model_validate(source.bias) if source.bias else None,
        bias_analyses=[
            BiasAnalysisOut.model_validate(ba) for ba in source.bias_analyses
        ],
        alternative_perspectives=[
            AlternativePerspectiveOut.model_validate(ap)
            for ap in source.alternative_perspectives
        ],
        fact_checks=fact_checks,
    )


@router.post("/sources/{source_id}/analyze")
async def trigger_bias_analysis(
    source_id: int,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """Trigger bias analysis for a specific source."""

    source = await session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # Queue bias analysis task
    celery_app.send_task("analyze_source_bias", args=[source_id])

    return {"message": f"Bias analysis queued for source {source_id}"}


@router.post("/analyze/batch")
async def trigger_batch_analysis(
    limit: int = 20, background_tasks: BackgroundTasks = None
):
    """Trigger batch bias analysis for unprocessed sources."""

    # Queue batch analysis task
    celery_app.send_task("batch_analyze_bias", args=[limit])

    return {"message": f"Batch bias analysis queued for up to {limit} sources"}


@router.get("/bias-stats")
async def get_bias_statistics(session: AsyncSession = Depends(get_session)):
    """Get system-wide bias analysis statistics."""

    # Get source counts by bias label
    bias_distribution = await session.execute(
        select(SourceBias.bias_label, func.count(Source.id))
        .outerjoin(Source, SourceBias.id == Source.bias_id)
        .group_by(SourceBias.bias_label)
    )

    # Get analysis counts
    analysis_counts = await session.execute(
        select(BiasAnalysis.analysis_type, func.count(BiasAnalysis.id)).group_by(
            BiasAnalysis.analysis_type
        )
    )

    # Get fact-check verification distribution
    fact_check_distribution = await session.execute(
        select(FactCheck.verification_status, func.count(FactCheck.id)).group_by(
            FactCheck.verification_status
        )
    )

    # Get average accuracy scores
    avg_accuracy = await session.execute(
        select(func.avg(SourceBias.factual_accuracy)).where(
            SourceBias.factual_accuracy.is_not(None)
        )
    )

    return {
        "bias_distribution": dict(bias_distribution.all()),
        "analysis_counts": dict(analysis_counts.all()),
        "fact_check_distribution": dict(fact_check_distribution.all()),
        "average_factual_accuracy": float(avg_accuracy.scalar() or 0.0),
        "total_academic_sources": await session.scalar(
            select(func.count(AcademicSource.id))
        ),
    }


@router.get("/alternative-perspectives")
async def get_recent_alternatives(
    limit: int = 20, session: AsyncSession = Depends(get_session)
) -> List[AlternativePerspectiveOut]:
    """Get recent alternative perspectives."""

    alternatives = await session.execute(
        select(AlternativePerspective)
        .order_by(AlternativePerspective.created_at.desc())
        .limit(limit)
    )

    return [
        AlternativePerspectiveOut.model_validate(ap) for ap in alternatives.scalars()
    ]
