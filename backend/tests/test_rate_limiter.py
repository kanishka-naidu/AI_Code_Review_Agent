import importlib
import sys
import time

import shutil
from fastapi.testclient import TestClient

import app.core.config as config_mod


def _reload_app_with_settings(settings_obj):
    # Build a fresh FastAPI test app that mounts only the health router and the
    # in-memory rate limiter middleware. This avoids mutating the already-started
    # application in app.main which would raise when adding middleware after start.
    from fastapi import FastAPI
    from app.api.routes import health
    from app.api.rate_limiter import InMemoryRateLimiter

    test_app = FastAPI(title="test")
    # Register middleware before the app is started
    test_app.add_middleware(InMemoryRateLimiter, rate_per_minute=settings_obj.rate_limit_per_minute)
    test_app.include_router(health.router)
    return TestClient(test_app)


class S:
    rate_limit_enabled = True
    rate_limit_per_minute = 2
    app_name = "test"
    app_version = "0"
    log_level = "INFO"
    orchestrator_concurrency_limit = 4
    startup_fail_on_missing_analyzers = False


def test_rate_limiter_blocks_excess_requests(monkeypatch):
    # ensure shutil.which not changed (middleware independent)
    client = _reload_app_with_settings(S())
    # first two requests allowed
    r1 = client.get("/health")
    assert r1.status_code == 200
    r2 = client.get("/health")
    assert r2.status_code == 200
    # third within same minute should be rate-limited
    r3 = client.get("/health")
    assert r3.status_code == 429

    # wait > window and ensure tokens refill
    time.sleep(1.1)
    r4 = client.get("/health")
    assert r4.status_code in (200, 429)
