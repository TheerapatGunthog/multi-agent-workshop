"""Step 4 · Orchestrator — ผู้เข้าร่วมเขียน

รับคำขอ → memory → make_plan → research ตาม dependency (ระดับเดียวกันรันขนาน)
→ write_document หรือ write_answer → registry.validate → ส่ง event ผ่าน bus แล้ว bus.close() เสมอ
event ที่ต้องส่ง: plan, activity, progress, document หรือ token, citations, done (ดู AGENTS.md)
"""
from ..events import EventBus


async def run(message: str, session_id: str, bus: EventBus) -> None:
    raise NotImplementedError("Step 4: ยังไม่ได้เขียน run() ใน backend/app/agents/orchestrator.py")
