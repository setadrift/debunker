import asyncio

from sqlalchemy import text

from app.db import AsyncSessionLocal
from app.models import Cluster, Embedding, Narrative, Source


async def clear_data():
    async with AsyncSessionLocal() as session:
        print("--- Clearing Data ---")
        async with session.begin():
            await session.execute(
                text(
                    f"TRUNCATE TABLE {Narrative.__tablename__} RESTART IDENTITY CASCADE"
                )
            )
            await session.execute(
                text(f"TRUNCATE TABLE {Cluster.__tablename__} RESTART IDENTITY CASCADE")
            )
            await session.execute(
                text(
                    f"TRUNCATE TABLE {Embedding.__tablename__} RESTART IDENTITY CASCADE"
                )
            )
            await session.execute(
                text(f"TRUNCATE TABLE {Source.__tablename__} RESTART IDENTITY CASCADE")
            )
        print("--- Data Cleared ---")


if __name__ == "__main__":
    asyncio.run(clear_data())
