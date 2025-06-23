#!/usr/bin/env python3
"""
Bias Loader Script

Loads bias ratings from CSV file into the source_bias table.
Supports upsert operations (insert new, update existing).

Usage:
    python -m app.etl.load_bias data/bias_ratings.csv

CSV Format:
    name,bias_score,bias_label
    CNN,-0.234,left
    Fox News,0.456,right
    Reuters,0.001,center
"""
import asyncio
import csv
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import async_session

# Configure structured logging
logger = structlog.get_logger(__name__)


class BiasRecord:
    """Data class for bias record from CSV."""

    def __init__(
        self, name: str, bias_score: Optional[float], bias_label: Optional[str]
    ):
        self.name = name.strip()
        self.bias_score = bias_score
        self.bias_label = bias_label.strip() if bias_label else None

    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> "BiasRecord":
        """Create BiasRecord from CSV row dictionary."""
        name = row.get("name", "").strip()
        if not name:
            raise ValueError("Name field is required and cannot be empty")

        # Parse bias_score
        bias_score = None
        bias_score_str = row.get("bias_score", "").strip()
        if bias_score_str:
            try:
                bias_score = float(bias_score_str)
                # Validate range
                if bias_score < -1.0 or bias_score > 1.0:
                    raise ValueError(
                        f"bias_score must be between -1.0 and 1.0, got {bias_score}"
                    )
            except ValueError as e:
                raise ValueError(f"Invalid bias_score '{bias_score_str}': {e}")

        # Parse bias_label
        bias_label = row.get("bias_label", "").strip().lower()
        if bias_label and bias_label not in ("left", "center", "right", "unknown"):
            raise ValueError(
                f"bias_label must be one of: left, center, right, unknown. Got: {bias_label}"
            )

        return cls(name=name, bias_score=bias_score, bias_label=bias_label)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database operations."""
        return {
            "name": self.name,
            "bias_score": self.bias_score,
            "bias_label": self.bias_label,
        }


async def load_csv_file(file_path: Path) -> List[BiasRecord]:
    """Load and validate CSV file."""
    logger.info("Loading CSV file", file_path=str(file_path))

    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    records = []

    try:
        with open(file_path, "r", encoding="utf-8") as csvfile:
            # Detect if file has header
            sample = csvfile.read(1024)
            csvfile.seek(0)
            csv.Sniffer().has_header(sample)

            reader = csv.DictReader(csvfile)

            # Validate required columns
            required_columns = {"name", "bias_score", "bias_label"}
            if not required_columns.issubset(reader.fieldnames or []):
                raise ValueError(f"CSV must contain columns: {required_columns}")

            for line_num, row in enumerate(
                reader, start=2
            ):  # Start at 2 since header is line 1
                try:
                    record = BiasRecord.from_csv_row(row)
                    records.append(record)
                except ValueError as e:
                    logger.error(
                        "Invalid CSV row", line=line_num, error=str(e), row=row
                    )
                    raise ValueError(f"Line {line_num}: {e}")

    except Exception as e:
        logger.error("Failed to load CSV file", error=str(e))
        raise

    logger.info("CSV file loaded successfully", total_records=len(records))
    return records


async def get_existing_names(session: AsyncSession, names: List[str]) -> set[str]:
    """Get set of existing bias names from database."""
    if not names:
        return set()

    # Use raw SQL for better performance with large lists
    escaped_names = [name.replace("'", "''") for name in names]
    placeholders = ",".join([f"'{name}'" for name in escaped_names])
    query = text(f"SELECT name FROM source_bias WHERE name IN ({placeholders})")

    result = await session.execute(query)
    existing_names = {row[0] for row in result}

    logger.info(
        "Checked existing records",
        total_names=len(names),
        existing_count=len(existing_names),
    )

    return existing_names


async def bulk_upsert_bias_records(
    session: AsyncSession, records: List[BiasRecord]
) -> tuple[int, int]:
    """
    Bulk upsert bias records using efficient approach.
    Returns (inserted_count, updated_count).
    """
    if not records:
        return 0, 0

    logger.info("Starting bulk upsert", total_records=len(records))

    # Get existing names to determine inserts vs updates
    all_names = [record.name for record in records]
    existing_names = await get_existing_names(session, all_names)

    # Separate records into insert and update batches
    insert_records = []
    update_records = []

    for record in records:
        if record.name in existing_names:
            update_records.append(record)
        else:
            insert_records.append(record)

    inserted_count = 0
    updated_count = 0

    # Bulk insert new records
    if insert_records:
        insert_mappings = [record.to_dict() for record in insert_records]
        await session.execute(
            text(
                """
                INSERT INTO source_bias (name, bias_score, bias_label)
                VALUES (:name, :bias_score, :bias_label)
            """
            ),
            insert_mappings,
        )
        inserted_count = len(insert_records)
        logger.info("Bulk insert completed", count=inserted_count)

    # Bulk update existing records
    if update_records:
        for record in update_records:
            await session.execute(
                text(
                    """
                    UPDATE source_bias
                    SET bias_score = :bias_score,
                        bias_label = :bias_label,
                        updated_at = NOW()
                    WHERE name = :name
                """
                ),
                record.to_dict(),
            )
        updated_count = len(update_records)
        logger.info("Bulk update completed", count=updated_count)

    # Commit all changes
    await session.commit()

    logger.info(
        "Bulk upsert completed successfully",
        inserted=inserted_count,
        updated=updated_count,
        total=inserted_count + updated_count,
    )

    return inserted_count, updated_count


async def main() -> None:
    """Main entry point for bias loader."""
    if len(sys.argv) != 2:
        logger.error("Usage: python -m app.etl.load_bias <csv_file_path>")
        sys.exit(1)

    csv_file_path = Path(sys.argv[1])

    try:
        logger.info("Starting bias data load", csv_file=str(csv_file_path))

        # Load and validate CSV data
        records = await load_csv_file(csv_file_path)

        if not records:
            logger.warning("No records found in CSV file")
            sys.exit(0)

        # Process records in database
        async with async_session() as session:
            inserted_count, updated_count = await bulk_upsert_bias_records(
                session, records
            )

        # Log final results
        logger.info(
            "Bias data load completed successfully",
            inserted=inserted_count,
            updated=updated_count,
            total=len(records),
        )

        print(
            f"✅ Load completed: Inserted {inserted_count} / Updated {updated_count} rows"
        )
        sys.exit(0)

    except FileNotFoundError as e:
        logger.error("File not found", error=str(e))
        print(f"❌ Error: {e}")
        sys.exit(1)

    except ValueError as e:
        logger.error("Data validation error", error=str(e))
        print(f"❌ Validation Error: {e}")
        sys.exit(1)

    except Exception as e:
        logger.error("Unexpected error during bias load", error=str(e), exc_info=True)
        print(f"❌ Unexpected Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Import logging configuration
    import app.logging  # noqa: F401

    asyncio.run(main())
