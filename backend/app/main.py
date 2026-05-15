from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.middleware import GlobalExceptionMiddleware, RequestContextMiddleware
from app.config import settings



@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Handled application startup and shutdown events.
    """

    yield

def create_app() -> FastAPI:
    """
    Application factory.
    """

    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan
    )

    application.add_middleware(GlobalExceptionMiddleware)
    application.add_middleware(RequestContextMiddleware)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    application.include_router(
        router=api_router,
        prefix=settings.API_V1_PREFIX
    )

    return application

app = create_app()
