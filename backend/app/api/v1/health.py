import time
from datetime import datetime, timezone

import psutil
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import get_db

router = APIRouter(
    tags=["Health"],
)

START_TIME = time.time()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(response: Response, db: AsyncSession = Depends(get_db)) -> dict:
    """
    Detailed application health check.
    """

    health_status = "healthy"

    dependencies: dict = {}

    try:
        database_start_time = time.perf_counter()

        await db.execute(text("SELECT 1"))

        database_latency = (time.perf_counter() - database_start_time) * 1000

        dependencies["database"] = {
            "status": "healthy",
            "latency_ms": round(database_latency, 2)
        }
    
    except Exception as ex:
        health_status = "unhealthy"

        dependencies["database"] = {
            "status": "unhealthy",
            "error": str(ex),
        }

        response.status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    memory = psutil.virtual_memory()

    system_metrics = {
        "cpu_usage_percent": psutil.cpu_percent(
            interval=None,
        ),
        "memory_usage_percent": memory.percent,
        "memory_available_mb": round(
            memory.available / (1024 * 1024),
            2,
        ),
    }

    return {
        "status": health_status,
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(
            timezone.utc,
        ).isoformat(),
        "uptime_seconds": round(
            time.time() - START_TIME,
            2,
        ),
        "system": system_metrics,
        "dependencies": dependencies,
    }