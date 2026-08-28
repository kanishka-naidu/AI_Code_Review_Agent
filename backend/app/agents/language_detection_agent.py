"""Language detection agent."""
from __future__ import annotations

from pathlib import Path

from app.core.logging import get_logger
from app.core.repository_config import get_repository_config

logger = get_logger(__name__)


class LanguageDetectionAgent:
    """Detect the programming language of a source file."""

    def __init__(self) -> None:
        self._config = get_repository_config().load("analysis.json")

    def detect(self, filename: str, content: str) -> str:
        """Return the configured language string for a filename/content pair."""
        suffix = Path(filename).suffix.lower()
        extensions = self._config.get("language_extensions", {})
        if suffix in extensions:
            detected = str(extensions[suffix])
            logger.debug("Language '%s' detected from extension '%s'", detected, suffix)
            return detected

        for item in self._config.get("language_content_hints", []):
            hint = item.get("hint", "")
            language = item.get("language", "")
            if hint and hint in content:
                logger.debug("Language '%s' detected from configured content hint", language)
                return str(language)

        fallback = str(self._config.get("fallback_language", "text"))
        logger.debug("Language detection defaulted to '%s' for '%s'", fallback, filename)
        return fallback
