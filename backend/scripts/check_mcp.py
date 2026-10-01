"""ตรวจว่า MCP server ทั้งสองตัวทำงาน: docker compose exec backend python scripts/check_mcp.py

ต่อด้วย MCP SDK โดยตรง (ไม่ใช้ tools.py ที่ผู้เข้าร่วมเขียนใน Step 2)
search_docs ต้อง ingest แล้วและตั้ง EMBED_MODEL ถ้ายังไม่พร้อมจะเห็น error ของ tool นั้นแต่ไม่ถือว่า server พัง
"""
import asyncio
import json

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from app.config import settings

CALLS = {
    settings.docs_mcp_url: [("get_page", {"doc_id": "welfare-handbook", "page": 2}), ("search_docs", {"query": "ค่ารักษาพยาบาล", "k": 2})],
    settings.hr_mcp_url: [("leave_balance", {"employee_id": "E001"})],
}


async def probe(url: str, calls: list) -> None:
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(f"{url}\n  tools: {[t.name for t in tools.tools]}")
            for name, args in calls:
                res = await session.call_tool(name, args)
                text = " ".join(c.text for c in res.content if hasattr(c, "text"))
                status = "ERROR" if res.isError else "ok"
                print(f"  {name}: {status} {json.dumps(json.loads(text), ensure_ascii=False)[:150] if not res.isError else text[:150]}")


async def main() -> None:
    for url, calls in CALLS.items():
        await probe(url, calls)


asyncio.run(main())
