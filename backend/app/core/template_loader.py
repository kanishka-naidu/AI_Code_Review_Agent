from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class PromptTemplateLoader:
    """Loads prompt templates from the configured prompt directory."""

    def __init__(self) -> None:
        self._settings = get_settings()

    def load(self, template_name: str) -> str:
        """Return a prompt template by filename."""
        template_path = self._settings.prompt_path / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Prompt template '{template_name}' not found at '{template_path}'.")
        logger.debug("Loading prompt template '%s'", template_path)
        return template_path.read_text(encoding="utf-8")

    def render(self, template_name: str, **values: object) -> str:
        """Render a named template with explicit values."""
        return self.load(template_name).format(**values)


@lru_cache(maxsize=1)
def get_prompt_loader() -> PromptTemplateLoader:
    return PromptTemplateLoader()
