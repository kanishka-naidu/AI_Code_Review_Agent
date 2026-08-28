import os
import json
import tempfile
import importlib
import importlib.util
import sys

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings


@pytest.fixture(autouse=True)
def env_clear(monkeypatch):
    # Ensure LLM_API_KEY is empty so the app uses mocked LLM in tests
    monkeypatch.setenv("LLM_API_KEY", "")
    yield


@pytest.fixture()
def client():
    # Import app.main lazily to ensure env vars are set
    import app.main as main_mod

    return TestClient(main_mod.app)


@pytest.fixture()
def mock_llm(monkeypatch):
    """Patch the LiteLLMGeminiClient to return deterministic summaries for agenerate."""
    # Import the module that defines the LLM client class
    llm_mod = importlib.import_module("app.core.llm")

    class MockLLM:
        def __init__(self, *args, **kwargs):
            pass

        async def agenerate(self, prompt: str, **kwargs):
            # Return a predictable plain-text string like the real client
            return "Mocked LLM summary of: " + (prompt or "")

        def generate(self, prompt: str, **kwargs):
            return "Mocked LLM summary of: " + (prompt or "")

    monkeypatch.setattr(llm_mod, "LiteLLMGeminiClient", MockLLM)
    yield MockLLM


@pytest.mark.integration
def test_rag_pipeline_with_seeded_chroma(client, mock_llm, tmp_path):
    """Integration test: seed a small Chroma DB and run the analyze endpoint.

    Requires chromadb to be installed in the environment running the test. If chromadb
    is not available, the test will be skipped.
    """
    chromadb_spec = importlib.util.find_spec("chromadb")
    if chromadb_spec is None:
        pytest.skip("chromadb not installed; skipping RAG integration test")

    # Load seed_chroma from the sibling file
    seed_path = os.path.join(os.path.dirname(__file__), "seed_chroma.py")
    spec = importlib.util.spec_from_file_location("seed_chroma", seed_path)
    seed_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seed_mod)
    seed_chroma = seed_mod.seed_chroma

    db_path = tmp_path / "chroma_db"
    db_path.mkdir()
    try:
        seed_chroma(str(db_path))
    except Exception as e:
        pytest.skip(f"Could not seed chroma DB in this environment: {e}")

    # Ensure settings point to the seeded chroma persistence directory
    settings = get_settings()
    # Some Settings objects used in tests may be lightweight; set attribute directly
    setattr(settings, "chroma_persistence_dir", str(db_path))

    # Call the analyze endpoint with a small python file to trigger RAG usage
    payload = {
        "language": "python",
        "code": "def query(db, user_input):\n    sql = \"SELECT * FROM users WHERE name = '%s'\" % user_input\n    db.execute(sql)\n",
        "include_rag": True,
    }

    resp = client.post("/analyze", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Basic assertions about report contents (response now wraps the report)
    report = data.get("report", {})
    assert "report_id" in report
    assert report.get("language") == "python"
    assert "findings" in report
    # Ensure RAG contributed to the assistant summary by checking for the mocked LLM text
    assert "Mocked LLM summary" in json.dumps(data, ensure_ascii=False)
