"""Verify the assistant context includes source_code and detail level."""
import asyncio
import json
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app.agents.assistant_agent import AssistantAgent
from app.models.request_models import AssistantRequest
from app.services.assistant_service import AssistantService


def test_prepare_context_source_code():
    """Verify prepare_context extracts source_code from assistant_context."""
    agent = AssistantAgent()
    report = json.load(open(os.path.join(BASE_DIR, "app/reports/02b19803-e898-4183-bccf-6abe23c1151f.json"), encoding="utf-8"))
    ctx = agent.prepare_context(report)
    assert ctx["source_code"] is not None, "source_code should be extracted from assistant_context"
    assert "import os" in ctx["source_code"], "source_code should contain the actual code"
    print("PASS: prepare_context extracts source_code from assistant_context")
    print(f"  source_code length: {len(ctx['source_code'])} chars")


def test_assistant_request_detail_level():
    """Verify AssistantRequest accepts assistant_detail_level."""
    req = AssistantRequest(message="Fix this code", assistant_detail_level="detailed")
    assert req.assistant_detail_level == "detailed"
    print("PASS: AssistantRequest accepts assistant_detail_level")


def test_build_context_detail_level():
    """Verify _build_context passes detail level to context."""
    svc = AssistantService()
    req = AssistantRequest(message="Fix this code", assistant_detail_level="concise")
    ctx = svc._build_context(req)
    assert ctx.get("assistant_detail_level") == "concise"
    print("PASS: _build_context includes assistant_detail_level")


if __name__ == "__main__":
    test_prepare_context_source_code()
    test_assistant_request_detail_level()
    test_build_context_detail_level()
    print("\nALL ASSISTANT CONTEXT CHECKS PASSED")