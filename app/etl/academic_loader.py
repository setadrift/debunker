#!/usr/bin/env python3
"""
Academic Source Loader for bias analysis and fact-checking.
"""
import asyncio
import csv
import sys
from pathlib import Path
from typing import Dict, List

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.models import AcademicSource

logger = structlog.get_logger(__name__)


class AcademicRecord:
    def __init__(self, title: str, source_type: str = "academic_paper", **kwargs):
        self.title = title.strip()
        self.authors = kwargs.get("authors", "").strip() or None
        self.publication_year = self._parse_int(kwargs.get("publication_year"))
        self.doi = kwargs.get("doi", "").strip() or None
        self.abstract = kwargs.get("abstract", "").strip() or None
        self.source_type = source_type.strip()
        self.url = kwargs.get("url", "").strip() or None
        self.keywords = self._parse_keywords(kwargs.get("keywords", ""))
        self.credibility_score = self._parse_float(kwargs.get("credibility_score"))
        self.citation_count = self._parse_int(kwargs.get("citation_count"))
        self.full_text = kwargs.get("full_text", "").strip() or None

    def _parse_int(self, value):
        try:
            return int(value) if value and str(value).strip() else None
        except ValueError:
            return None

    def _parse_float(self, value):
        try:
            return float(value) if value and str(value).strip() else None
        except ValueError:
            return None

    def _parse_keywords(self, value):
        if not value:
            return []
        return [k.strip() for k in str(value).split(",") if k.strip()]

    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> "AcademicRecord":
        title = row.get("title", "").strip()
        if not title:
            raise ValueError("Title field is required")

        # Remove title from row to avoid duplicate keyword argument
        clean_row = {k: v for k, v in row.items() if k != "title"}
        return cls(title=title, **clean_row)

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "authors": self.authors,
            "publication_year": self.publication_year,
            "doi": self.doi,
            "abstract": self.abstract,
            "source_type": self.source_type,
            "url": self.url,
            "keywords": self.keywords,
            "credibility_score": self.credibility_score,
            "citation_count": self.citation_count,
            "full_text": self.full_text,
        }


async def load_csv_file(file_path: Path) -> List[AcademicRecord]:
    """Load academic sources from CSV."""
    logger.info("Loading academic sources", file_path=str(file_path))

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    records = []
    with open(file_path, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for line_num, row in enumerate(reader, start=2):
            try:
                record = AcademicRecord.from_csv_row(row)
                records.append(record)
            except ValueError as e:
                logger.error("Invalid row", line=line_num, error=str(e))
                raise ValueError(f"Line {line_num}: {e}")

    logger.info("Loaded academic sources", total=len(records))
    return records


async def bulk_insert_records(
    session: AsyncSession, records: List[AcademicRecord]
) -> int:
    """Bulk insert academic records."""
    if not records:
        return 0

    # Convert records to ORM objects instead of using raw SQL
    academic_sources = []
    for record in records:
        data = record.to_dict()
        academic_source = AcademicSource(**data)
        academic_sources.append(academic_source)

    # Use ORM to handle JSON serialization properly
    session.add_all(academic_sources)
    await session.commit()

    logger.info("Bulk insert completed", count=len(records))
    return len(records)


async def main() -> None:
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python -m app.etl.academic_loader <csv_file_path>")
        sys.exit(1)

    csv_file_path = Path(sys.argv[1])

    try:
        records = await load_csv_file(csv_file_path)

        async with AsyncSessionLocal() as session:
            inserted = await bulk_insert_records(session, records)

        print(f"✅ Loaded {inserted} academic sources from {csv_file_path}")

    except Exception as e:
        print(f"❌ Failed to load academic sources: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
