from __future__ import annotations

from typing import List, Protocol
import asyncio


class ConversationStore(Protocol):
    async def get_history(self, conversation_id: str) -> List[dict[str, str]]:
        ...

    async def append(self, conversation_id: str, role: str, content: str) -> None:
        ...

    async def create_conversation(self) -> str:
        ...


class InMemoryConversationStore:
    def __init__(self) -> None:
        self._store: dict[str, list[dict[str, str]]] = {}
        self._lock = asyncio.Lock()

    async def get_history(self, conversation_id: str) -> List[dict[str, str]]:
        return list(self._store.get(conversation_id, []))

    async def append(self, conversation_id: str, role: str, content: str) -> None:
        async with self._lock:
            self._store.setdefault(conversation_id, []).append({"role": role, "content": content})

    async def create_conversation(self) -> str:
        import uuid

        cid = str(uuid.uuid4())
        async with self._lock:
            self._store.setdefault(cid, [])
        return cid


class RedisConversationStore:
    """Redis-backed conversation store (async) using redis.asyncio. Lazy import."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0", key_prefix: str = "conv:") -> None:
        try:
            import redis.asyncio as aioredis
        except Exception as exc:
            raise RuntimeError(f"redis.asyncio is required for RedisConversationStore: {exc}")
        self._client = aioredis.from_url(redis_url)
        self._prefix = key_prefix

    async def get_history(self, conversation_id: str) -> List[dict[str, str]]:
        key = f"{self._prefix}{conversation_id}"
        raw = await self._client.lrange(key, 0, -1)
        # stored as JSON strings
        import json

        return [json.loads(item) for item in raw]

    async def append(self, conversation_id: str, role: str, content: str) -> None:
        key = f"{self._prefix}{conversation_id}"
        import json

        await self._client.rpush(key, json.dumps({"role": role, "content": content}))
        # set TTL for cleanup
        await self._client.expire(key, 60 * 60 * 24)

    async def create_conversation(self) -> str:
        import uuid

        cid = str(uuid.uuid4())
        # ensure key exists
        key = f"{self._prefix}{cid}"
        await self._client.rpush(key, "[]")
        await self._client.lpop(key)
        await self._client.expire(key, 60 * 60 * 24)
        return cid
