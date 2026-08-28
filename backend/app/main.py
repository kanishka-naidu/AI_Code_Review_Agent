from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, upload, analyze, assistant, reports, metrics
from app.api.rate_limiter import InMemoryRateLimiter
from app.api.rate_limiter_redis import TokenBucketRedisRateLimiter, RedisRateLimiter
from app.api.security import SecurityHeadersMiddleware
from app.core.config import get_settings


settings = get_settings()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version
)


# ==============================
# CORS Configuration
# Frontend: Next.js localhost:3000
# Backend: FastAPI localhost:8000
# ==============================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://ai-code-review-frontend-u2s6.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================
# Security Headers Middleware
# ==============================

if getattr(settings, "security_headers_enabled", True):
    app.add_middleware(SecurityHeadersMiddleware)


# ==============================
# Rate Limiter Middleware
# ==============================

if getattr(settings, "redis_rate_limiter_enabled", False):

    try:
        app.add_middleware(
            TokenBucketRedisRateLimiter,
            redis_url=settings.redis_url,
            capacity=settings.redis_rate_limit_per_minute,
            refill_per_minute=settings.redis_rate_limit_per_minute
        )

    except Exception:
        app.add_middleware(
            RedisRateLimiter,
            redis_url=settings.redis_url,
            rate_per_minute=settings.redis_rate_limit_per_minute
        )

elif getattr(settings, "rate_limit_enabled", False):

    app.add_middleware(
        InMemoryRateLimiter,
        rate_per_minute=settings.rate_limit_per_minute
    )


# ==============================
# Startup Readiness Checks
# ==============================

try:
    from app.core.startup import run_startup_checks

    @app.on_event("startup")
    async def _startup_checks():
        run_startup_checks()

except Exception as exc:

    import logging

    logging.getLogger(__name__).warning(
        "Startup checks could not be registered: %s",
        exc
    )


# ==============================
# API Routes
# ==============================

app.include_router(health.router)
app.include_router(upload.router)
app.include_router(analyze.router)
app.include_router(assistant.router)
app.include_router(reports.router)
app.include_router(metrics.router)