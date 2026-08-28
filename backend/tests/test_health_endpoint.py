from fastapi.testclient import TestClient

import shutil

from app.main import app
from app.core import startup_checks
from app.core import config as config_mod

client = TestClient(app)


def test_readiness_warn_only(monkeypatch):
    # Simulate missing analyzers
    monkeypatch.setattr(shutil, "which", lambda name: None)
    # Ensure settings default is warn-only
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("degraded", "ready")
    assert isinstance(data["missing_analyzers"], list)


def test_readiness_fail_on_missing(monkeypatch):
    # Simulate missing analyzers
    monkeypatch.setattr(shutil, "which", lambda name: None)

    # Create a fake settings object with startup_fail_on_missing_analyzers True
    class _S:
        startup_fail_on_missing_analyzers = True

    monkeypatch.setattr(config_mod, "get_settings", lambda: _S())
    # health module imported get_settings at import-time — patch it there as well
    import app.api.routes.health as health_mod
    monkeypatch.setattr(health_mod, "get_settings", lambda: _S())

    resp = client.get("/health/ready")
    assert resp.status_code == 503
    data = resp.json()
    assert data["status"] == "degraded"
    assert isinstance(data["missing_analyzers"], list)
