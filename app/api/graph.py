from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_session
from app.models import Cluster, Embedding, Source

router = APIRouter()


class GraphNode(BaseModel):
    id: str
    platform: str
    engagement: int


class GraphLink(BaseModel):
    source: str
    target: str


class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    links: List[GraphLink]


@router.get("/graph", response_model=GraphResponse)
async def get_network_graph(
    session: AsyncSession = Depends(get_session),
) -> GraphResponse:
    """Return nodes and links for the network graph.

    * Nodes represent unique news sources (platform field).
    * Links connect two sources when they appear in the same cluster.
    * Engagement is the number of articles (Source rows) for that platform.
    """
    # Build node list with engagement counts
    node_stmt = select(
        Source.platform, func.count(Source.id).label("engagement")
    ).group_by(Source.platform)
    node_rows = await session.execute(node_stmt)
    node_map: dict[str, GraphNode] = {
        row.platform: GraphNode(
            id=row.platform, platform=row.platform, engagement=row.engagement
        )
        for row in node_rows
    }

    # Build links by iterating clusters → embeddings → sources
    clusters_stmt = select(Cluster).options(
        selectinload(Cluster.embeddings).selectinload(Embedding.source)
    )
    clusters_result = await session.execute(clusters_stmt)
    clusters = clusters_result.scalars().all()

    links_set: set[tuple[str, str]] = set()

    for cluster in clusters:
        platforms = {emb.source.platform for emb in cluster.embeddings if emb.source}
        # Add link for each unique pair in the cluster
        platforms_list = sorted(platforms)
        for i in range(len(platforms_list)):
            for j in range(i + 1, len(platforms_list)):
                links_set.add((platforms_list[i], platforms_list[j]))

    links = [GraphLink(source=s, target=t) for s, t in links_set]

    return GraphResponse(nodes=list(node_map.values()), links=links)
