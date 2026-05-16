from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)

from app.config import settings

# Initialize the Async Engine
# url: Database connection string.
# echo: Enables SQL logging in dev mode for query debugging.
# connect_args: Low-level driver arguments (e.g., statement_cache_size=0 for PgBouncer compatibility).
engine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    connect_args={
        "statement_cache_size": 0,
    },
    pool_size=20,
    max_overflow=10,
    pool_recycle=3600,
    pool_pre_ping=True,
)

# Application-level session factory
# expire_on_commit=False: Prevents SQLAlchemy from trying to refresh objects 
# from the DB after a commit, which is essential for async workflows.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)