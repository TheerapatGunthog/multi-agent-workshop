# Multi-agent Workshop

ต่อยอด docs agent จาก workshop 1 ให้เป็นระบบหลาย agent: สั่งประโยคเดียวแล้วได้เอกสารทั้งฉบับ
ทุกประโยคยังมี citation `[n]` ที่คลิกแล้วเปิด PDF ไปหน้าที่อ้างอิงพร้อม highlight
และเห็นความคืบหน้าของทุก agent แบบ real-time

repo นี้เริ่มจากเฉลยของ workshop 1 (`agent.py` ทำงานได้แล้ว) คนที่ไม่ได้เข้า workshop 1 เริ่มที่นี่ได้เลย

## เริ่มต้น

ต้องมี Docker Desktop (หรือ Docker Engine + Compose v2.24 ขึ้นไป) และ LLM แบบ OpenAI-compatible
ที่รองรับ tool calling และ `response_format` แบบ `json_schema` (เช่น vLLM)

```bash
cp .env.example .env              # ใส่ LLM_MODEL, EMBED_MODEL และ URL ที่ผู้สอนแจก
docker compose up --build         # container 5 ตัว: qdrant, docs-mcp, hr-mcp, backend, frontend
docker compose run --rm backend python ingest.py
```

เปิด http://localhost:3000 ตอนแรก `MOCK_MODE=true` ระบบตอบจาก `contract/` โดยไม่เรียก LLM

- คำถามทั่วไป → คำตอบพร้อมปุ่ม `[n]` แบบ workshop 1
- คำถามที่มีคำว่า "เอกสาร" → Activity panel + เอกสารทั้งฉบับ (ตัวอย่างของสิ่งที่จะสร้างใน Step 4)

ถ้ามี container ของ workshop 1 รันอยู่ ให้ `docker compose down` ใน repo นั้นก่อน เพราะใช้ port 3000/8000 เหมือนกัน

## ตรวจของที่ทำไว้ให้

```bash
docker compose exec backend python check_validate.py    # validator จาก workshop 1
docker compose exec backend python check_registry.py    # CitationRegistry
docker compose exec backend python check_events.py      # EventBus
docker compose exec backend python scripts/check_mcp.py  # MCP servers ทั้งสองตัว
```

หรือ `make check` (`search_docs` ใน `check_mcp.py` ต้อง ingest แล้วและตั้ง `EMBED_MODEL`)

## ลำดับงาน

| Step | หัวข้อ | ไฟล์ที่เขียน |
| --- | --- | --- |
| 1 | vanilla RAG → agentic RAG | `backend/app/research.py` |
| 2 | ต่อ tools ผ่าน MCP | `backend/app/tools.py` |
| 3 | Memory: sliding window + summary | `backend/app/memory.py` |
| 4 | Multi-agent: Planning agent + Docs agent | `backend/app/agents/` |
| 5 | Activity & progress | เติม event ใน step 1–4 |

prompt ของแต่ละ step อยู่ใน `PROMPTS.md` และ contract ทั้งหมดอยู่ใน `AGENTS.md`
ตามไม่ทันให้ `git stash && git checkout solution-w2-step-n` ของ step ก่อนหน้า

## โครงสร้าง

```
AGENTS.md / CLAUDE.md     context สำหรับ AI coding tool (contract, กฎ, ไฟล์ที่แก้ได้)
PROMPTS.md                prompt สำหรับ vibe code Step 1–5
contract/                 ตัวอย่าง event ที่ frontend คาดหวัง (ใช้ใน Mock mode)
data/pdfs/                เอกสารสมมติ 3 ไฟล์ (คู่มือการลา, สวัสดิการ, เบิกค่าใช้จ่าย)
data/sources/             HTML ต้นฉบับของ PDF ที่เพิ่มใน workshop 2
mcp_servers/docs_mcp/     MCP server ค้นเอกสาร: search_docs, get_page
mcp_servers/hr_mcp/       MCP server ระบบ HR จำลอง: leave_balance
backend/app/
  agent.py                agent ตัวเดียวจาก workshop 1 (ทำงานได้แล้ว)
  registry.py             CitationRegistry (ทำไว้ให้แล้ว)
  events.py               EventBus → SSE (ทำไว้ให้แล้ว)
  research.py             Step 1
  tools.py                Step 2
  memory.py               Step 3
  agents/                 Step 4: planner.py, orchestrator.py, docs_writer.py
backend/scripts/          script ทดสอบ (รันด้วย docker compose exec backend python scripts/...)
frontend/                 Next.js + react-pdf + Activity panel + Document view (ทำไว้ให้แล้ว)
```

## เพิ่ม PDF ของตัวเอง

วางไฟล์ใน `data/pdfs/` แล้วรัน ingest ใหม่ ชื่อไฟล์ต้องเป็นภาษาอังกฤษ ตัวเลข `-` หรือ `_` เท่านั้น
(ไม่งั้นคลิก citation แล้วเปิดไม่ได้) ไฟล์สแกนที่ไม่มี text layer ต้อง OCR ก่อน
และอย่าใช้เอกสารลับ เพราะเนื้อหาจะถูกส่งไปที่ embedding และ LLM server ของ workshop

PDF ตัวอย่างใน workshop นี้สร้างจาก `data/sources/*.html` ด้วย
`soffice --headless --convert-to pdf --outdir data/pdfs data/sources/<ไฟล์>.html`
