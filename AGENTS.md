# AGENTS.md — context สำหรับ AI coding tool

อ่านไฟล์นี้ก่อนแก้โค้ดทุกครั้ง ข้อกำหนดตรงนี้สำคัญกว่าค่า default ของ tool

## โปรเจกต์นี้คืออะไร

ต่อยอด docs agent จาก workshop 1 ให้เป็นระบบหลาย agent ที่สั่งงานประโยคเดียวแล้วได้เอกสารทั้งฉบับ
ทุกประโยคยังมี citation `[n]` ที่คลิกแล้วเปิด PDF ไปหน้าที่อ้างอิงพร้อม highlight

- `frontend/` Next.js 14 + react-pdf — **ทำเสร็จแล้ว** รองรับ event ใหม่ทั้งหมด (Activity panel, Document view)
- `backend/` FastAPI — `agent.py` คือ agent ตัวเดียวจาก workshop 1 (ทำงานได้แล้ว) และเป็นจุดเริ่มต้น
- `mcp_servers/` MCP server สองตัว (docs-mcp, hr-mcp) — **ทำเสร็จแล้ว**
- `contract/` ตัวอย่าง event ที่ frontend คาดหวัง ใช้ใน Mock mode
- `data/pdfs/` เอกสารสมมติ 3 ไฟล์: leave-handbook, welfare-handbook, expense-policy

## กฎบังคับ

1. **รันทุกอย่างผ่าน Docker เท่านั้น** ห้ามแนะนำ `pip install`, `uvicorn`, `npm run dev` บนเครื่อง
   - เริ่มระบบ: `docker compose up --build`
   - รันคำสั่งใน backend: `docker compose exec backend <command>` (script ใน `backend/scripts/` import `app` ได้เพราะตั้ง `PYTHONPATH=/app` แล้ว)
   - เพิ่ม Python package: แก้ `backend/requirements.txt` แล้ว `docker compose up --build backend`
   - ingest PDF: `docker compose run --rm backend python ingest.py`
2. **ห้ามเปลี่ยน shape ของ contract** ทุกตัวด้านล่าง (citation, plan, research note, SSE events)
3. **ห้ามแก้** `backend/app/registry.py`, `backend/app/events.py`, `backend/app/retrieval.py`, `backend/ingest.py`, `mcp_servers/`, `contract/`, `frontend/` เว้นแต่ผู้ใช้สั่งตรง ๆ
4. ใช้ `openai` SDK ที่ชี้ไป `LLM_BASE_URL` (OpenAI-compatible) ห้ามเพิ่ม framework agent อื่น (LangChain, LangGraph ฯลฯ)
5. MCP ใช้ **MCP Python SDK 1.x** (`mcp==1.30.0`) ห้ามอัปเกรดเป็น 2.x เพราะ `FastMCP` ถูกเปลี่ยนชื่อและ API เปลี่ยน
6. อ่านค่าจาก `app/config.py` (`settings`) ห้าม hard-code URL หรือชื่อ model
7. LLM call ที่ต้องการ JSON ให้ใช้ `response_format={"type": "json_schema", "json_schema": {"name": ..., "schema": ...}}` และมี fallback เมื่อ parse ไม่ได้

## Citation contract (เหมือน workshop 1)

```json
{ "id": 1, "doc_id": "leave-handbook", "filename": "leave-handbook.pdf", "page": 2, "quote": "ข้อความจาก chunk" }
```

- ทุก field มาจากผลค้นหา **ห้ามให้ LLM แต่งเลขหน้าหรือชื่อไฟล์** `page` เป็น 1-based
- LLM อ้างได้แค่ `[id]`

## Citation registry (`backend/app/registry.py` ทำไว้ให้แล้ว)

หนึ่ง request มี `CitationRegistry()` เดียว ทุก agent ขอ id จากที่นี่ ห้ามนับ `[n]` เอง

| method | ทำอะไร |
| --- | --- |
| `register(chunk) -> int` | รับ dict/object ที่มี doc_id, filename, page, text คืน id (chunk เดิมได้ id เดิม) |
| `get(cid) -> dict` | citation ตาม contract |
| `ids() -> set[int]` | id ทั้งหมดที่มี |
| `validate(markdown) -> list[dict]` | citation ของ id ที่ถูกอ้างใน markdown และมีอยู่จริง เรียงตาม id |

registry สร้างใหม่ทุก request ดังนั้น **ต้องตัด `[n]` ออกก่อนเก็บคำตอบลง memory**

## Plan (Planning agent → Orchestrator)

```json
{
  "goal": "เอกสารสรุปสิทธิการลาสำหรับพนักงานใหม่",
  "tasks": [
    { "id": "t1", "agent": "research", "question": "สิทธิลาพักผ่อนและการสะสมวันลา", "depends_on": [] },
    { "id": "t4", "agent": "docs", "outline": ["การลาพักผ่อน", "การลาป่วย"], "depends_on": ["t1"] }
  ]
}
```

ตรวจหลัง parse: id ไม่ซ้ำ, `depends_on` อ้าง task ที่มีจริงและไม่วน, ไม่เกิน 5 task, research มี `question`, docs มี `outline`
ไม่มี docs task = คำถามสั้น ตอบใน chat

## Research note (Research agent → Docs agent)

```json
{
  "task_id": "t1",
  "findings": [{ "text": "ลาพักผ่อนได้ปีละ 10 วันทำงาน", "citations": [1] }],
  "data": [{ "source": "hr-mcp", "text": "พนักงาน E001 เหลือวันลาพักผ่อน 6 วัน" }],
  "gaps": ["ไม่พบเงื่อนไขของพนักงานชั่วคราว"]
}
```

- `findings` ทุกข้อต้องมี citation id จาก registry
- `data` คือข้อมูลจากระบบ (ไม่ใช่เอกสาร) **ห้ามมี citation**
- `gaps` คือสิ่งที่ค้นไม่เจอ Docs agent ต้องเขียนว่าไม่พบ ห้ามเดาเติม

## SSE ที่ `POST /chat` ส่ง

| event | data | เมื่อไร |
| --- | --- | --- |
| `token` | `{"text": "..."}` | โหมด chat: หลายครั้งระหว่าง stream คำตอบ |
| `plan` | `{"tasks": [{"id", "agent", "title"}]}` | หลัง Planning agent ทำเสร็จ |
| `activity` | `{"agent", "task_id", "kind", "message"}` | ทุกครั้งที่ agent ทำอะไร `kind`: `thinking` `tool_call` `tool_result` `note` `error` |
| `progress` | `{"done", "total", "current_task"}` | เมื่อ task เริ่มหรือจบ |
| `document` | `{"title", "markdown"}` | โหมดเอกสาร: เมื่อ Docs agent เขียนเสร็จ |
| `citations` | `{"citations": [Citation]}` | ครั้งเดียว หลัง validate |
| `done` | `{}` | ปิดท้ายเสมอ |
| `error` | `{"message": "..."}` | เกิดข้อผิดพลาด |

- ใช้ `EventBus` จาก `backend/app/events.py` (`emit`, `activity`, `progress`, `close`, `stream`) ทุก event จาก research ต้องมี `task_id`
- `message` ของ activity เป็นภาษาไทยสั้น ๆ ไม่เกิน 120 ตัวอักษร ห้ามใส่ prompt, JSON ดิบ หรือข้อความจาก chunk
- ตัวอย่างลำดับ event ครบชุด: `contract/document-response.json`

## MCP servers (ทำไว้ให้แล้ว)

| server | URL ใน Docker | tool | คืนค่า (JSON ใน text content) |
| --- | --- | --- | --- |
| docs-mcp | `settings.docs_mcp_url` | `search_docs(query, k=5)` | `{"chunks": [{doc_id, filename, page, text, score}]}` |
| | | `get_page(doc_id, page)` | `{doc_id, filename, page, text}` |
| hr-mcp | `settings.hr_mcp_url` | `leave_balance(employee_id)` | `{employee_id, name, annual_left, sick_used}` หรือ `{employee_id, error}` |

- ผลของ `call_tool` อยู่ใน `content[0].text` เป็น JSON (`structuredContent` เป็น `None`) ถ้า `isError` เป็นจริงให้ถือว่า tool ล้ม
- ชื่อ tool ที่เปิดให้ LLM ใช้ต้อง prefix ด้วย `docs__` หรือ `hr__` เพราะชื่อ function ของ OpenAI มีจุดไม่ได้
- ตรวจว่า server ทำงาน: `docker compose exec backend python scripts/check_mcp.py`

## งานของ workshop (ไฟล์ที่แก้ได้ในแต่ละ step)

| Step | งาน | ไฟล์ |
| --- | --- | --- |
| 1 | Agentic RAG: `run_research(task, registry, bus=None) -> dict` | `backend/app/research.py`, `backend/scripts/` |
| 2 | MCP client: `ToolHub`, `get_tool_hub()` และให้ research ค้นผ่าน MCP | `backend/app/tools.py`, `backend/app/research.py`, `backend/scripts/` |
| 3 | Memory: `ConversationMemory`, `get_memory(session_id)` | `backend/app/memory.py`, `backend/app/agent.py`, `backend/app/main.py`, `backend/scripts/` |
| 4 | `make_plan`, `write_document`, `write_answer`, `run(message, session_id, bus)` และให้ `/chat` ใช้ orchestrator | `backend/app/agents/`, `backend/app/main.py`, `backend/scripts/` |
| 5 | เติม activity/progress ให้ครบ | `research.py`, `tools.py`, `agents/` |

prompt ของแต่ละ step อยู่ใน `PROMPTS.md`
