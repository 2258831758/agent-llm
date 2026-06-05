from __future__ import annotations

import asyncio
import contextlib
import json
from collections import defaultdict
from collections.abc import AsyncIterator
from datetime import datetime, timezone

from backend.app.core.config import settings
from backend.app.core.redis_client import get_redis


class AuditEventBus:
    def __init__(self) -> None:
        self._history: dict[str, list[str]] = defaultdict(list)
        self._subscribers: dict[str, list[asyncio.Queue[str]]] = defaultdict(list)

    @staticmethod
    def history_key(task_id: str) -> str:
        return f"audit:history:{task_id}"

    @staticmethod
    def channel_key(task_id: str) -> str:
        return f"audit:events:{task_id}"

    async def publish(self, task_id: str, payload: dict[str, object]) -> None:
        payload.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        raw = json.dumps(payload, ensure_ascii=False)
        self._history[task_id].append(raw)
        self._history[task_id] = self._history[task_id][-settings.report_history_limit :]

        for queue in list(self._subscribers[task_id]):
            queue.put_nowait(raw)

        try:
            redis = await get_redis()
            await redis.rpush(self.history_key(task_id), raw)
            await redis.ltrim(self.history_key(task_id), -settings.report_history_limit, -1)
            await redis.publish(self.channel_key(task_id), raw)
        except Exception:
            return

    async def read_history(self, task_id: str) -> list[dict[str, object]]:
        try:
            redis = await get_redis()
            values = await redis.lrange(self.history_key(task_id), 0, -1)
            if values:
                return [json.loads(item) for item in values]
        except Exception:
            pass
        return [json.loads(item) for item in self._history[task_id]]

    async def subscribe(self, task_id: str) -> AsyncIterator[dict[str, object]]:
        queue: asyncio.Queue[str] = asyncio.Queue()
        pubsub = None
        use_local_queue = False

        try:
            try:
                redis = await get_redis()
                pubsub = redis.pubsub()
                await pubsub.subscribe(self.channel_key(task_id))
            except Exception:
                use_local_queue = True
                self._subscribers[task_id].append(queue)

            if use_local_queue:
                while True:
                    raw = await queue.get()
                    yield json.loads(raw)
            else:
                assert pubsub is not None
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        yield json.loads(message["data"])
        finally:
            if use_local_queue:
                self._subscribers[task_id] = [item for item in self._subscribers[task_id] if item is not queue]
            if pubsub is not None:
                with contextlib.suppress(Exception):
                    await pubsub.unsubscribe(self.channel_key(task_id))
                with contextlib.suppress(Exception):
                    await pubsub.aclose()

event_bus = AuditEventBus()
