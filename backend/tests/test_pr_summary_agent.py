import asyncio

from app.agents.pr_summary_agent import PRSummaryAgent


class MockLLM:
    def __init__(self, response: str):
        self._response = response

    async def agenerate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 256):
        await asyncio.sleep(0)
        return self._response


def test_generate_pr_summary_uses_llm():
    report = {
        "filename": "a.py",
        "language": "python",
        "findings": [{"rule_id": "R1", "severity": "high"}],
        "quality_score": 80,
        "security_score": 70,
    }
    agent = PRSummaryAgent(llm=MockLLM("Generated summary content"))
    summary = asyncio.run(agent.generate_pr_summary(report))
    assert isinstance(summary, str)
    assert "Generated summary content" in summary


def test_generate_pr_summary_fallback_when_llm_none(monkeypatch):
    report = {"filename": "b.py", "language": "python", "findings": [], "quality_score": 90, "security_score": 95}
    # Ensure any cached/global LLM client is not used by forcing get_llm_client to raise
    import app.core.llm as llm_mod
    import app.agents.pr_summary_agent as pr_mod
    # Ensure both the core llm accessor and the imported alias in the agent module
    # raise so the agent will fall back to its internal summary generator.
    monkeypatch.setattr(llm_mod, "get_llm_client", lambda: (_ for _ in ()).throw(Exception("no llm")))
    monkeypatch.setattr(pr_mod, "get_llm_client", lambda: (_ for _ in ()).throw(Exception("no llm")))
    agent = PRSummaryAgent(llm=None)
    summary = asyncio.run(agent.generate_pr_summary(report))
    assert isinstance(summary, str)
    assert "Pull Request Analysis" in summary
