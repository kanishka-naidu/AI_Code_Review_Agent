import logging
from typing import Iterable

from app.core.config import get_settings


class SecretRedactingFilter(logging.Filter):
    """Logging filter that redacts known secret values from log messages.

    It collects secret values from settings (LLM API keys, redis URLs) and replaces
    any occurrences in log messages with a redacted placeholder. This prevents
    accidental leakage of secrets in logs while keeping messages readable.
    """

    def __init__(self, secrets: Iterable[str] | None = None):
        super().__init__()
        self._secrets = [s for s in (secrets or []) if s]

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if not msg:
            return True
        redacted = msg
        for s in self._secrets:
            if not s:
                continue
            try:
                if s in redacted:
                    # Replace secret with redacted placeholder
                    redacted = redacted.replace(s, "<REDACTED>")
            except Exception:
                # Defensive: don't break logging
                continue
        # Mutate the record message safely and clear args so formatting doesn't attempt
        # to interpolate unknown args (which may cause TypeError in formatters).
        record.msg = redacted
        record.args = ()
        return True


def get_logger(name: str) -> logging.Logger:
    settings = get_settings()
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        # Attach redaction filter to handler
        secrets = [
            getattr(settings, "llm_api_key", ""),
            getattr(settings, "redis_url", ""),
        ]
        handler.addFilter(SecretRedactingFilter(secrets))
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    return logger
