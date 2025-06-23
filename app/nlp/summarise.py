from anthropic import AsyncAnthropic
from sqlalchemy import select

from app.models import Cluster, Narrative, Source, cluster_sources

ANTHROPIC_MODEL = "claude-3-haiku-20240307"  # or whatever tier you have
client = AsyncAnthropic()

SYSTEM_PROMPT = (
    "You are an assistant that writes SHORT, neutral summaries of "
    "clusters of news headlines and social-media posts. Keep it to one sentence."
)


async def summarise_clusters(session):
    stmt = select(Cluster).where(~Cluster.narratives.any())
    clusters = (await session.execute(stmt)).scalars().all()

    for cluster in clusters:
        # Pull up to 20 snippets
        texts = (
            await session.scalars(
                select(Source.raw_text)
                .join(Source.embeddings)
                .join(cluster_sources)
                .where(cluster_sources.c.cluster_id == cluster.id)
                .limit(20)
            )
        ).all()
        prompt = "\n\n".join(texts[:20])

        try:
            response = await client.messages.create(
                model=ANTHROPIC_MODEL,
                system=SYSTEM_PROMPT,
                max_tokens=128,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )
            summary = response.content[0].text.strip()
        except Exception as exc:
            # simple back-off / retry left as TODO
            print(f"Anthropic error: {exc}")
            continue

        narrative = Narrative(cluster_id=cluster.id, summary=summary)
        session.add(narrative)
    await session.commit()
