"""hr-mcp: MCP server จำลองระบบ HR — ทำไว้ให้แล้ว (Step 2 code tour)

ข้อมูลทั้งหมดเป็นข้อมูลสมมติสำหรับ workshop ไม่ได้ต่อระบบจริง
ข้อมูลจาก server นี้ไม่ใช่เอกสาร จึงต้องไม่มี citation [n] ในคำตอบ

Tools:
  leave_balance(employee_id) -> {employee_id, name, annual_left, sick_used}
"""
import os
import sys

from mcp.server.fastmcp import FastMCP

if os.getenv("IN_DOCKER") != "1":
    sys.exit("[hr-mcp] ต้องรันผ่าน Docker เท่านั้น: docker compose up --build")

# ข้อมูลสมมติ
EMPLOYEES = {
    "E001": {"name": "สมชาย ใจดี", "annual_left": 6, "sick_used": 2},
    "E002": {"name": "สมหญิง รักงาน", "annual_left": 10, "sick_used": 0},
    "E003": {"name": "วิชัย ตั้งใจ", "annual_left": 3, "sick_used": 5},
    "E004": {"name": "มาลี ขยัน", "annual_left": 12, "sick_used": 1},
    "E005": {"name": "ประเสริฐ มั่นคง", "annual_left": 0, "sick_used": 8},
}

mcp = FastMCP(
    "hr-mcp",
    instructions="ระบบ HR จำลอง ใช้ดูข้อมูลวันลาของพนักงานรายคน",
    host="0.0.0.0",
    port=int(os.getenv("PORT", "8000")),
)


@mcp.tool()
def leave_balance(employee_id: str) -> dict:
    """ดูวันลาพักผ่อนคงเหลือ (annual_left) และวันลาป่วยที่ใช้ไปแล้วในปีนี้ (sick_used) ของพนักงาน
    ใช้เมื่อคำถามระบุรหัสพนักงาน เช่น E001"""
    emp = EMPLOYEES.get(employee_id.strip().upper())
    if not emp:
        return {"employee_id": employee_id, "error": "ไม่พบพนักงานรหัสนี้"}
    return {"employee_id": employee_id.strip().upper(), **emp}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
