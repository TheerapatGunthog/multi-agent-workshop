"""Mock mode: stream event ตาม contract ผ่าน SSE แบบเดียวกับ agent จริง (ไม่เรียก LLM)

- คำถามทั่วไป   → contract/chat-response.json      (token → citations → done) แบบ workshop 1
- คำว่า "เอกสาร" → contract/document-response.json  (plan → activity/progress → document → citations → done)
"""
import asyncio
import json
from typing import AsyncIterator

from .config import settings
from .sse import sse


async def mock_stream(message: str = "") -> AsyncIterator[str]:
    if "เอกสาร" in message:
        async for event in _document_stream():
            yield event
        return
    payload = json.loads(settings.contract_path.read_text(encoding="utf-8"))
    answer: str = payload["answer"]
    for i in range(0, len(answer), 4):
        yield sse("token", {"text": answer[i : i + 4]})
        await asyncio.sleep(0.015)
    yield sse("citations", {"citations": payload["citations"]})
    yield sse("done", {})


async def _document_stream() -> AsyncIterator[str]:
    payload = json.loads(settings.document_contract_path.read_text(encoding="utf-8"))
    for item in payload["events"]:
        yield sse(item["event"], item["data"])
        await asyncio.sleep(0.35 if item["event"] in ("activity", "progress") else 0.05)
