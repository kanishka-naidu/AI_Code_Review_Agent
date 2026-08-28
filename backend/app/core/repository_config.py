from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RepositoryConfig:
    """Loads repository-owned JSON configuration files."""

    def __init__(self) -> None:
        self._settings = get_settings()

    @lru_cache(maxsize=16)
    def load(self, filename: str) -> dict[str, Any]:
        """Read and parse a JSON config file from the configured directory."""
        path = self._settings.configuration_path / filename
        if not path.exists():
            raise FileNotFoundError(f"Configuration file '{filename}' not found at '{path}'.")
        logger.debug("Loading repository configuration '%s'", path)
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise ValueError(f"Configuration file '{filename}' must contain a JSON object.")
        return payload


@lru_cache(maxsize=1)
def get_repository_config() -> RepositoryConfig:
    return RepositoryConfig()
