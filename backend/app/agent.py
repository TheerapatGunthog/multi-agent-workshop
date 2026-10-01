"""Docs Agent จาก workshop 1 (สถานะ solution-step-4)

ใน workshop 2 ไฟล์นี้คือ agent ตัวเดียวแบบเดิม ใช้เป็นจุดเริ่มต้น:
- Step 3 จะเปลี่ยนให้ใช้ memory แทน history จาก frontend
- Step 4 จะย้าย /chat ไปใช้ agents/orchestrator.py แทน
"""
import asyncio
import json
import re
from typing import AsyncIterator

from openai import AsyncOpenAI

from .config import settings
from .retrieval import Chunk, search
from .sse import sse

client = AsyncOpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)

SYSTEM_PROMPT = """คุณคือผู้ช่วยตอบคำถามจากเอกสาร ใช้ tool search_docs ค้นหาข้อมูลก่อนตอบทุกครั้ง

กฎการอ้างอิง:
- ตอบโดยใช้ข้อมูลจากผลการค้นหาเท่านั้น
- ใส่ [n] ท้ายประโยคที่ใช้ข้อมูลจากแหล่งที่ n
- ใช้ได้เฉพาะเลขที่ปรากฏในผลการค้นหาเท่านั้น
- ถ้าประโยคใช้หลายแหล่ง ให้ใส่ [1][2]
- ถ้าไม่พบข้อมูลในผลการค้นหา ให้ตอบว่า "ไม่พบข้อมูลในเอกสาร" ห้ามเดา
- ตอบเป็นภาษาไทย"""

SEARCH_DOCS_TOOL = {
    "type": "function",
    "function": {
        "name": "search_docs",
        "description": "ค้นหาข้อความที่เกี่ยวข้องจากเอกสาร PDF ในระบบ",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "คำค้นหา"},
            },
            "required": ["query"],
        },
    },
}

MAX_TOOL_ROUNDS = 3


def format_chunks(chunks: list[Chunk], start_id: int) -> str:
    """แปลง chunks เป็นข้อความสำหรับส่งกลับให้ LLM โดยกำกับเลข [n] ต่อจาก start_id

    ตัวอย่าง:
        [1] (leave-handbook.pdf หน้า 2)
        พนักงานที่ทำงานครบหนึ่งปี...
    """
    return "\n\n".join(
        f"[{start_id + i}] ({c.filename} หน้า {c.page})\n{c.text}" for i, c in enumerate(chunks)
    )


CITE = re.compile(r"\[(\d+)\]")


async def run_agent(message: str, history: list[dict]) -> AsyncIterator[str]:
    """tool-calling loop แล้ว stream คำตอบตาม contract: token หลายครั้ง → citations → done"""
    if not settings.llm_model:
        raise RuntimeError("ยังไม่ได้ตั้ง LLM_MODEL ใน .env")

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += [h for h in history if h.get("role") in ("user", "assistant")]
    messages.append({"role": "user", "content": message})

    citations: dict[int, dict] = {}
    next_id = 1  # นับต่อเนื่องทุกรอบ ห้ามเริ่ม 1 ใหม่

    for _ in range(MAX_TOOL_ROUNDS):
        res = await client.chat.completions.create(
            model=settings.llm_model, messages=messages, tools=[SEARCH_DOCS_TOOL]
        )
        reply = res.choices[0].message
        if not reply.tool_calls:
            break
        messages.append(reply.model_dump(exclude_none=True))
        for call in reply.tool_calls:
            try:
                query = json.loads(call.function.arguments or "{}").get("query", message)
            except json.JSONDecodeError:
                query = message
            chunks = await asyncio.to_thread(search, query)
            for i, c in enumerate(chunks):
                cid = next_id + i
                citations[cid] = {
                    "id": cid,
                    "doc_id": c.doc_id,
                    "filename": c.filename,
                    "page": c.page,
                    "quote": c.text[:200],
                }
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": format_chunks(chunks, next_id) or "ไม่พบผลลัพธ์"}
            )
            next_id += len(chunks)

    answer = ""
    stream = await client.chat.completions.create(model=settings.llm_model, messages=messages, stream=True)
    async for part in stream:
        delta = part.choices[0].delta.content if part.choices else None
        if delta:
            answer += delta
            yield sse("token", {"text": delta})

    yield sse("citations", {"citations": validate_citations(answer, list(citations.values()))})
    yield sse("done", {})


def validate_citations(answer: str, citations: list[dict]) -> list[dict]:
    """คืนเฉพาะ citation ที่ถูกอ้างถึงใน answer และมีอยู่ในผลค้นหาจริง เรียงตาม id"""
    cited = {int(n) for n in CITE.findall(answer)}
    return sorted((c for c in citations if c["id"] in cited), key=lambda c: c["id"])
