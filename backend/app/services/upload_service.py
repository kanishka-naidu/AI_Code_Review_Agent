"""
Upload Service.

Handles persisting uploaded source files and detecting their language.
Language detection is delegated to LanguageDetectionAgent — no duplicate logic.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from app.agents.language_detection_agent import LanguageDetectionAgent
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class UploadService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._settings.upload_path.mkdir(parents=True, exist_ok=True)
        self._language_agent = LanguageDetectionAgent()

    @property
    def settings(self):
        return self._settings

    def save_upload(self, filename: str, content: str, language: str | None) -> tuple[str, str]:
        """
        Persist *content* to the upload directory.

        Returns (source_id, detected_language).
        """
        source_id = str(uuid.uuid4())
        safe_name = Path(filename).name
        destination = self._settings.upload_path / f"{source_id}_{safe_name}"
        destination.write_text(content, encoding="utf-8")
        detected = language or self._language_agent.detect(safe_name, content)
        logger.info("UploadService: saved '%s' as source_id='%s', language='%s'", safe_name, source_id, detected)
        return source_id, detected
