from __future__ import annotations

import asyncio
import os
import pickle
from typing import Any, Dict, List

import hdbscan
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import selectinload

from app.db import get_session
from app.models import Cluster, Embedding, Narrative, Source
from app.models import cluster_sources as cluster_sources_table
from app.nlp.summarise import summarise_clusters
from app.scraper import collect_latest_news
from app.scrapers.reddit import RedditScraper
from app.scrapers.twitter import TwitterScraper
from app.scrapers.youtube import YouTubeScraper
from app.worker import celery_app

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


# Celery Tasks
@celery_app.task
def ingest_news_task():
    """Celery task wrapper for ingest_news."""

    async def _task():
        session_generator = get_session()
        db = await session_generator.__anext__()
        try:
            await _ingest_news(db)
        finally:
            await db.close()

    asyncio.run(_task())


async def _ingest_news(db: AsyncSession):
    """
    Scrape latest news and insert new articles into the database.
    Skips articles if a source with the same URL already exists.
    """
    print("Collecting latest news from RSS feeds...")
    news_items = collect_latest_news()
    if not news_items:
        print("No new articles found.")
        return

    print(
        f"Found {len(news_items)} potentially new articles. Checking for duplicates..."
    )

    # Fetch all existing URLs from the DB to check for duplicates in memory
    existing_urls = (await db.execute(select(Source.url))).scalars().all()
    existing_urls_set = set(existing_urls)

    new_sources = []
    seen_urls_in_batch = set()  # Track URLs we've already processed in this batch

    for item in news_items:
        if item.url not in existing_urls_set and item.url not in seen_urls_in_batch:
            source = Source(
                platform=item.source_name,
                raw_text=item.text,
                url=item.url,
                meta={
                    "title": item.title,
                    "source_name": item.source_name,
                    "published_at": item.published_at.isoformat(),
                },
            )
            new_sources.append(source)
            seen_urls_in_batch.add(item.url)  # Mark this URL as seen in this batch
        elif item.url in seen_urls_in_batch:
            print(f"Skipping duplicate URL within batch: {item.url}")

    if not new_sources:
        print("No new articles to add after checking for duplicates.")
        return

    print(f"Adding {len(new_sources)} new sources to the database...")
    try:
        db.add_all(new_sources)
        await db.commit()
        print("Ingestion complete.")
    except Exception as e:
        print(f"Error during database insertion: {e}")
        await db.rollback()
        print("Transaction rolled back. Attempting to insert sources one by one...")

        # Try inserting one by one to identify and skip problematic entries
        successful_inserts = 0
        for source in new_sources:
            try:
                db.add(source)
                await db.commit()
                successful_inserts += 1
            except Exception as individual_error:
                print(f"Failed to insert source {source.url}: {individual_error}")
                await db.rollback()

        print(
            f"Successfully inserted {successful_inserts} out of {len(new_sources)} sources."
        )


@celery_app.task
def generate_embeddings_task():
    """Celery task wrapper for generate_embeddings."""

    async def _task():
        session_generator = get_session()
        session = await session_generator.__anext__()
        try:
            await _generate_embeddings(session)
        finally:
            await session.close()

    asyncio.run(_task())


async def _generate_embeddings(session: AsyncSession):
    """
    Generate embeddings for Source rows that don't have any embeddings yet.
    Uses sentence-transformers/paraphrase-MiniLM-L6-v2 model to create 384-dim embeddings.
    """
    print("Loading sentence transformer model...")
    model = SentenceTransformer("sentence-transformers/paraphrase-MiniLM-L6-v2")

    print("Finding sources without embeddings...")
    # Query sources that don't have any embeddings
    query = (
        select(Source)
        .outerjoin(Embedding, Source.id == Embedding.source_id)
        .where(Embedding.source_id.is_(None))
        .options(selectinload(Source.embeddings))
    )

    result = await session.execute(query)
    sources_without_embeddings = result.scalars().all()

    if not sources_without_embeddings:
        print("No sources found that need embeddings.")
        return

    print(f"Found {len(sources_without_embeddings)} sources needing embeddings.")

    # Prepare text for embedding (combine title and raw_text for better context)
    texts_to_embed: List[str] = []
    for source in sources_without_embeddings:
        # Use title from metadata if available, otherwise just raw_text
        title = source.meta.get("title", "") if source.meta else ""
        if title:
            text = f"{title}\n\n{source.raw_text}"
        else:
            text = source.raw_text
        texts_to_embed.append(text)

    print("Generating embeddings...")
    # Generate embeddings in batch for efficiency
    embeddings = model.encode(texts_to_embed, convert_to_numpy=True)
    # Convert to float32 for consistency
    embeddings = embeddings.astype(np.float32)

    print(f"Generated {len(embeddings)} embeddings with shape {embeddings.shape}")

    # Create Embedding records
    new_embeddings = []
    for source, embedding_vector in zip(sources_without_embeddings, embeddings):
        # Convert numpy array to bytes using pickle for storage
        vector_bytes = pickle.dumps(embedding_vector)

        embedding_record = Embedding(source_id=source.id, vector=vector_bytes)
        new_embeddings.append(embedding_record)

    print(f"Storing {len(new_embeddings)} embeddings to database...")
    session.add_all(new_embeddings)
    await session.commit()
    print("Embedding generation complete.")


@celery_app.task
def cluster_sources_task():
    """Celery task wrapper for cluster_sources."""

    async def _task():
        session_generator = get_session()
        session = await session_generator.__anext__()
        try:
            await _cluster_sources(session)
        finally:
            await session.close()

    asyncio.run(_task())


async def _cluster_sources(session: AsyncSession):
    """
    Load all embeddings and run HDBSCAN clustering to group similar sources.
    Creates Cluster records and links embeddings via the cluster_sources association table.
    Handles noise points (cluster_id=None) appropriately.
    """
    print("Loading all embeddings for clustering...")

    # Load all embeddings from the database
    query = select(Embedding).options(selectinload(Embedding.source))
    result = await session.execute(query)
    embeddings_records = result.scalars().all()

    if not embeddings_records:
        print("No embeddings found for clustering.")
        return

    print(f"Found {len(embeddings_records)} embeddings to cluster.")

    # Convert stored embeddings back to numpy arrays
    embedding_vectors = []
    for embedding_record in embeddings_records:
        # Unpickle the stored numpy array
        vector = pickle.loads(embedding_record.vector)
        embedding_vectors.append(vector)

    # Convert to numpy matrix for clustering
    embedding_matrix = np.array(embedding_vectors, dtype=np.float32)
    print(f"Created embedding matrix with shape: {embedding_matrix.shape}")

    # Run HDBSCAN clustering
    print("Running HDBSCAN clustering...")
    clusterer = hdbscan.HDBSCAN(min_cluster_size=3, metric="euclidean")
    cluster_labels = clusterer.fit_predict(embedding_matrix)

    # Count clusters and noise points
    unique_labels = np.unique(cluster_labels)
    n_clusters = len(unique_labels[unique_labels >= 0])  # -1 indicates noise
    n_noise = len(cluster_labels[cluster_labels == -1])

    print(f"Found {n_clusters} clusters and {n_noise} noise points.")

    if n_clusters == 0:
        print("No clusters found. All points are noise.")
        return

    # Create Cluster records for each unique cluster (excluding noise -1)
    cluster_id_mapping = {}
    new_clusters = []

    for label in unique_labels:
        if label >= 0:  # Skip noise points (-1)
            cluster_record = Cluster()
            new_clusters.append(cluster_record)

    # Add clusters to session to get IDs
    session.add_all(new_clusters)
    await session.flush()  # Flush to get IDs without committing

    # Create mapping from HDBSCAN labels to actual cluster IDs
    cluster_idx = 0
    for label in unique_labels:
        if label >= 0:
            cluster_id_mapping[label] = new_clusters[cluster_idx].id
            cluster_idx += 1

    print(f"Created {len(new_clusters)} cluster records.")

    # Create associations between embeddings and clusters
    associations = []
    clustered_count = 0
    noise_count = 0

    for embedding_record, cluster_label in zip(embeddings_records, cluster_labels):
        if cluster_label >= 0:  # Not a noise point
            cluster_id = cluster_id_mapping[cluster_label]
            # Create association record
            association = {
                "embedding_id": embedding_record.id,
                "cluster_id": cluster_id,
            }
            associations.append(association)
            clustered_count += 1
        else:
            # Noise point - no cluster association
            noise_count += 1

    # Insert associations into the cluster_sources table
    if associations:
        await session.execute(cluster_sources_table.insert().values(associations))

    await session.commit()

    print("Clustering complete:")
    print(f"  - {clustered_count} embeddings assigned to {n_clusters} clusters")
    print(f"  - {noise_count} embeddings marked as noise (no cluster)")


@celery_app.task
def ingest_social_media_task():
    """Celery task wrapper for ingest_social_media."""

    async def _task():
        session_generator = get_session()
        db = await session_generator.__anext__()
        try:
            await _ingest_social_media(db)
        finally:
            await db.close()

    asyncio.run(_task())


async def _ingest_social_media(db: AsyncSession):
    """
    Run all social media scrapers and ingest their data with deduplication.
    Handles Twitter, Reddit, and YouTube scrapers.
    """
    print("Starting social media ingestion...")

    # Collect data from all scrapers
    all_scraped_data = []

    # Twitter scraper
    print("\n--- Running Twitter scraper ---")
    try:
        twitter_scraper = TwitterScraper()
        twitter_data = twitter_scraper.scrape_and_format(limit=50)
        all_scraped_data.extend(twitter_data)
        print(f"Twitter: Collected {len(twitter_data)} items")
    except Exception as e:
        print(f"Twitter scraper failed: {e}")

    # Reddit scraper
    print("\n--- Running Reddit scraper ---")
    try:
        reddit_scraper = RedditScraper()
        reddit_data = reddit_scraper.scrape_and_format(limit_per_subreddit=25)
        all_scraped_data.extend(reddit_data)
        print(f"Reddit: Collected {len(reddit_data)} items")
    except Exception as e:
        print(f"Reddit scraper failed: {e}")

    # YouTube scraper
    print("\n--- Running YouTube scraper ---")
    try:
        youtube_scraper = YouTubeScraper()
        youtube_data = youtube_scraper.scrape_and_format(limit=15)
        all_scraped_data.extend(youtube_data)
        print(f"YouTube: Collected {len(youtube_data)} items")
    except Exception as e:
        print(f"YouTube scraper failed: {e}")

    if not all_scraped_data:
        print("No data collected from any scraper.")
        return

    print(f"\nTotal items collected: {len(all_scraped_data)}")

    # Deduplicate and insert
    await _deduplicate_and_insert(db, all_scraped_data)


async def _deduplicate_and_insert(db: AsyncSession, scraped_data: List[Dict[str, Any]]):
    """
    Deduplicate scraped data by URL and external_id, then insert into database.

    Args:
        db: Database session
        scraped_data: List of formatted data from scrapers
    """
    print("Deduplicating scraped data...")

    # Extract all URLs and external_ids to check against database
    urls_to_check = [
        item.get("source_url") for item in scraped_data if item.get("source_url")
    ]
    external_ids_to_check = [
        item.get("external_id") for item in scraped_data if item.get("external_id")
    ]

    # Query existing sources by URL or external_id
    existing_query = select(Source.url, Source.meta).where(
        or_(
            Source.url.in_(urls_to_check) if urls_to_check else False,
            # Check external_id in metadata
            Source.meta.op("->>")("external_id").in_(external_ids_to_check)
            if external_ids_to_check
            else False,
        )
    )

    result = await db.execute(existing_query)
    existing_sources = result.all()

    # Create sets for fast lookup
    existing_urls = {row[0] for row in existing_sources if row[0]}
    existing_external_ids = {
        row[1].get("external_id")
        for row in existing_sources
        if row[1] and row[1].get("external_id")
    }

    print(
        f"Found {len(existing_urls)} existing URLs and {len(existing_external_ids)} existing external IDs"
    )

    # Deduplicate within the batch and against database
    new_sources = []
    seen_in_batch = set()
    duplicates_skipped = 0

    for item in scraped_data:
        # Create unique identifier for this item
        url = item.get("source_url", "")
        external_id = item.get("external_id", "")

        # Create a batch identifier combining URL and external_id
        batch_identifier = f"{item.get('platform', '')}:{external_id}:{url}"

        # Skip if already seen in this batch
        if batch_identifier in seen_in_batch:
            duplicates_skipped += 1
            continue

        # Skip if exists in database
        if url and url in existing_urls:
            duplicates_skipped += 1
            continue

        if external_id and external_id in existing_external_ids:
            duplicates_skipped += 1
            continue

        # Convert scraped data to Source model
        source = Source(
            platform=item.get("platform", "unknown"),
            raw_text=item.get("content", ""),
            url=url,
            meta={
                "title": item.get("title", ""),
                "author": item.get("author", ""),
                "external_id": external_id,
                "published_date": item.get("published_date").isoformat()
                if item.get("published_date")
                else None,
                "platform_metadata": item.get("metadata", {}),
            },
        )

        new_sources.append(source)
        seen_in_batch.add(batch_identifier)

    print(
        f"After deduplication: {len(new_sources)} new sources, {duplicates_skipped} duplicates skipped"
    )

    if not new_sources:
        print("No new sources to insert after deduplication.")
        return

    # Insert new sources
    print(f"Inserting {len(new_sources)} new sources...")
    try:
        db.add_all(new_sources)
        await db.commit()
        print("Social media ingestion complete.")
    except Exception as e:
        print(f"Error during database insertion: {e}")
        await db.rollback()

        # Try inserting one by one
        print("Attempting individual insertions...")
        successful_inserts = 0
        for source in new_sources:
            try:
                db.add(source)
                await db.commit()
                successful_inserts += 1
            except Exception as individual_error:
                source_id = source.url or source.meta.get("external_id", "unknown")
                print(f"Failed to insert source {source_id}: {individual_error}")
                await db.rollback()

        print(
            f"Successfully inserted {successful_inserts} out of {len(new_sources)} sources."
        )


@celery_app.task
def ingest_all_task():
    """Celery task wrapper for ingest_all."""

    async def _task():
        session_generator = get_session()
        db = await session_generator.__anext__()
        try:
            await _ingest_all(db)
        finally:
            await db.close()

    asyncio.run(_task())


async def _ingest_all(db: AsyncSession):
    """
    Run all ingestion processes: RSS news + social media scrapers.
    """
    print("=== Starting complete ingestion process ===")

    # First ingest RSS news
    await _ingest_news(db)

    # Then ingest social media
    await _ingest_social_media(db)

    # Generate embeddings for all new content
    await _generate_embeddings(db)

    # Re-cluster all sources
    await _cluster_sources(db)

    # Generate cluster summaries
    await summarise_clusters(db)

    print("=== Complete ingestion process finished ===")


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


@celery_app.task
def pipeline_main_task():
    """Celery task wrapper for pipeline main."""

    async def _task():
        await _pipeline_main()

    asyncio.run(_task())


async def _pipeline_main():
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
    await run_with_fresh_engine(_generate_embeddings)
    await log_counts("After embedding generation")

    # Stage 2: Cluster sources
    print("\n=== Stage 2: Clustering sources ===")
    await run_with_fresh_engine(_cluster_sources)
    await log_counts("After clustering")

    # Stage 3: Generate summaries
    print("\n=== Stage 3: Generating summaries ===")
    await run_with_fresh_engine(summarise_clusters)
    await log_counts("After summarization")

    print("\nPipeline complete!")


# CLI Wrapper Functions (use .apply_async() for synchronous execution)
async def ingest_news(db: AsyncSession):
    """CLI wrapper for ingest_news_task."""
    return ingest_news_task.apply_async()


async def generate_embeddings(session: AsyncSession):
    """CLI wrapper for generate_embeddings_task."""
    return generate_embeddings_task.apply_async()


async def cluster_sources(session: AsyncSession):
    """CLI wrapper for cluster_sources_task."""
    return cluster_sources_task.apply_async()


async def ingest_social_media(db: AsyncSession):
    """CLI wrapper for ingest_social_media_task."""
    return ingest_social_media_task.apply_async()


async def ingest_all(db: AsyncSession):
    """CLI wrapper for ingest_all_task."""
    return ingest_all_task.apply_async()


async def main():
    """CLI wrapper for pipeline_main_task."""
    return pipeline_main_task.apply_async()
