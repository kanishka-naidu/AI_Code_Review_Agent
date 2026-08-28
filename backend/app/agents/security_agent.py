"""
Security Agent (facade).

Thin wrapper that dispatches to the language-specific security analyzer.
This agent is not in the LangGraph pipeline (the orchestrator calls analyzers
directly); it exists as a convenience facade for direct callers.
"""
from __future__ import annotations

from app.analyzers.python.security import PythonSecurityAnalyzer
from app.analyzers.java.security import JavaSecurityAnalyzer
from app.analyzers.common.tooling import AnalyzerError
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.finding import Finding

logger = get_logger(__name__)

_SECURITY_ANALYZERS = {
    "python": PythonSecurityAnalyzer(),
    "java": JavaSecurityAnalyzer(),
}


class SecurityAgent:
    """Facade for invoking security analysis on a code snippet."""

    def analyze(self, language: str, source: str, filename: str | None = None) -> dict[str, object]:
        """
        Run the security analyzer for *language* and return a result dict.

        Returns:
            {
              "language": str,
              "findings": list[Finding],
              "error": str | None
            }
        """
        analyzer = _SECURITY_ANALYZERS.get(language)
        if analyzer is None:
            logger.warning("SecurityAgent: no security analyzer for language '%s'", language)
            return {"language": language, "findings": [], "error": f"No security analyzer for '{language}'"}

        try:
            configured_filename = filename or get_settings().default_submitted_filename
            findings, _ = analyzer.analyze(source, configured_filename)
            logger.info("SecurityAgent: %d security findings for '%s'", len(findings), configured_filename)
            return {"language": language, "findings": findings, "error": None}
        except AnalyzerError as exc:
            logger.error("SecurityAgent error: %s", exc.message)
            return {"language": language, "findings": [], "error": exc.message}
