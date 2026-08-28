import sys
import asyncio

from types import ModuleType

import os
from app.core.llm import LiteLLMGeminiClient
from app.core.config import get_settings



class _FakeLiteLLM(ModuleType):
    def __init__(self):
        super().__init__("litellm")
        self._calls = 0

    def completion(self, model, api_key, messages, temperature, max_tokens):
        self._calls += 1
        # Fail the first two times with a transient-like error, then succeed
        if self._calls <= 2:
            raise Exception("429 Too Many Requests")
        return {"choices": [{"message": {"content": "{\"result\": \"ok\"}"}}]}


def test_generate_retries_and_returns():
    fake = _FakeLiteLLM()
    sys.modules["litellm"] = fake

    model = os.environ.get("LLM_MODEL") or get_settings().llm_model or "test-model"
    client = LiteLLMGeminiClient(model=model, api_key="fake-key")
    # Should retry twice internally and then return the final string
    result = client.generate("hello", temperature=0.1, max_tokens=10)
    assert "ok" in result


def test_agenerate_async():
    fake = _FakeLiteLLM()
    sys.modules["litellm"] = fake

    model = os.environ.get("LLM_MODEL") or get_settings().llm_model or "test-model"
    client = LiteLLMGeminiClient(model=model, api_key="fake-key")

    async def run():
        r = await client.agenerate("hi", temperature=0.1, max_tokens=10)
        assert "ok" in r

    asyncio.run(run())
