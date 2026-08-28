import asyncio

import pytest

import app.core.config as config_mod
from app.services.assistant_service import AssistantService
from app.models.request_models import AssistantRequest


@pytest.fixture(autouse=True)
def patch_settings(monkeypatch):
    class S:
        app_name = "test"
        app_version = "0"
        log_level = "INFO"
        llm_api_key = ""
        llm_model = ""
        llm_default_temperature = 0.2
        llm_default_max_tokens = 1200

    monkeypatch.setattr(config_mod, "get_settings", lambda: S())
    yield


def test_assistant_service_with_mocked_agent(monkeypatch):
    # Create a mock assistant agent with an async answer method
    class MockAssistant:
        async def answer(self, question, analysis_context=None, conversation_history=None):
            return ("Mocked assistant reply to: " + question, ["kb1"])

        def new_conversation_id(self):
            return "conv-123"

    svc = AssistantService(assistant_agent=MockAssistant())

    req = AssistantRequest(question="Explain this vulnerability")

    answer = asyncio.run(svc.answer(req))
    assert "Mocked assistant reply" in answer.answer
    assert isinstance(answer.conversation_id, str)
    assert answer.sources == ["kb1"]
