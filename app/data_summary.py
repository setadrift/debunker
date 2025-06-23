import asyncio

from sqlalchemy import func, select

from app.db import AsyncSessionLocal
from app.models import Narrative, Source


async def summarize_data():
    async with AsyncSessionLocal() as session:
        print("--- Data Summary ---")

        # Summarize Narratives
        narratives_stmt = select(Narrative.summary)
        narratives_result = await session.execute(narratives_stmt)
        narratives = narratives_result.scalars().all()
        print(f"\nFound {len(narratives)} Narratives:")
        for i, narrative in enumerate(narratives):
            print(f"  {i+1}. {narrative}")

        # Summarize Sources
        sources_stmt = select(
            Source.platform,
            func.count(Source.id).label("count"),
            func.min(Source.created_at).label("first_seen"),
            func.max(Source.created_at).label("last_seen"),
        ).group_by(Source.platform)
        sources_result = await session.execute(sources_stmt)
        sources_summary = sources_result.all()

        print("\nSource Breakdown:")
        for row in sources_summary:
            print(f"  - Platform: {row.platform}")
            print(f"    Count: {row.count}")
            print(f"    First Seen: {row.first_seen}")
            print(f"    Last Seen: {row.last_seen}")

        print("\n--- End of Summary ---")


if __name__ == "__main__":
    asyncio.run(summarize_data())
