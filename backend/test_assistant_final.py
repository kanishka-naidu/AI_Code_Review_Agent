import sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

heavy_modules = ["torch", "transformers", "sentence_transformers", "chromadb"]

# Test 1: Assistant with EMPTY analysis_context
print("=== Test 1: POST /assistant with EMPTY analysis_context ===")
loaded_before = {m: m in sys.modules for m in heavy_modules}
print(f"Heavy modules before: {[m for m, loaded in loaded_before.items() if loaded]}")

resp = client.post(
    "/assistant",
    json={
        "message": "What is a hardcoded API key?",
        "report_context": None,
        "conversation_id": None,
        "assistant_detail_level": "concise",
    },
)
print(f"status={resp.status_code}")
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:300]}"

data = resp.json()
print(f"has_answer={bool(data.get('answer'))}")
print(f"conversation_id={data.get('conversation_id')}")
print(f"answer_preview={str(data.get('answer', ''))[:200]}")

loaded_after = {m: m in sys.modules for m in heavy_modules}
new_heavy = [m for m in heavy_modules if loaded_after.get(m) and not loaded_before.get(m)]
print(f"New heavy modules loaded during empty-context request: {new_heavy}")
assert new_heavy == [], f"Heavy modules were loaded: {new_heavy}"

# Test 2: Assistant with NON-EMPTY analysis_context
print("\n=== Test 2: POST /assistant with NON-EMPTY analysis_context ===")
resp2 = client.post(
    "/assistant",
    json={
        "message": "Explain the findings",
        "report_context": {
            "findings": [{"title": "Hardcoded API Key", "severity": "high"}],
            "language": "python",
        },
        "conversation_id": None,
        "assistant_detail_level": "concise",
    },
)
print(f"status={resp2.status_code}")
assert resp2.status_code == 200, f"Expected 200, got {resp2.status_code}: {resp2.text[:300]}"

data2 = resp2.json()
print(f"has_answer={bool(data2.get('answer'))}")
print(f"conversation_id={data2.get('conversation_id')}")
print(f"answer_preview={str(data2.get('answer', ''))[:200]}")

print("\n=== ALL ASSISTANT TESTS PASSED ===")
