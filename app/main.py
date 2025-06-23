import os
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_limiter import FastAPILimiter
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api import bias  # New bias analysis endpoints
from app.api import graph, narratives, refresh
from app.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    redis_client = redis.from_url(
        os.getenv("REDIS_URL", "redis://redis:6379/0"),
        encoding="utf8",
        decode_responses=True,
    )
    FastAPICache.init(RedisBackend(redis_client), prefix="iimisinfo")
    await FastAPILimiter.init(redis_client)
    yield
    # Shutdown
    await redis_client.aclose()


limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(narratives.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(refresh.router, prefix="/api")
app.include_router(auth_router, prefix="/auth/jwt", tags=["auth"])
app.include_router(bias.router, prefix="/api/bias", tags=["bias"])  # New bias endpoints

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app)


@app.get("/health")
async def health():
    """Simple health-check endpoint."""
    return {"status": "ok"}
