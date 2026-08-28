from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.startup_checks import check_analyzer_binaries
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_root() -> dict[str, str]:
    """Legacy health root endpoint kept for compatibility."""
    return {"status": "ok"}


@router.get("/ready")
async def readiness() -> JSONResponse:
    """Readiness endpoint.

    - Runs analyzer binary checks and returns HTTP 200 if service is ready.
    - If settings.startup_fail_on_missing_analyzers is True, missing analyzers make the
      endpoint return HTTP 503 (service not ready). By default it's warn-only.
    """
    settings = get_settings()
    results = check_analyzer_binaries()
    missing = [tool for tool, present in results.items() if not present]

    payload = {
        "status": "ready" if not missing else "degraded",
        "missing_analyzers": missing,
        "details": results,
    }

    if missing and getattr(settings, "startup_fail_on_missing_analyzers", False):
        logger.error("Readiness check failed - missing analyzers: %s", missing)
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=payload)

    # Warn-only by default
    if missing:
        logger.warning("Readiness check: missing analyzers (warn-only): %s", missing)

    return JSONResponse(status_code=status.HTTP_200_OK, content=payload)


@router.get("/live")
async def liveness() -> JSONResponse:
    """Liveness endpoint - basic uptime probe."""
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "alive"})
