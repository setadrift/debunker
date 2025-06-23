import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from app.ingest import cluster_sources, generate_embeddings
from app.models import Cluster, Embedding, Narrative, Source
from app.nlp.summarise import summarise_clusters

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def create_fresh_engine():
    """Create a completely fresh engine with no statement caching."""
    return create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=60,  # Very short recycle time
        pool_size=1,
        max_overflow=0,
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "command_timeout": 60,
            "server_settings": {
                "application_name": (
                    f"ii_pipeline_{asyncio.current_task().get_name()}"
                    if asyncio.current_task()
                    else "ii_pipeline_main"
                ),
                "search_path": "public",
            },
        },
    )


async def main():
    """
    Pipeline CLI that orchestrates the entire process:
    1. Generate embeddings for sources without embeddings
    2. Cluster sources using HDBSCAN
    3. Generate narrative summaries for clusters

    Logs counts after each stage.
    """
    print("Starting pipeline...")

    # Log initial counts
    await log_counts("Initial state")

    # Stage 1: Generate embeddings
    print("\n=== Stage 1: Generating embeddings ===")
    await run_with_fresh_engine(generate_embeddings)
    await log_counts("After embedding generation")

    # Stage 2: Cluster sources
    print("\n=== Stage 2: Clustering sources ===")
    await run_with_fresh_engine(cluster_sources)
    await log_counts("After clustering")

    # Stage 3: Generate summaries
    print("\n=== Stage 3: Generating summaries ===")
    await run_with_fresh_engine(summarise_clusters)
    await log_counts("After summarization")

    print("\nPipeline complete!")


async def run_with_fresh_engine(func):
    """Run a function with a completely fresh engine and session."""
    engine = create_fresh_engine()
    SessionLocal = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    try:
        async with SessionLocal() as session:
            await func(session)
            await session.commit()
    except Exception as e:
        print(f"Error in {func.__name__}: {e}")
        raise
    finally:
        await engine.dispose()


async def log_counts(stage: str):
    """Log counts of sources, embeddings, clusters, and narratives at current stage."""
    engine = create_fresh_engine()
    SessionLocal = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    try:
        async with SessionLocal() as session:
            # Count sources
            source_count = await session.scalar(select(func.count(Source.id)))

            # Count embeddings
            embedding_count = await session.scalar(select(func.count(Embedding.id)))

            # Count clusters
            cluster_count = await session.scalar(select(func.count(Cluster.id)))

            # Count narratives
            narrative_count = await session.scalar(select(func.count(Narrative.id)))

            print(f"\n{stage}:")
            print(f"  Sources: {source_count}")
            print(f"  Embeddings: {embedding_count}")
            print(f"  Clusters: {cluster_count}")
            print(f"  Narratives: {narrative_count}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
