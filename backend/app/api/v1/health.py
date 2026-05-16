import psutil
import time

from datetime import(
    datetime, 
    timezone
)

from fastapi import (
    APIRouter, 
    Depends, 
    Response, 
    status
)

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import get_db
from app.schemas import (
    HealthResponse, 
    SystemMetrics, 
    DatabaseHealth
)


router = APIRouter(
    tags=["Health"],
)

# Captures the precise moment the module is loaded to calculate uptime.
START_TIME = time.time()


@router.get("/health", 
    response_model=HealthResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK
)
async def health_check(
    response: Response, 
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Performs a comprehensive diagnostic of the application and its dependencies.

    This endpoint is used by load balancers, container orchestrators (like Kubernetes),
    and monitoring tools to determine if the service is capable of handling traffic.
    It checks:
    1. Database connectivity and latency.
    2. System resource utilization (CPU/Memory).
    3. Application uptime and version metadata.

    Args:
        response: FastAPI response object to dynamically set status codes.
        db: Asynchronous database session dependency.

    Returns:
        dict: A nested dictionary containing status, system metrics, and dependency health.
    """

    health_status = "healthy"

    # --- Dependency Check: Database ---
    try:
        # High-resolution timer for latency measurement
        database_start_time = time.perf_counter()

        # Executes a lightweight "ping" query to verify the connection is active
        await db.execute(text("SELECT 1"))

        database_latency = (time.perf_counter() - database_start_time) * 1000

        db_health = DatabaseHealth(
            status="healthy",
            latency_ms=round(database_latency, 2)
        )
    
    except Exception as ex:
        # If the database is down, the entire service is considered 'unhealthy'
        health_status = "unhealthy"

        db_health = DatabaseHealth(
            status="unhealthy",
            error=str(ex)
        )

        # Set 503 so automated systems know the service cannot fulfill requests
        response.status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    # --- System Metrics ---
    memory = psutil.virtual_memory()

    system_metrics = SystemMetrics(
        cpu_usage_percent=psutil.cpu_percent(interval=None),
        memory_usage_percent=memory.percent,
        memory_available_mb=round(memory.available / (1024 * 1024), 2)
    )

    # --- Final Payload Construction ---
    return HealthResponse(
        status=health_status,
        application=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc),
        uptime_seconds=round(time.time() - START_TIME, 2),
        system=system_metrics,
        dependencies={"database": db_health}
    )