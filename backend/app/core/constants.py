"""Project-wide constants sourced from settings and repository configuration."""

from app.core.config import get_settings
from app.core.repository_config import get_repository_config

_settings = get_settings()
_analysis_config = get_repository_config().load("analysis.json")
_severity_config = get_repository_config().load("severity.json")

SUPPORTED_LANGUAGES = {language: language for language in _settings.supported_languages_list}
SUPPORTED_EXTENSIONS = dict(_analysis_config.get("language_extensions", {}))
QUALITY_THRESHOLD = _settings.quality_penalty_per_finding
SECURITY_THRESHOLD = _settings.security_penalty_per_finding
SEVERITY_ORDER = list(_severity_config.get("order_asc", []))
