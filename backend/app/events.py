"""Event bus → SSE — ทำไว้ให้แล้ว ห้ามแก้ shape ของ event (ดู AGENTS.md)

หนึ่ง request มี EventBus เดียว ทุก agent ส่ง event เข้า queue นี้ แล้ว /chat ดึงออกไปส่งเป็น SSE
event ที่รองรับ: plan, activity, progress, document, token, citations, done, error
"""
import asyncio
from typing import AsyncIterator

from .sse import sse

KEEPALIVE_SECONDS = 15
_CLOSE = object()


class EventBus:
    def __init__(self) -> None:
        self._queue: asyncio.Queue = asyncio.Queue()
        self.closed = False

    async def emit(self, event: str, data: dict) -> None:
        if not self.closed:
            await self._queue.put(sse(event, data))

    async def activity(self, agent: str, task_id: str, kind: str, message: str) -> None:
        """kind: thinking | tool_call | tool_result | note | error"""
        await self.emit("activity", {"agent": agent, "task_id": task_id, "kind": kind, "message": message})

    async def progress(self, done: int, total: int, current_task: str) -> None:
        await self.emit("progress", {"done": done, "total": total, "current_task": current_task})

    async def close(self) -> None:
        if not self.closed:
            self.closed = True
            await self._queue.put(_CLOSE)

    async def stream(self) -> AsyncIterator[str]:
        """ส่ง SSE ไปเรื่อย ๆ จนกว่าจะ close ถ้าเงียบนาน 15 วินาทีส่ง ping กัน proxy ตัด connection"""
        while True:
            try:
                item = await asyncio.wait_for(self._queue.get(), timeout=KEEPALIVE_SECONDS)
            except asyncio.TimeoutError:
                yield ": ping\n\n"
                continue
            if item is _CLOSE:
                return
            yield item
