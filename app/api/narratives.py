from datetime import date, datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Embedding, Narrative, Source, cluster_sources

router = APIRouter()


class NarrativeResponse(BaseModel):
    id: int
    summary: str
    first_seen: datetime
    last_seen: datetime
    source_count: int


class SourceDetail(BaseModel):
    id: int
    platform: str
    text_excerpt: str
    timestamp: datetime
    url: str
    engagement: int


class TimelineEvent(BaseModel):
    date: date
    mentions: int


class NarrativeDetailResponse(BaseModel):
    summary: str
    sources: List[SourceDetail]
    timeline: List[TimelineEvent]


@router.get("/narratives")
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
        )
        .join(Narrative.cluster)
        .join(cluster_sources, Narrative.cluster_id == cluster_sources.c.cluster_id)
        .join(Embedding, cluster_sources.c.embedding_id == Embedding.id)
        .join(Source, Embedding.source_id == Source.id)
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
        .join(Embedding)
        .join(cluster_sources)
        .where(cluster_sources.c.cluster_id == narrative.cluster_id)
        .order_by(Source.created_at.desc())
    )
    sources_result = await session.execute(sources_stmt)
    sources = sources_result.scalars().all()

    source_details = [
        SourceDetail(
            id=s.id,
            platform=s.platform,
            text_excerpt=s.raw_text[:100],
            timestamp=s.created_at,
            url=s.url,
            engagement=0,
        )
        for s in sources
    ]

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
    )
