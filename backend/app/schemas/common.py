from datetime import datetime

from pydantic import BaseModel

from typing import Dict


class DatabaseHealth(BaseModel):
    """
    Data serialization schema representing the state of an external database dependency.

    Captures connection availability, response latency, and explicit system errors 
    to simplify remote debugging and connection performance monitoring.
    """
    
    # The availability status of the target database node (e.g., "healthy", "unhealthy").
    status: str
    
    # The time taken in milliseconds to execute a simple ping query (e.g., 'SELECT 1').
    # Set to None if the network connection fails or timeouts occur.
    latency_ms: float | None = None
    
    # Captures the raw exception or failure message if the connection is broken.
    # Stored as None when the database node is performing within parameters.
    error: str | None = None

class SystemMetrics(BaseModel):
    """
    Data serialization schema representing host server physical resource utilization.

    Exposes low-level telemetry metrics captured from the operating system 
    environment layer to aid in automated horizontal scaling assessments.
    """

    # Total CPU utilization percentage across all allocated processor cores.
    cpu_usage_percent: float

    # Total system RAM consumption ratio relative to maximum capacity.
    memory_usage_percent: float
    
    # Total remaining unallocated operational RAM footprint available in megabytes.
    memory_available_mb: float

class HealthResponse(BaseModel):
    """
    Top-level data serialization schema for global application diagnostic reporting.

    Combines baseline application manifest details, real-time host hardware usage, 
    and multi-dependency statuses into a single structured payload.
    """

    # Overall systemic state indicator (typically "healthy", "degraded", or "unhealthy").
    status: str 

    # The official name identifier of the running service instance (e.g., "secure-deal-room-api").
    application: str

    # The current deployed build version string extracted from system metadata (e.g., "1.2.4").
    version: str

    # The targeted host tier context the app is running under (e.g., "production", "development").
    environment: str

    # The exact ISO timestamp generated when the health snapshot was calculated by the worker.
    timestamp: datetime

    # Total duration in seconds elapsed since the primary ASGI server process was initialized.
    uptime_seconds: float

    # Nested infrastructure resources payload covering CPU and memory metrics.
    system: SystemMetrics

    # A dynamic mapping of named network dependencies and their respective check results.
    # Keys represent dependency nicknames (e.g., "supabase_postgres", "redis_cache").
    dependencies: Dict[str, DatabaseHealth]
