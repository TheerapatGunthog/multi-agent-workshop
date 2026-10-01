"""Step 1 · Research agent แบบ agentic RAG — ผู้เข้าร่วมเขียน (prompt W2-S1 ใน PROMPTS.md)

รับ task {"id", "question"} แล้วคืน research note ตาม contract ใน AGENTS.md:
    {"task_id": str, "findings": [{"text": str, "citations": [int]}], "data": [...], "gaps": [str]}

แนวทาง: เขียน query ใหม่ → ค้น → คัด chunk → ข้อมูลพอหรือยัง (ไม่เกิน 3 รอบ) → เขียน note
chunk ที่ใช้ต้อง registry.register() แล้วอ้างด้วย id จาก registry เท่านั้น
ของที่ใช้ได้: search() ใน retrieval.py (Step 2 จะเปลี่ยนไปค้นผ่าน MCP)
"""
from .registry import CitationRegistry


async def run_research(task: dict, registry: CitationRegistry, bus=None) -> dict:
    raise NotImplementedError("Step 1: ยังไม่ได้เขียน run_research() ใน backend/app/research.py")
