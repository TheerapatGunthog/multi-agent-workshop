"""Step 2 · MCP client — ผู้เข้าร่วมเขียน (prompt W2-S2 ใน PROMPTS.md)

ต่อ MCP server สองตัว (settings.docs_mcp_url, settings.hr_mcp_url) ผ่าน Streamable HTTP
ชื่อ tool ที่เปิดให้ LLM ใช้ต้อง prefix ด้วย "docs__" หรือ "hr__" (ชื่อ function ของ OpenAI มีจุดไม่ได้)
ใช้ MCP Python SDK 1.x: from mcp import ClientSession
                      from mcp.client.streamable_http import streamablehttp_client
"""
from typing import Any


class ToolHub:
    async def connect(self) -> None:
        """เปิด session กับทั้งสอง server แล้ว list_tools"""
        raise NotImplementedError("Step 2: ยังไม่ได้เขียน ToolHub.connect()")

    def openai_tools(self, prefix: str | None = None) -> list[dict]:
        """แปลง tool เป็น OpenAI tool schema กรองตาม prefix ได้"""
        raise NotImplementedError("Step 2: ยังไม่ได้เขียน ToolHub.openai_tools()")

    async def call(self, name: str, arguments: dict) -> Any:
        """ตัด prefix แล้วเรียก call_tool บน server ที่ถูกต้อง"""
        raise NotImplementedError("Step 2: ยังไม่ได้เขียน ToolHub.call()")

    async def close(self) -> None:
        raise NotImplementedError("Step 2: ยังไม่ได้เขียน ToolHub.close()")


async def get_tool_hub() -> ToolHub:
    """singleton ที่ connect ครั้งแรกที่ถูกเรียก"""
    raise NotImplementedError("Step 2: ยังไม่ได้เขียน get_tool_hub()")
