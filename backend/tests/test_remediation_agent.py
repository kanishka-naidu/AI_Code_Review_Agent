import asyncio

from app.agents.remediation_agent import RemediationAgent
from app.models.finding import Finding
from app.models.severity import Severity


class MockLLM:
    def __init__(self, response: str):
        self._response = response

    async def agenerate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 256):
        # Simulate some async delay
        await asyncio.sleep(0)
        return self._response


def test_suggest_generates_remediation_from_llm():
    finding = Finding(
        rule_id="TEST-1",
        title="Test",
        description="desc",
        severity=Severity.MEDIUM,
        category="security",
    )
    # LLM returns a JSON array with remediation fields
    llm_output = '[{"index": 1, "root_cause": "missing validation", "corrected_code": "safe_execute()", "secure_alternative": "use prepared statements"}]'
    agent = RemediationAgent(llm=MockLLM(llm_output))

    remediations = asyncio.run(agent.suggest([finding]))
    assert isinstance(remediations, list)
    assert len(remediations) == 1
    # The remediation should be human-readable, not raw field:value pairs
    assert "missing validation" in remediations[0]
    assert "root_cause" not in remediations[0]
    assert "corrected_code" not in remediations[0]


def test_generate_report_recommendations_parses_numbered_list():
    findings = [
        Finding(rule_id="R1", title="a", description="d", severity=Severity.LOW, category="quality"),
        Finding(rule_id="R2", title="b", description="d2", severity=Severity.HIGH, category="security"),
    ]
    # Simulate LLm returning a numbered list
    llm_output = "1. Fix high severity issues\n2. Improve tests"
    agent = RemediationAgent(llm=MockLLM(llm_output))

    recs = asyncio.run(agent.generate_report_recommendations(findings))
    assert isinstance(recs, list)
    assert len(recs) >= 1
    assert any("Fix high severity" in item for item in recs)
