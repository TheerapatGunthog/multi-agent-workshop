"""Step 3 · Memory: sliding window + running summary — ผู้เข้าร่วมเขียน (prompt W2-S3 ใน PROMPTS.md)

สิ่งที่ส่งให้ LLM: system + summary ของ turn เก่า + turn ล่าสุดที่อยู่ใน token budget + คำถามใหม่
ข้อห้าม: ต้องตัด [n] ออกก่อนเก็บลง history เพราะ registry สร้างใหม่ทุก request
"""


class ConversationMemory:
    def __init__(self) -> None:
        raise NotImplementedError("Step 3: ยังไม่ได้เขียน ConversationMemory ใน backend/app/memory.py")


def get_memory(session_id: str) -> ConversationMemory:
    raise NotImplementedError("Step 3: ยังไม่ได้เขียน get_memory()")
