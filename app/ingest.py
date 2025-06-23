from __future__ import annotations

import asyncio
import pickle
import sys
# datetime imported for type annotations and date handling
from typing import Any, Dict, List

import hdbscan
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_session
from app.models import Cluster, Embedding, Source
from app.models import cluster_sources as cluster_sources_table
from app.nlp.summarise import summarise_clusters
from app.scraper import collect_latest_news
from app.scrapers.reddit import RedditScraper
from app.scrapers.twitter import TwitterScraper
from app.scrapers.youtube import YouTubeScraper


async def ingest_news(db: AsyncSession):
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


async def generate_embeddings(session: AsyncSession):
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


async def cluster_sources(session: AsyncSession):
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


async def ingest_social_media(db: AsyncSession):
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


async def ingest_all(db: AsyncSession):
    """
    Run all ingestion processes: RSS news + social media scrapers.
    """
    print("=== Starting complete ingestion process ===")

    # First ingest RSS news
    await ingest_news(db)

    # Then ingest social media
    await ingest_social_media(db)

    # Generate embeddings for all new content
    await generate_embeddings(db)

    # Re-cluster all sources
    await cluster_sources(db)

    # Generate cluster summaries
    await summarise_clusters(db)

    print("=== Complete ingestion process finished ===")


async def main():
    """CLI entry point for the ingestion script."""
    if len(sys.argv) < 2:
        print("Usage: python -m app.ingest [news|all]")
        print("  news - Ingest RSS news feeds only")
        print("  all  - Ingest all sources (RSS + social media scrapers)")
        sys.exit(1)

    command = sys.argv[1]

    if command not in ["news", "all"]:
        print(f"Unknown command: {command}")
        print("Usage: python -m app.ingest [news|all]")
        sys.exit(1)

    # Get a database session
    session_generator = get_session()
    db = await session_generator.__anext__()
    try:
        if command == "news":
            # Original news-only workflow
            await ingest_news(db)
            await generate_embeddings(db)
            await cluster_sources(db)
            await summarise_clusters(db)
        elif command == "all":
            # Complete ingestion workflow
            await ingest_all(db)
    finally:
        await db.close()


if __name__ == "__main__":
    # Ensure the script is run in an environment with the project root in PYTHONPATH
    # e.g., PYTHONPATH=. python -m app.ingest news
    asyncio.run(main())
