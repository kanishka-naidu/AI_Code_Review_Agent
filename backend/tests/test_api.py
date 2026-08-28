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
