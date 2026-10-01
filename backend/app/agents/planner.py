"""Step 4 · Planning agent — ผู้เข้าร่วมเขียน

คืน plan ตาม contract ใน AGENTS.md:
    {"goal": str, "tasks": [{"id", "agent": "research"|"docs", "question"?, "outline"?, "depends_on": [...]}]}
บังคับรูปแบบด้วย response_format json_schema แล้วตรวจซ้ำ: id ไม่ซ้ำ, depends_on มีจริง, ไม่เกิน 5 task
"""


async def make_plan(message: str, context: list[dict]) -> dict:
    raise NotImplementedError("Step 4: ยังไม่ได้เขียน make_plan() ใน backend/app/agents/planner.py")
