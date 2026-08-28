"""Application service for the conversational code assistant."""
from __future__ import annotations

from typing import Any

from app.agents.assistant_agent import AssistantAgent
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.request_models import AssistantRequest
from app.models.response_models import AssistantResponse
from app.services.upload_service import UploadService
from app.services.conversation_store import ConversationStore, InMemoryConversationStore

logger = get_logger(__name__)


class AssistantService:
    """Coordinates assistant context assembly and conversation memory."""

    def __init__(
        self,
        upload_service: UploadService | None = None,
        assistant_agent: AssistantAgent | None = None,
        conversation_store: ConversationStore | None = None,
    ) -> None:
        self._settings = get_settings()
        self._upload_service = upload_service or UploadService()
        self._assistant = assistant_agent or AssistantAgent()
        # Conversation store is async-capable. Default to in-memory store for dev/test.
        self._conversation_store: ConversationStore = conversation_store or InMemoryConversationStore()

    async def answer(self, request: AssistantRequest) -> AssistantResponse:
        """Answer a user question with optional uploaded code/report context."""
        conversation_id = request.conversation_id or await self._conversation_store.create_conversation()
        # Include uncommitted current question in history so the assistant sees it
        history = await self._conversation_store.get_history(conversation_id)
        analysis_context = self._build_context(request)
        # Await the async assistant agent
        answer, sources = await self._assistant.answer(
            request.question,
            analysis_context=analysis_context,
            conversation_history=history,
        )
        # Update history after successful generation
        await self._conversation_store.append(conversation_id, "user", request.question)
        await self._conversation_store.append(conversation_id, "assistant", answer)
        logger.info("AssistantService answered conversation_id='%s' sources=%d", conversation_id, len(sources))
        return AssistantResponse(answer=answer, sources=sources, conversation_id=conversation_id)

    def _build_context(self, request: AssistantRequest) -> dict[str, Any]:
        source_code = self._load_source_code(request.source_id) if request.source_id else None
        base_context: dict[str, Any] = {}
        if request.context:
            base_context["user_context"] = request.context
        if request.report:
            base_context.update(self._assistant.prepare_context(request.report, source_code=source_code))
        elif source_code:
            base_context["source_code"] = source_code
        # Pass the user's preferred response detail level so the assistant can
        # tailor its answer (concise vs detailed).
        if request.assistant_detail_level:
            base_context["assistant_detail_level"] = request.assistant_detail_level
        return base_context

    def _load_source_code(self, source_id: str | None) -> str | None:
        if not source_id:
            return None
        matches = list(self._upload_service.settings.upload_path.glob(f"{source_id}_*"))
        if not matches:
            return None
        return matches[0].read_text(encoding="utf-8")
