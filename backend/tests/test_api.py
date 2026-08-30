from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_and_analyze():
    upload_response = client.post(
        "/upload?filename=test.py",
        data={"content": "def hello():\n    return 'world'\n"},
    )
    assert upload_response.status_code == 200
    source_id = upload_response.json()["source_id"]

    analyze_response = client.post(
        "/analyze",
        json={"source_id": source_id},
    )
    assert analyze_response.status_code == 200
    assert analyze_response.json()["report"]["language"] == "python"


def test_paste_and_analyze():
    analyze_response = client.post(
        "/analyze",
        json={"language": "python", "code": "print('hello')", "include_rag": True},
    )
    assert analyze_response.status_code == 200
    assert analyze_response.json()["report"]["language"] == "python"


def test_hardcoded_secret_detection():
    analyze_response = client.post(
        "/analyze",
        json={
            "language": "python",
            "code": 'API_KEY = "my-secret-key-123"',
            "include_rag": True,
        },
    )
    assert analyze_response.status_code == 200, analyze_response.text
    data = analyze_response.json()
    findings = data.get("report", {}).get("findings", [])
    rule_ids = {f.get("rule_id") for f in findings}
    assert any("hardcoded_secret" in (r or "") for r in rule_ids), f"Missing hardcoded_secret in {rule_ids}"
    matching = [f for f in findings if "hardcoded_secret" in f.get("rule_id", "")]
    assert matching, "Expected at least one hardcoded secret finding"
    assert matching[0].get("severity") == "high"
    assert "API_KEY" in (matching[0].get("evidence") or "")
