import os
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings


def _make_client():
    import app.main as main_mod
    return TestClient(main_mod.app)


PAYLOAD = {
    "language": "python",
    "code": "password = \"admin123\"\n\nimport os\n\ndef execute(user_input):\n    eval(user_input)\n    os.system(user_input)",
    "include_rag": True,
}


@pytest.mark.integration
def test_reproduction_partial_mode(monkeypatch):
    monkeypatch.setenv("ANALYZER_FAILURE_MODE", "partial")
    client = _make_client()
    resp = client.post("/analyze", json=PAYLOAD)
    assert resp.status_code == 200, resp.text
    data = resp.json().get("report", {})
    findings = data.get("findings", [])
    rule_ids = {f.get("rule_id") for f in findings}
    # Expect Bandit B105 (hardcoded password) and B307 (eval) and os.system detection
    assert any("B105" in (r or "") for r in rule_ids), f"Missing B105 in {rule_ids}"
    assert any("B307" in (r or "") for r in rule_ids), f"Missing B307 in {rule_ids}"
    assert any("os.system" in (f.get('evidence') or "") or "command injection" in (f.get('explanation') or "") for f in findings), "Missing os.system/command injection finding"


@pytest.mark.integration
def test_reproduction_strict_mode(monkeypatch):
    monkeypatch.setenv("ANALYZER_FAILURE_MODE", "strict")
    client = _make_client()
    resp = client.post("/analyze", json=PAYLOAD)
    # Strict mode should still succeed for this input (no analyzer failure) and return findings
    assert resp.status_code == 200, resp.text
    data = resp.json().get("report", {})
    findings = data.get("findings", [])
    assert findings, "Expected findings in strict mode"