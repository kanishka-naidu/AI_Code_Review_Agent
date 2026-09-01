from functools import lru_cache
import os
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings sourced from environment variables and .env."""

    app_name: str = Field(default="Development of Smart Code Inspection Platform with Vulnerability Detection System")
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)  # Default to False for production safety
    upload_dir: str = Field(default="uploads")
    reports_dir: str = Field(default="reports")
    knowledge_base_dir: str = Field(default="knowledge_base")
    vector_db_dir: str = Field(default="vector_db")
    # Backwards-compatible setting for Chromadb persistence directory. Tests and
    # older configurations may reference CHROMA_PERSISTENCE_DIR; map it here so
    # code can continue to set it without causing attribute errors. Prefer
    # settings.vector_db_dir in new code.
    chroma_persistence_dir: str = Field(default="vector_db")
    prompt_directory: str = Field(default="prompts")
    configuration_dir: str = Field(default="configuration")
    rag_collection: str = Field(default="owasp_knowledge_base")
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    allowed_extensions: str = Field(default=".py,.java,.txt,.md")
    supported_languages: str = Field(default="python,java")
    max_upload_size_mb: int = Field(default=10)
    llm_provider: str = Field(default="gemini")
    llm_model: str = Field(default="")
    llm_api_key: str = Field(default="")
    # LLM retry and concurrency tuning
    llm_max_retries: int = Field(default=2)
    llm_backoff_min_seconds: float = Field(default=0.5)
    llm_backoff_max_seconds: float = Field(default=10.0)
    llm_timeout_seconds: float = Field(default=30.0)
    llm_concurrency_limit: int = Field(default=2)
    # Default LLM generation tuning (override in .env)
    llm_default_temperature: float = Field(default=0.2)
    llm_default_max_tokens: int = Field(default=1200)
    chunk_size: int = Field(default=800)
    chunk_overlap: int = Field(default=50)
    retrieval_count: int = Field(default=4)
    analyzer_timeout: int = Field(default=60)
    semgrep_timeout: int = Field(default=60)
    # Analyzer tool option strings may be provided via environment; if unset the
    # repository configuration (configuration/analyzers.json -> tool_options) is used.
    bandit_options: str = Field(default="")
    ruff_options: str = Field(default="")
    semgrep_options: str = Field(default="")
    radon_cc_options: str = Field(default="")
    radon_mi_options: str = Field(default="")
    pmd_options: str = Field(default="")
    log_level: str = Field(default="INFO")
    quality_penalty_per_finding: int = Field(default=7)
    security_penalty_per_finding: int = Field(default=10)
    max_quality_severity_penalty: int = Field(default=30)
    max_security_severity_penalty: int = Field(default=40)
    quality_severity_divisor: int = Field(default=3)
    security_severity_divisor: int = Field(default=2)
    severity_weight_critical: int = Field(default=20)
    severity_weight_high: int = Field(default=15)
    severity_weight_medium: int = Field(default=10)
    severity_weight_low: int = Field(default=5)
    severity_weight_info: int = Field(default=2)
    min_code_length: int = Field(default=10)
    max_code_length: int = Field(default=500_000)
    default_upload_filename: str = Field(default="uploaded_source")
    default_paste_filename: str = Field(default="pasted_code")
    default_submitted_filename: str = Field(default="submitted_code")
    unknown_tool_label: str = Field(default="unknown")
    unsupported_provider_help: str = Field(default="Set LLM_PROVIDER=gemini or add a configured provider.")
    # Readiness policy: whether missing analyzers should mark service as Unready
    startup_fail_on_missing_analyzers: bool = Field(default=False)
    # Orchestrator concurrency limit (max simultaneous pipeline runs)
    orchestrator_concurrency_limit: int = Field(default=2)
    # AI Assistant RAG settings. When False, the assistant does NOT load the
    # SentenceTransformer embedding model or ChromaDB, avoiding OOM on Render.
    # The assistant still uses analysis_context directly in the prompt.
    assistant_rag_enabled: bool = Field(default=False)
    # Analyzer failure policy: 'partial' (continue and return partial results) or 'strict' (fail the request)
    # Configure via .env ANALYZER_FAILURE_MODE=partial|strict
    analyzer_failure_mode: str = Field(default="partial")
    # Simple in-memory rate limiter config
    rate_limit_enabled: bool = Field(default=False)
    rate_limit_per_minute: int = Field(default=60)
    # Redis-backed distributed rate limiter (recommended for production)
    redis_rate_limiter_enabled: bool = Field(default=False)
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_rate_limit_per_minute: int = Field(default=600)
    # Conversation persistence in Redis (optional)
    redis_conversations_enabled: bool = Field(default=False)
    redis_conversation_key_prefix: str = Field(default="conv:")

    # Security headers middleware
    security_headers_enabled: bool = Field(default=True)
    csp_policy: str = Field(default="default-src 'self'; script-src 'self' 'unsafe-inline';")
    # Additional CSP sources (comma-separated) that can be merged into directives
    csp_additional_script_src: str = Field(default="")
    csp_additional_style_src: str = Field(default="")
    csp_additional_img_src: str = Field(default="")
    # When True and debug is True, allow https: for docs routes to enable external Swagger UI loading
    csp_allow_https_for_docs: bool = Field(default=True)
    hsts_seconds: int = Field(default=31536000)

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("llm_model")
    @classmethod
    def validate_llm_model(cls, value: str) -> str:
        """Reject Gemini Pro model names while allowing env-driven Flash values."""
        model = value.strip()
        if model and "pro" in model.lower():
            raise ValueError("LLM_MODEL must not reference a Gemini Pro model.")
        return model

    @field_validator("analyzer_failure_mode")
    @classmethod
    def validate_analyzer_failure_mode(cls, value: str) -> str:
        val = (value or "").strip().lower()
        if val not in ("partial", "strict"):
            raise ValueError("analyzer_failure_mode must be one of 'partial' or 'strict'")
        return val

    @property
    def allowed_extensions_list(self) -> list[str]:
        return self.csv_list(self.allowed_extensions)

    @property
    def supported_languages_list(self) -> list[str]:
        return self.csv_list(self.supported_languages)

    @staticmethod
    def csv_list(value: str) -> list[str]:
        """Parse a comma-separated setting into a trimmed list."""
        return [item.strip() for item in value.split(",") if item.strip()]

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parents[1]

    @property
    def upload_path(self) -> Path:
        return self.base_dir / self.upload_dir

    @property
    def reports_path(self) -> Path:
        # Use REPORTS_DIR env var if set (for Render persistent disk)
        env_reports_dir = os.environ.get("REPORTS_DIR")
        if env_reports_dir:
            return Path(env_reports_dir)
        return self.base_dir / self.reports_dir

    @property
    def knowledge_base_path(self) -> Path:
        return self.base_dir / self.knowledge_base_dir

    @property
    def vector_db_path(self) -> Path:
        return self.base_dir / self.vector_db_dir

    @property
    def chroma_persistence_path(self) -> Path:
        """Backwards-compatible path to the chroma persistence directory.

        New code should prefer vector_db_path; this property exists so tests and
        legacy configs that set CHROMA_PERSISTENCE_DIR continue to work.
        """
        return self.base_dir / self.chroma_persistence_dir

    @property
    def prompt_path(self) -> Path:
        return self.base_dir / self.prompt_directory

    @property
    def configuration_path(self) -> Path:
        return self.base_dir / self.configuration_dir

    def severity_weights(self) -> dict[str, int]:
        return {
            "critical": self.severity_weight_critical,
            "high": self.severity_weight_high,
            "medium": self.severity_weight_medium,
            "low": self.severity_weight_low,
            "info": self.severity_weight_info,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return validated Settings instance.

    Additional validation enforces provider-specific rules such as only allowing
    Gemini 2.5 Flash style models when the provider is set to 'gemini'.
    """
    settings = Settings()

    # Provider-specific validations
    provider = settings.llm_provider.strip().lower()
    model = settings.llm_model.strip()
    if provider == "gemini":
        # Only enforce strict Gemini model requirements when an API key exists.
        # This allows local test runs without setting LLM credentials.
        if settings.llm_api_key and settings.llm_api_key.strip():
            if not model:
                raise ValueError("LLM_MODEL must be set when using Gemini with an API key and must reference a Gemini Flash model.")
            low = model.lower()
            if "pro" in low:
                raise ValueError("Gemini Pro models are not allowed.")
            if "flash" not in low:
                raise ValueError(
                    "LLM_MODEL must reference a Gemini Flash model."
                )

    return settings
