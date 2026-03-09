import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.rate_limit import limiter
from app.routers import admin, stripe, subscribers, tides
from app.services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if settings.ENVIRONMENT == "production":
        start_scheduler()
    yield
    # Shutdown
    stop_scheduler()


is_production = settings.ENVIRONMENT == "production"

app = FastAPI(
    title="King Tide Alerts",
    description="Alerts for king tides in the SF Bay Area",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

app.state.limiter = limiter


def _rate_limit_exceeded_handler(request: Request, exc: Exception) -> Response:
    return Response(
        content='{"detail":"Rate limit exceeded"}',
        status_code=429,
        media_type="application/json",
    )


app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.APP_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Content-Type", "x-admin-password", "x-api-key", "stripe-signature"],
)

app.include_router(admin.router)
app.include_router(subscribers.router)
app.include_router(tides.router)
app.include_router(stripe.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
