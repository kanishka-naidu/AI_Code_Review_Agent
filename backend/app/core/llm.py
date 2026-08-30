"""
Modular LLM client.

The provider, model, and API key are resolved from Settings. The implementation
uses LiteLLM so the rest of the application is isolated from provider SDKs.
"""
from __future__ import annotations

import time
import asyncio
from abc import ABC, abstractmethod
from functools import lru_cache

from tenacity import retry, retry_if_exception, wait_exponential_jitter, stop_after_attempt, RetryError

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core import metrics

logger = get_logger(__name__)


class BaseLLMClient(ABC):
    """Minimal interface every LLM provider must satisfy."""

    @abstractmethod
    def generate(self, prompt: str, *, temperature: float = 0.2, max_tokens: int = 2048) -> str:
        """Return a plain-text completion for *prompt* (synchronous)."""

    async def agenerate(self, prompt: str, *, temperature: float = 0.2, max_tokens: int = 2048) -> str:
        """Asynchronous completion. By default runs the sync generate in a threadpool."""
        return await asyncio.to_thread(self.generate, prompt, temperature=temperature, max_tokens=max_tokens)


class LLMConfigurationError(RuntimeError):
    """Raised when required LLM settings are missing or invalid."""


class _RetryableLLMError(Exception):
    """Indicates an LLM error that may be retried (rate limits, transient quota)."""


class LiteLLMGeminiClient(BaseLLMClient):
    """Gemini client implemented through LiteLLM.

    - Uses lazy import to avoid optional dependency failures during test collection.
    - Adds jittered exponential backoff retries for transient errors.
    - Provides async agenerate by delegating to generate in a thread.
    """

    def __init__(self, model: str, api_key: str) -> None:
        if not api_key:
            raise LLMConfigurationError("LLM_API_KEY is not set.")
        if not model:
            raise LLMConfigurationError("LLM_MODEL is not set.")
        settings = get_settings()
        self._model_name = model if "/" in model else f"{settings.llm_provider}/{model}"
        self._api_key = api_key
        self._max_retries = max(1, int(settings.llm_max_retries))
        self._backoff_min = max(0.1, float(settings.llm_backoff_min_seconds))
        self._backoff_max = max(1.0, float(settings.llm_backoff_max_seconds))
        self._timeout_seconds = max(10, float(getattr(settings, "llm_timeout_seconds", 30)))
        self._concurrency_limit = max(1, int(settings.llm_concurrency_limit))
        import threading
        self._sync_semaphore = threading.BoundedSemaphore(self._concurrency_limit)
        self._async_semaphore = asyncio.Semaphore(self._concurrency_limit)
        logger.info("LiteLLMGeminiClient initialised with configured model '%s' (concurrency=%d retries=%d timeout=%ds)", settings.llm_model, self._concurrency_limit, self._max_retries, int(self._timeout_seconds))

    def _is_retryable(self, err_str: str) -> bool:
        low = err_str.lower()
        if "429" in err_str or "resource_exhausted" in low or "rate" in low:
            return True
        return False

    def _call_provider(self, prompt: str, temperature: float, max_tokens: int) -> str:
        # Lazy import litellm to avoid import-time failures when the package isn't installed
        try:
            import litellm  # type: ignore
        except Exception as exc:  # pragma: no cover - environment-specific
            logger.error("litellm is not available: %s", exc)
            raise

        try:
            response = litellm.completion(
                model=self._model_name,
                api_key=self._api_key,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self._timeout_seconds,
            )
        except Exception as e:
            logger.error("LLM provider call failed: %s", e)
            raise
        content = response.get("choices", [{}])[0].get("message", {}).get("content")
        return str(content or "")

    def generate(self, prompt: str, *, temperature: float = 0.2, max_tokens: int = 2048) -> str:
        """Synchronous generation with tenacity-powered retry for transient LLM errors."""
        retry_pred = retry_if_exception(lambda exc: self._is_retryable(str(exc)))

        def _before_sleep(retry_state):
            try:
                metrics.llm_retries_total.labels(self._model_name).inc()
            except Exception:
                logger.debug("Failed to increment llm_retries_total metric")

        @retry(retry=retry_pred, wait=wait_exponential_jitter(self._backoff_min, self._backoff_max), stop=stop_after_attempt(self._max_retries), before_sleep=_before_sleep)
        def _invoke():
            return self._call_provider(prompt, temperature, max_tokens)

        self._sync_semaphore.acquire()
        start = time.time()
        try:
            try:
                metrics.llm_requests_total.labels(self._model_name).inc()
            except Exception:
                logger.debug("Failed to increment llm_requests_total metric")
            try:
                metrics.llm_inprogress.labels(self._model_name).inc()
            except Exception:
                logger.debug("Failed to inc llm_inprogress metric")

            try:
                result = _invoke()
                return result
            except RetryError as rex:
                last_exc = rex.last_attempt.exception() if rex.last_attempt is not None else None
                logger.error("LLM generation failed after retries: %s", last_exc or rex)
                raise last_exc or RuntimeError("LLM generation failed.")
            finally:
                elapsed = time.time() - start
                try:
                    metrics.llm_request_latency_seconds.labels(self._model_name).observe(elapsed)
                except Exception:
                    logger.debug("Failed to observe llm_request_latency_seconds metric")
                try:
                    metrics.llm_inprogress.labels(self._model_name).dec()
                except Exception:
                    logger.debug("Failed to dec llm_inprogress metric")
        finally:
            self._sync_semaphore.release()

    async def agenerate(self, prompt: str, *, temperature: float = 0.2, max_tokens: int = 2048) -> str:
        """Async wrapper that runs the blocking generate in a threadpool and respects concurrency limits."""
        await self._async_semaphore.acquire()
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self.generate, prompt, temperature=temperature, max_tokens=max_tokens),
                timeout=self._timeout_seconds + 5,
            )
        except asyncio.TimeoutError as exc:
            logger.error("LLM generation timed out after %ds: %s", int(self._timeout_seconds + 5), exc)
            raise RuntimeError("LLM generation timed out") from exc
        finally:
            self._async_semaphore.release()


@lru_cache(maxsize=1)
def get_llm_client() -> BaseLLMClient:
    """Application-level singleton LLM client."""
    settings = get_settings()
    provider = settings.llm_provider.lower()
    if provider == "gemini":
        return LiteLLMGeminiClient(model=settings.llm_model, api_key=settings.llm_api_key)
    raise ValueError(f"Unsupported llm_provider '{provider}'. {settings.unsupported_provider_help}")
