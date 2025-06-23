import asyncio
import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import get_session
from app.ingest import ingest_all
from app.pipeline import main as pipeline_main

logger = logging.getLogger(__name__)

router = APIRouter()


class RefreshRequest(BaseModel):
    sources: str


class RefreshResponse(BaseModel):
    status: str
    message: str
    task_id: str


# Track running refresh tasks
_running_tasks: Dict[str, asyncio.Task] = {}


async def run_full_refresh() -> None:
    """
    Run the complete refresh process: ingest all sources, then run pipeline.
    This is the background task that performs the actual work.
    """
    task_id = f"refresh_{asyncio.current_task().get_name()}"
    logger.info(f"Starting full refresh task: {task_id}")

    try:
        # Get database session
        session_generator = get_session()
        db = await session_generator.__anext__()

        try:
            logger.info("Running full ingestion (all sources)")
            # Run complete ingestion: RSS + social media + processing
            await ingest_all(db)

            logger.info("Ingestion complete, running pipeline")
            # Note: pipeline_main expects to create its own session
            # so we close this one first
            await db.close()

            # Run the pipeline processing
            await pipeline_main()

            logger.info(f"Full refresh task completed successfully: {task_id}")

        except Exception as e:
            logger.error(f"Error during refresh task {task_id}: {str(e)}")
            raise
        finally:
            # Ensure database session is closed
            await db.close()

    except Exception as e:
        logger.error(f"Full refresh task {task_id} failed: {str(e)}")
    finally:
        # Clean up task reference
        if task_id in _running_tasks:
            del _running_tasks[task_id]


@router.post("/refresh", response_model=RefreshResponse, status_code=202)
async def refresh_sources(request: RefreshRequest) -> RefreshResponse:
    """
    Trigger a background refresh of data sources and processing pipeline.

    Args:
        request: RefreshRequest with sources type

    Returns:
        RefreshResponse with task information

    Raises:
        HTTPException: If invalid sources type or task creation fails
    """
    logger.info(f"Refresh request received: {request.sources}")

    # Validate request
    if request.sources != "all":
        raise HTTPException(
            status_code=400, detail="Only 'all' sources refresh is currently supported"
        )

    # Check if a refresh task is already running
    active_tasks = [task for task in _running_tasks.values() if not task.done()]
    if active_tasks:
        raise HTTPException(
            status_code=409,
            detail="A refresh task is already running. Please wait for it to complete.",
        )

    try:
        # Create and start the background task
        task = asyncio.create_task(run_full_refresh())
        task_id = f"refresh_{task.get_name()}"

        # Store task reference
        _running_tasks[task_id] = task

        logger.info(f"Created refresh task: {task_id}")

        return RefreshResponse(
            status="accepted",
            message=f"Refresh task started for sources: {request.sources}",
            task_id=task_id,
        )

    except Exception as e:
        logger.error(f"Failed to create refresh task: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start refresh task: {str(e)}"
        )


@router.get("/refresh/status")
async def get_refresh_status() -> Dict[str, Any]:
    """
    Get the status of running refresh tasks.

    Returns:
        Dictionary with task status information
    """
    # Clean up completed tasks
    completed_tasks = [
        task_id for task_id, task in _running_tasks.items() if task.done()
    ]
    for task_id in completed_tasks:
        del _running_tasks[task_id]

    active_tasks = [
        {
            "task_id": task_id,
            "status": "running" if not task.done() else "completed",
            "done": task.done(),
        }
        for task_id, task in _running_tasks.items()
    ]

    return {
        "active_tasks": active_tasks,
        "total_active": len([t for t in active_tasks if t["status"] == "running"]),
    }
