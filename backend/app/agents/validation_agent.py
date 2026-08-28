"""Validation Agent validates a submission before analysis begins."""
from __future__ import annotations

from app.core.config import get_settings
from app.core.constants import SUPPORTED_LANGUAGES
from app.core.logging import get_logger

logger = get_logger(__name__)


class ValidationAgent:
    """Validate a code submission before passing it to the analyzers."""

    def __init__(self) -> None:
        self._settings = get_settings()

    def validate(self, language: str, source: str) -> dict[str, object]:
        """Return validation metadata for the submitted source."""
        warnings: list[str] = []
        valid = True

        if language not in SUPPORTED_LANGUAGES:
            logger.warning("Unsupported language '%s'; analysis may be limited", language)
            warnings.append(
                f"Language '{language}' is not in the supported set {list(SUPPORTED_LANGUAGES)}."
            )

        source_length = len(source)
        if source_length < self._settings.min_code_length:
            valid = False
            warnings.append(
                f"Code is too short ({source_length} chars). Minimum is {self._settings.min_code_length}."
            )

        if source_length > self._settings.max_code_length:
            valid = False
            warnings.append(
                f"Code exceeds the maximum allowed size ({source_length} chars). "
                f"Maximum is {self._settings.max_code_length}."
            )

        result: dict[str, object] = {
            "language": language,
            "valid": valid,
            "warnings": warnings,
            "source_length": source_length,
        }
        logger.info(
            "ValidationAgent: language='%s', valid=%s, source_length=%d, warnings=%d",
            language,
            valid,
            source_length,
            len(warnings),
        )
        return result
