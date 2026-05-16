from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.core.middleware import (
    GlobalExceptionMiddleware, 
    RequestContextMiddleware
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Manages the application lifecycle events.

    This context manager handles logic that needs to run before the application
    starts (e.g., database connection pooling) and after it shuts down
    (e.g., closing connections).

    Args:
        _: The FastAPI application instance
    """

    # Startup logic goes here(e.g. await init_db())
    yield
    # Shutdown logic goes here (e.g. await close_db())

def create_app() -> FastAPI:
    """
    Initializes and configures the FastAPI application instance.

    This factory function handles the assembly of the application by:
        1. Setting up core metadata (title, version).
        2. Registering the lifespan context manager.
        3. Attaching global middlewares (Exception handling, Context, CORS)
        4. Including API versioned routers.
    
    Returns:
        FastAPI: A fully configured FastAPI application instance.
    """

    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan
    )

    # Custom Middleware: Handles global try-except blocks for unhandled errors
    application.add_middleware(middleware_class=GlobalExceptionMiddleware)
    
    # Custom Middleware: Manages request-scoped state or correlation IDs
    application.add_middleware(middleware_class=RequestContextMiddleware)

    # Security: Configure Cross-Origin Resource Sharing
    application.add_middleware(
        middleware_class=CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    # Routing: Attach the primary V1 router with the configured prefix
    application.include_router(
        router=api_router,
        prefix=settings.API_V1_PREFIX
    )

    return application

# Entry point for ASGI servers (like Uvicorn)
app = create_app()
