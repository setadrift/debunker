from fastapi import APIRouter, Depends, status

from app.auth import current_superuser
from app.worker import celery_app

router = APIRouter()


@router.post(
    "/refresh",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(current_superuser)],
)
async def refresh_all():
    celery_app.send_task("app.tasks.full_refresh")
    return {"detail": "Refresh started"}
