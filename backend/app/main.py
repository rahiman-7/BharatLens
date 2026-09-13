from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.database import engine
from app.models import Base
from app.services.scheduler import start_news_scheduler, stop_news_scheduler
from app.api.routes import health, categories, states, news, archive, search, auth, bookmarks, reading_events, stories


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables on startup
    Base.metadata.create_all(bind=engine)
    # Start background news scheduler
    start_news_scheduler()
    yield
    # Clean shutdown of scheduler
    stop_news_scheduler()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for BharatLens — India-focused intelligent news aggregator with historical archive.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register v1 API Routers
app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(categories.router, prefix=settings.API_V1_PREFIX)
app.include_router(states.router, prefix=settings.API_V1_PREFIX)
app.include_router(news.router, prefix=settings.API_V1_PREFIX)
app.include_router(archive.router, prefix=settings.API_V1_PREFIX)
app.include_router(search.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(bookmarks.router, prefix=settings.API_V1_PREFIX)
app.include_router(reading_events.router, prefix=settings.API_V1_PREFIX)
app.include_router(stories.router, prefix=settings.API_V1_PREFIX)



@app.get("/", tags=["Root"])
def read_root():
    return {
        "service": "BharatLens API",
        "tagline": "News with a wider perspective — See India. See the World.",
        "docs": "/docs",
        "version": "1.0.0",
        "status": "online",
    }
