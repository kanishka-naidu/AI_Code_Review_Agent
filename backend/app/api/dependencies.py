from functools import lru_cache

from app.core.config import get_settings
from app.services.analysis_service import AnalysisService
from app.services.assistant_service import AssistantService
from app.services.upload_service import UploadService


def get_settings_dependency():
    return get_settings()


def get_upload_service() -> UploadService:
    return _upload_service()


def get_analysis_service() -> AnalysisService:
    return _analysis_service()


def get_assistant_service() -> AssistantService:
    return _assistant_service()


@lru_cache(maxsize=1)
def _upload_service() -> UploadService:
    return UploadService()


@lru_cache(maxsize=1)
def _analysis_service() -> AnalysisService:
    return AnalysisService()


@lru_cache(maxsize=1)
def _assistant_service() -> AssistantService:
    settings = get_settings()
    # Lazy import of conversation store implementations
    conversation_store = None
    if settings.redis_conversations_enabled:
        try:
            from app.services.conversation_store import RedisConversationStore

            conversation_store = RedisConversationStore(redis_url=settings.redis_url, key_prefix=settings.redis_conversation_key_prefix)
        except Exception:
            # Fallback to in-memory if Redis not available at startup
            from app.services.conversation_store import InMemoryConversationStore

            conversation_store = InMemoryConversationStore()
    else:
        from app.services.conversation_store import InMemoryConversationStore

        conversation_store = InMemoryConversationStore()

    return AssistantService(upload_service=_upload_service(), conversation_store=conversation_store)
