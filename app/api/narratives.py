from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi_cache.decorator import cache
from pydantic import BaseModel
from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_session
from app.models import (Embedding, Narrative, Source, SourceBias,
                        SourceBiasOut, SourceOut, cluster_sources)

router = APIRouter()


class NarrativeResponse(BaseModel):
    id: int
    summary: str
    first_seen: datetime
    last_seen: datetime
    source_count: int
    cluster_bias_avg: Optional[float]


class TimelineEvent(BaseModel):
    date: date
    mentions: int


class NarrativeDetailResponse(BaseModel):
    summary: str
    sources: List[SourceOut]
    timeline: List[TimelineEvent]
    cluster_bias_avg: Optional[float]


@router.get("/narratives")
@cache(expire=60)
async def list_narratives(
    session: AsyncSession = Depends(get_session),
) -> List[NarrativeResponse]:
    stmt = (
        select(
            Narrative.id,
            Narrative.summary,
            func.min(Source.created_at).label("first_seen"),
            func.max(Source.created_at).label("last_seen"),
            func.count(Source.id).label("source_count"),
            func.round(
                func.avg(SourceBias.bias_score).filter(
                    SourceBias.bias_score.is_not(None)
                ),
                2,
            ).label("cluster_bias_avg"),
            func.count(SourceBias.bias_score.distinct())
            .filter(SourceBias.bias_score.is_not(None))
            .label("bias_count"),
        )
        .join(Narrative.cluster)
        .join(cluster_sources, Narrative.cluster_id == cluster_sources.c.cluster_id)
        .join(Embedding, cluster_sources.c.embedding_id == Embedding.id)
        .join(Source, Embedding.source_id == Source.id)
        .outerjoin(SourceBias, Source.bias_id == SourceBias.id)
        .group_by(Narrative.id)
        .order_by(func.max(Source.created_at).desc())
    )
    results = await session.execute(stmt)
    return [
        NarrativeResponse(
            id=row.id,
            summary=row.summary,
            first_seen=row.first_seen,
            last_seen=row.last_seen,
            source_count=row.source_count,
            cluster_bias_avg=row.cluster_bias_avg if row.bias_count >= 2 else None,
        )
        for row in results
    ]


@router.get("/narratives/{narrative_id}")
async def get_narrative_detail(
    narrative_id: int, session: AsyncSession = Depends(get_session)
) -> NarrativeDetailResponse:
    narrative = await session.get(Narrative, narrative_id)
    if not narrative:
        raise HTTPException(status_code=404, detail="Narrative not found")

    sources_stmt = (
        select(Source)
        .options(selectinload(Source.bias))
        .join(Embedding)
        .join(cluster_sources)
        .where(cluster_sources.c.cluster_id == narrative.cluster_id)
        .order_by(Source.created_at.desc())
    )
    sources_result = await session.execute(sources_stmt)
    sources = sources_result.scalars().all()

    source_details = [
        SourceOut(
            id=s.id,
            platform=s.platform,
            text_excerpt=s.raw_text[:100],
            timestamp=s.created_at,
            url=s.url,
            engagement=0,
            bias=SourceBiasOut.model_validate(s.bias) if s.bias else None,
        )
        for s in sources
    ]

    # Calculate cluster bias average
    bias_scores = [
        s.bias.bias_score for s in sources if s.bias and s.bias.bias_score is not None
    ]
    cluster_bias_avg = None
    if len(bias_scores) >= 2:
        cluster_bias_avg = round(sum(bias_scores) / len(bias_scores), 2)

    timeline_stmt = (
        select(
            cast(Source.created_at, Date).label("date"),
            func.count(Source.id).label("mentions"),
        )
        .join(Embedding)
        .join(cluster_sources)
        .where(cluster_sources.c.cluster_id == narrative.cluster_id)
        .group_by(cast(Source.created_at, Date))
        .order_by(cast(Source.created_at, Date))
    )
    timeline_result = await session.execute(timeline_stmt)
    timeline_events = [
        TimelineEvent(date=row.date, mentions=row.mentions) for row in timeline_result
    ]

    return NarrativeDetailResponse(
        summary=narrative.summary,
        sources=source_details,
        timeline=timeline_events,
        cluster_bias_avg=cluster_bias_avg,
    )
