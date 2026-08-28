import os
import asyncio
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_analysis_service, get_upload_service
from app.core.config import get_settings
from app.models.submission import CodeSubmission

from app.main import app


class GoodAnalyzer:
    name = "good"

    def analyze(self, source: str, filename: str):
        from app.models.finding import Finding
        from app.models.severity import Severity
        f = Finding(rule_id="GOOD1", title="good", description="desc", severity=Severity.LOW, category="quality", location="1", evidence="e")
        return [f], {}


class FailingAnalyzer:
    name = "fail"

    def analyze(self, source: str, filename: str):
        raise RuntimeError("simulated analyzer crash")


@pytest.fixture(autouse=True)
def reset_settings():
    # Ensure default between tests
    s = get_settings()
    s.analyzer_failure_mode = "partial"
    yield


def _reconfigure_orchestrator_with(analyzers_map):
    svc = get_analysis_service()
    orch = svc._orchestrator
    # Backup current analyzers so tests restore them afterwards
    old = getattr(orch, "_analyzers", None)
    orch._analyzers = analyzers_map
    orch._graph = orch._build_graph()
    return orch, old


def _restore_orchestrator(orch, old_analyzers):
    if old_analyzers is not None:
        orch._analyzers = old_analyzers
        orch._graph = orch._build_graph()


def test_partial_mode_allows_partial_results():
    s = get_settings()
    prev_mode = s.analyzer_failure_mode
    s.analyzer_failure_mode = "partial"
    analyzers = {"python": {"quality": GoodAnalyzer(), "security": FailingAnalyzer()}}
    orch, old = _reconfigure_orchestrator_with(analyzers)

    client = TestClient(app)
    payload = {"language": "python", "code": "print('hi')", "include_rag": False}
    resp = client.post("/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()["report"]
    # findings should include the good analyzer's finding
    assert any(f["rule_id"] == "GOOD1" for f in data["findings"]) or len(data["findings"]) >= 1
    # metadata should include analyzer_status and errors
    assert "errors" in data["metadata"]
    assert data["metadata"]["errors"]

    # restore
    _restore_orchestrator(orch, old)
    s.analyzer_failure_mode = prev_mode


def test_strict_mode_fails_request():
    s = get_settings()
    prev_mode = s.analyzer_failure_mode
    s.analyzer_failure_mode = "strict"
    analyzers = {"python": {"quality": GoodAnalyzer(), "security": FailingAnalyzer()}}
    orch, old = _reconfigure_orchestrator_with(analyzers)

    client = TestClient(app)
    payload = {"language": "python", "code": "print('hi')", "include_rag": False}
    resp = client.post("/analyze", json=payload)
    assert resp.status_code == 500
    assert "tool" in resp.json()["detail"]
    assert resp.json()["detail"]["tool"] == "analyzers"

    # restore
    _restore_orchestrator(orch, old)
    s.analyzer_failure_mode = prev_mode
