"""Step 4 · Docs agent — ผู้เข้าร่วมเขียน

เขียนจาก research notes เท่านั้น อ้าง [id] ได้เฉพาะ id ใน findings
data จากระบบ (hr-mcp) ห้ามมี [n] และ gaps ให้เขียนว่าไม่พบข้อมูลในเอกสาร
"""
from typing import AsyncIterator


async def write_document(goal: str, outline: list[str], notes: list[dict], registry) -> str:
    """โหมดเอกสาร: คืน markdown ทั้งฉบับ หัวข้อ ## ตาม outline"""
    raise NotImplementedError("Step 4: ยังไม่ได้เขียน write_document()")


async def write_answer(question: str, notes: list[dict], registry) -> AsyncIterator[str]:
    """โหมด chat: stream คำตอบสั้นทีละชิ้นข้อความ"""
    raise NotImplementedError("Step 4: ยังไม่ได้เขียน write_answer()")
    yield ""  # ทำให้ฟังก์ชันนี้เป็น async generator
