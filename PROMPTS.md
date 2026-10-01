# Prompt สำหรับ vibe code · Workshop 2

ใช้กับ AI coding tool ตัวไหนก็ได้ (Antigravity, Claude Code, Cursor ฯลฯ) เปิด repo นี้ทั้งโฟลเดอร์ แล้ว copy prompt ของ step นั้นไปวางทั้งก้อน

## ก่อนเริ่ม

- **ทำตามลำดับ step** แต่ละ step ต่อยอดจาก step ก่อน ถ้าตามไม่ทันให้ checkout `solution-w2-step-n` ของ step ก่อนหน้า
- **อ่าน diff ทุกครั้ง** ไฟล์ที่ควรถูกแก้มีแค่ที่ prompt ระบุ ถ้า AI จะแก้ `registry.py`, `events.py`, `mcp_servers/` หรือ `frontend/` ให้ปฏิเสธ
- **ทุกอย่างรันผ่าน Docker** ถ้า AI บอกให้ `pip install` หรือรันบนเครื่องให้ปฏิเสธ (ดู `AGENTS.md`)
- **เสร็จหรือยังให้ดูจากผลทดสอบ** ใช้คำสั่งทดสอบท้าย prompt ไม่ใช่เชื่อเพราะ AI บอกว่าเสร็จ
- ต้องตั้ง `LLM_MODEL` และ `EMBED_MODEL` ใน `.env` และ ingest แล้ว (`docker compose run --rm backend python ingest.py`)

## เตรียม: ให้ AI อ่าน repo ก่อน

```text
อ่าน AGENTS.md, backend/app/registry.py, backend/app/events.py, backend/app/agent.py และ contract/document-response.json
แล้วสรุปให้ฟังสั้น ๆ ว่า
1. research note, plan และ SSE event ใหม่มีหน้าตาอย่างไร
2. ทำไมทุก agent ต้องขอเลข [n] จาก CitationRegistry แทนการนับเอง
3. แต่ละ step แก้ไฟล์ไหนได้บ้าง
ยังไม่ต้องเขียนโค้ด
```

---

## Workshop 2 · Step 1 · Agentic RAG

```text
อ่าน AGENTS.md, backend/app/registry.py, backend/app/retrieval.py, backend/app/config.py และ backend/app/agent.py ก่อน แล้วทำงานนี้ให้เสร็จโดยไม่ต้องถามกลับ

งาน: เขียน backend/app/research.py เป็น Research agent แบบ agentic RAG ที่รับ task แล้วคืน research note

ข้อกำหนด
1. แก้/สร้างได้เฉพาะ backend/app/research.py และ backend/scripts/try_research.py
2. ฟังก์ชันหลัก: async def run_research(task: dict, registry: CitationRegistry, bus=None) -> dict
   task มี "id" และ "question" ถ้า bus ไม่ใช่ None ยังไม่ต้องส่ง event (Step 5 จะทำ)
3. ใช้ AsyncOpenAI ชี้ settings.llm_base_url / llm_api_key / llm_model ทุก LLM call ที่ต้องการ JSON ให้ใช้
   response_format={"type":"json_schema","json_schema":{"name": <ชื่อ>, "schema": <schema>}} แล้ว json.loads ผลลัพธ์
   ถ้า parse ไม่ได้ให้ลองใหม่อีก 1 ครั้ง ถ้ายังไม่ได้ให้ใช้ค่า fallback ตามข้อด้านล่าง
4. loop ไม่เกิน MAX_ROUNDS = 3 รอบ แต่ละรอบ:
   a. สร้าง query: LLM รับคำถาม task + สรุปสิ่งที่ค้นเจอแล้ว + ประเด็นที่ยังขาด แล้วคืน {"queries": [1–3 ข้อความ]}
      แตกคำถามหลายส่วนเป็นคำถามย่อย และใช้คำที่น่าจะอยู่ในเอกสาร (fallback: [task["question"]])
   b. ค้นทุก query ด้วย await asyncio.to_thread(search, q, 5) ตัด chunk ซ้ำ (doc_id, page, text เดียวกัน) และข้าม chunk ที่คัดไว้แล้วในรอบก่อน
   c. คัด chunk ใน LLM call เดียว: ส่ง chunk ใหม่แบบมีเลขลำดับ คืน {"relevant": [ลำดับ], "enough": bool, "missing": [ประเด็นที่ยังขาด]}
      (fallback: ถือว่าทุก chunk relevant และ enough=true)
   d. chunk ที่ relevant ให้ registry.register(chunk) แล้วเก็บ id
   e. ถ้า enough เป็นจริง ให้ออกจาก loop
5. เขียน note ด้วย LLM อีกหนึ่ง call ให้ส่ง chunk ที่คัดแล้วในรูป "[<registry id>] (<filename> หน้า <page>)\n<text>"
   คืนตาม schema {"findings":[{"text":str,"citations":[int]}], "gaps":[str]}
   กฎใน prompt: ใช้ข้อมูลจาก chunk เท่านั้น แต่ละ finding ต้องอ้าง id ที่ให้ไปอย่างน้อยหนึ่งตัว สิ่งที่ถามแต่ไม่พบให้ใส่ใน gaps ตอบเป็นภาษาไทย
6. ทำความสะอาดก่อนคืน: ตัด citation id ที่ไม่ได้มาจาก task นี้ ตัด finding ที่ไม่เหลือ citation
   ถ้าไม่มี chunk ที่ relevant เลย ให้ findings=[] และ gaps=[task["question"]]
7. คืน {"task_id": task["id"], "findings": [...], "data": [], "gaps": [...]}
8. backend/scripts/try_research.py: รับคำถามจาก argv สร้าง CitationRegistry() เรียก run_research({"id":"t1","question":...}, registry)
   แล้วพิมพ์ note เป็น JSON ภาษาไทยอ่านได้ (ensure_ascii=False, indent=2) ตามด้วย registry.get(id) ของทุก id ที่ใช้

ทดสอบ (รันเองทั้งหมด ถ้าไม่ผ่านให้แก้จนผ่าน)
- docker compose exec backend python scripts/try_research.py "ลาพักผ่อนกี่วัน และลาป่วยกี่วันต้องมีใบแพทย์"
  ต้องมี findings ครอบคลุมทั้งเรื่องลาพักผ่อนและลาป่วย และทุก citation id อยู่ใน registry
- docker compose exec backend python scripts/try_research.py "ลาคลอดได้กี่วัน"
  findings ต้องว่าง และมี gaps
- docker compose exec backend python -m py_compile app/research.py

เสร็จแล้วสรุป: ไฟล์ที่สร้าง จำนวนรอบที่ใช้ในแต่ละคำถามทดสอบ และ note ที่ได้แบบย่อ
```

---

## Workshop 2 · Step 2 · MCP client

```text
อ่าน AGENTS.md, backend/app/research.py, backend/app/config.py, docker-compose.yml และโค้ดใน mcp_servers/ ก่อน แล้วทำงานนี้ให้เสร็จโดยไม่ต้องถามกลับ

งาน: เขียน MCP client ใน backend/app/tools.py แล้วให้ Research agent ค้นเอกสารผ่าน docs-mcp และดึงข้อมูลจาก hr-mcp ได้

ข้อกำหนด
1. แก้/สร้างได้เฉพาะ backend/app/tools.py, backend/app/research.py และ backend/scripts/try_tools.py (mcp==1.30.0 อยู่ใน requirements แล้ว ห้ามอัปเกรดเป็น 2.x)
2. ใช้ MCP Python SDK: ClientSession กับ streamablehttp_client (mcp.client.streamable_http) ต่อ settings.docs_mcp_url และ settings.hr_mcp_url
3. class ToolHub:
   - async connect(): เปิด session ทั้งสอง server ด้วย AsyncExitStack, initialize, list_tools แล้วเก็บ tool ไว้
   - ชื่อ tool ที่เปิดให้ LLM ใช้ prefix ด้วย "docs__" หรือ "hr__" (ใช้ __ เพราะชื่อ function ของ OpenAI ห้ามมีจุด)
   - openai_tools(prefix=None) -> list: แปลงเป็น {"type":"function","function":{"name","description","parameters": inputSchema}} กรองตาม prefix ได้
   - async call(name, arguments) -> Any: ตัด prefix แล้วเรียก call_tool บน server ที่ถูกต้อง timeout 20 วินาที ถ้า result.isError ให้ raise RuntimeError พร้อมข้อความจาก content ไม่งั้นใช้ structuredContent ถ้ามี หรือ json.loads ข้อความใน content[0].text (ถ้า parse ไม่ได้คืนเป็นข้อความ)
   - async close()
   - get_tool_hub(): singleton ที่ connect ครั้งแรกที่ถูกเรียก (ใช้ asyncio.Lock) ถ้าการเรียกล้มเพราะ connection ให้ reconnect หนึ่งครั้ง
4. แก้ research.py:
   - ค้นเอกสารผ่าน await hub.call("docs__search_docs", {"query": q, "k": 5}) แทน search() โดยตรง ผลลัพธ์อยู่ใน key "chunks" และต้อง register ลง registry เหมือนเดิม
   - ในขั้นสร้าง query ของรอบแรก ให้ส่งรายการ tool ของ hr (ชื่อ, คำอธิบาย, parameters) ไปด้วย และขยาย schema เป็น
     {"queries":[...], "tool_calls":[{"name": str, "arguments": object}]} ให้ LLM เลือกเรียก hr tool เฉพาะเมื่อคำถามต้องใช้ข้อมูลระบบ
   - เรียก tool_calls ที่ชื่อขึ้นต้นด้วย "hr__" ผ่าน hub.call แล้วเก็บใน note["data"] เป็น {"source":"hr-mcp","text": <สรุปผลเป็นข้อความไทยสั้น ๆ พร้อมค่าตัวเลข>}
   - ข้อมูลจาก hr ห้ามลง registry และห้ามมี citation
   - ถ้า hr tool ล้ม ให้เพิ่มใน gaps ว่า "ดึงข้อมูลจากระบบ HR ไม่สำเร็จ" แล้วทำงานต่อ
5. backend/scripts/try_tools.py: พิมพ์ชื่อ tool ทั้งหมดจาก openai_tools() แล้วเรียก docs__search_docs("ลาพักผ่อน") กับ hr__leave_balance({"employee_id":"E001"}) และพิมพ์ผล

ทดสอบ (รันเองทั้งหมด ถ้าไม่ผ่านให้แก้จนผ่าน)
- docker compose exec backend python scripts/try_tools.py → ต้องเห็น docs__search_docs, docs__get_page, hr__leave_balance และผลจากทั้งสอง server
- docker compose exec backend python scripts/try_research.py "ลาพักผ่อนได้กี่วัน และพนักงาน E001 เหลือกี่วัน"
  findings ต้องมีเรื่องสิทธิลาพร้อม citation และ data ต้องมีวันลาคงเหลือจาก hr-mcp โดยไม่มี citation
- docker compose exec backend python scripts/try_research.py "ลาพักผ่อนกี่วัน และลาป่วยกี่วันต้องมีใบแพทย์" ยังได้ผลเหมือน Step 1
- docker compose stop hr-mcp แล้วรันคำถามเรื่อง E001 อีกครั้ง ต้องไม่ crash และ gaps มีข้อความว่าดึงข้อมูลไม่สำเร็จ จากนั้น docker compose start hr-mcp

เสร็จแล้วสรุป: ไฟล์ที่แก้ รายชื่อ tool ที่เห็น และผลของการทดสอบทั้ง 4 ข้อ
```

---

## Workshop 2 · Step 3 · Memory

```text
อ่าน AGENTS.md, backend/app/main.py, backend/app/agent.py และ backend/app/config.py ก่อน แล้วทำงานนี้ให้เสร็จโดยไม่ต้องถามกลับ

งาน: เขียน backend/app/memory.py ให้บทสนทนาจำได้ยาวโดย prompt ไม่เกิน budget ด้วย sliding window + running summary แล้วต่อเข้ากับ /chat

ข้อกำหนด
1. แก้/สร้างได้เฉพาะ backend/app/memory.py, backend/app/agent.py, backend/app/main.py และ backend/scripts/try_memory.py
2. count_tokens(text) = ceil(len(text) / 2.5) เป็นค่าประมาณ (เขียน comment บอกว่าเป็นค่าประมาณ)
3. MEMORY_TOKEN_BUDGET อ่านจาก env ค่า default 1500 (ตั้งต่ำเพื่อให้เห็นการ summarize ใน demo)
4. class ConversationMemory:
   - summary: str และ turns: list[{"user": str, "assistant": str}]
   - add_turn(user, assistant): ตัด [n] ทั้งหมดออกจาก assistant ด้วย regex r"\[\d+\]" ก่อนเก็บ (registry เป็นของแต่ละ request เลขเก่าจึงใช้ข้าม turn ไม่ได้)
   - async compact(): ถ้า token รวมของ turns เกิน budget ให้ดึง turn เก่าที่สุดออกจนเหลือไม่เกิน 60% ของ budget แล้วเรียก LLM หนึ่งครั้งเพื่อรวม summary เดิมกับ turn ที่ถูกดึงออกเป็น summary ใหม่ภาษาไทยไม่เกิน 800 ตัวอักษร
     เก็บข้อเท็จจริงเกี่ยวกับผู้ใช้ (ชื่อ แผนก สิ่งที่ขอ) และหัวข้อที่คุยไปแล้ว ห้ามมี [n]
   - build_messages(system_prompt, user_message) -> list: system, ตามด้วย {"role":"system","content":"สรุปบทสนทนาก่อนหน้า: ..."} ถ้ามี summary, ตามด้วย turns เป็นคู่ user/assistant, ปิดด้วย user_message
   - last_prompt_tokens: จำนวน token ประมาณของ messages ล่าสุดที่ build
5. get_memory(session_id) -> ConversationMemory เก็บใน dict ระดับ process
6. main.py: เพิ่ม session_id: str = "default" ใน ChatRequest ส่งให้ run_agent
7. agent.py: run_agent(message, history, session_id="default") สร้าง messages ด้วย memory.build_messages แทนการใช้ history จาก frontend
   หลังส่ง done แล้วให้ memory.add_turn(message, คำตอบเต็ม) แล้ว await memory.compact()
8. backend/scripts/try_memory.py: ใช้ session ใหม่ ส่ง 10 turn เข้า run_agent ตามลำดับ (อ่านผลจาก SSE string ที่ yield ออกมา)
   turn 1: "สวัสดี ผมชื่อสมชาย อยู่แผนกบัญชี" แล้วถามเรื่องลาพักผ่อน ลาป่วย ขั้นตอนขอลา สลับกันไปจนถึง turn 9
   turn 10: "ผมชื่ออะไร และอยู่แผนกไหน"
   พิมพ์ last_prompt_tokens ของแต่ละ turn, ความยาว summary และคำตอบของ turn 10

ทดสอบ (รันเองทั้งหมด ถ้าไม่ผ่านให้แก้จนผ่าน)
- docker compose exec backend python scripts/try_memory.py
  last_prompt_tokens ทุก turn ต้องไม่เกิน budget + ขนาด system prompt + ข้อความล่าสุด, summary ต้องไม่ว่างภายใน turn 10 และคำตอบ turn 10 ต้องมี "สมชาย" และ "บัญชี"
- summary และ turns ที่เก็บต้องไม่มี [n]
- curl คำถามเดิมจาก workshop 1 ผ่าน /chat ยังได้ token, citations, done ครบ

เสร็จแล้วสรุป: ไฟล์ที่แก้ ตาราง prompt tokens ต่อ turn และคำตอบของ turn 10
```

---

## Workshop 2 · Step 4 · Multi-agent

```text
อ่าน AGENTS.md, backend/app/research.py, backend/app/tools.py, backend/app/memory.py, backend/app/registry.py, backend/app/events.py, backend/app/main.py และโฟลเดอร์ backend/app/agents/ ก่อน แล้วทำงานนี้ให้เสร็จโดยไม่ต้องถามกลับ

งาน: สร้าง Planning agent, Docs agent และ Orchestrator แล้วให้ /chat ใช้ Orchestrator

ข้อกำหนด
1. แก้/สร้างได้เฉพาะ backend/app/agents/planner.py, orchestrator.py, docs_writer.py, backend/app/main.py และ backend/scripts/try_orchestrator.py
2. planner.py → async def make_plan(message: str, context: list[dict]) -> dict
   - LLM call ด้วย json_schema ตาม plan: {"goal": str, "tasks":[{"id": str, "agent": "research"|"docs", "question"?: str, "outline"?: [str], "depends_on":[str]}]}
   - กฎใน prompt: คำถามทั่วไปให้มี research task เดียวและไม่มี docs task; คำขอให้สร้างเอกสาร สรุป คู่มือ หรือรายงาน ให้แตก research ตามหัวข้อ (ไม่เกิน 4) แล้วตามด้วย docs task เดียวที่ depends_on ทุก research และมี outline
   - ตรวจหลัง parse: id ไม่ซ้ำ, depends_on อ้าง task ที่มีจริงและไม่วน, รวมไม่เกิน 5 task, research ต้องมี question, docs ต้องมี outline
   - ไม่ผ่านให้ลองใหม่อีก 1 ครั้ง ถ้ายังไม่ผ่านใช้ fallback {"goal": message, "tasks":[{"id":"t1","agent":"research","question": message,"depends_on":[]}]}
3. docs_writer.py
   - async def write_document(goal, outline, notes, registry) -> str: LLM stream=True เขียน markdown ภาษาไทย หัวข้อ ## ตาม outline ใช้เฉพาะ findings และ data ใน notes
     ส่ง findings พร้อม id ให้ LLM อ้างด้วย [id], data จาก hr-mcp เขียนโดยระบุว่ามาจากระบบ HR และห้ามมี [n], gaps เขียนว่า "ไม่พบข้อมูลในเอกสาร" ห้ามเติมความรู้อื่น
   - async def write_answer(question, notes, registry) -> AsyncIterator[str]: stream คำตอบสั้นแบบ chat จาก notes ด้วยกฎการอ้างอิงเดียวกัน yield ทีละชิ้นข้อความ
4. orchestrator.py → async def run(message: str, session_id: str, bus: EventBus)
   - สร้าง CitationRegistry() ใหม่ต่อ request, memory = get_memory(session_id), context = memory.build_messages("", message)[1:-1]
   - plan = await make_plan(message, context) แล้ว await bus.emit("plan", {"tasks":[{"id","agent","title": question หรือ "เขียนเอกสาร"}]})
   - ไม่มี docs task (โหมด chat): run_research task เดียว แล้ว stream write_answer เป็น event token; หลังจบ emit citations = registry.validate(คำตอบเต็ม) แล้ว done
   - มี docs task (โหมดเอกสาร): จัด research เป็นระดับตาม depends_on รัน task ในระดับเดียวกันพร้อมกันด้วย asyncio.gather(..., return_exceptions=True)
     task ที่ล้มให้ได้ note {"task_id", "findings":[], "data":[], "gaps":["ค้นข้อมูลหัวข้อนี้ไม่สำเร็จ"]} แล้วทำงานต่อ
     emit progress {"done","total","current_task"} ทุกครั้งที่ task เริ่มและจบ (total = จำนวน task ทั้งหมด)
     จากนั้น markdown = await write_document(...) แล้ว emit document {"title": plan["goal"], "markdown": markdown}, citations = registry.validate(markdown), done
   - ทุกกรณีจบด้วย memory.add_turn(message, คำตอบหรือ markdown) และ await memory.compact() แล้ว await bus.close()
   - exception ที่หลุดถึงระดับบนสุดให้ emit error {"message": ข้อความสั้น} แล้ว close
5. main.py: เมื่อ MOCK_MODE=false ให้ /chat สร้าง EventBus เริ่ม orchestrator.run เป็น background task (asyncio.create_task) แล้วคืน StreamingResponse(bus.stream(), media_type="text/event-stream") พร้อม header no-cache เดิม คงโหมด mock ไว้ตามเดิม
6. backend/scripts/try_orchestrator.py: รับข้อความจาก argv รัน orchestrator กับ EventBus แล้วพิมพ์ event ทั้งหมดที่ได้จาก bus.stream() ตามลำดับ (ตัด markdown ให้เหลือ 300 ตัวอักษรตอนพิมพ์)

ทดสอบ (รันเองทั้งหมด ถ้าไม่ผ่านให้แก้จนผ่าน)
- docker compose exec backend python scripts/try_orchestrator.py "สรุปสิทธิการลาทั้งหมดเป็นเอกสารสำหรับพนักงานใหม่"
  ต้องเห็น plan ที่มี research หลายตัวและ docs หนึ่งตัว, progress ไปถึง done == total, document ที่มีหัวข้อครบตาม outline และ citations ที่ทุก id อยู่ใน registry
- docker compose exec backend python scripts/try_orchestrator.py "ลาพักผ่อนได้ปีละกี่วัน"
  ต้องเป็นโหมด chat: มี token, citations, done และไม่มี document
- chunk ที่ research สองตัวเจอซ้ำต้องได้ id เดียวกัน (ตรวจจาก citations ของเอกสารว่าไม่มี doc_id+page+quote ซ้ำด้วย id ต่างกัน)
- curl -N -X POST localhost:8000/chat -H "Content-Type: application/json" -d '{"message":"สรุปสิทธิการลาทั้งหมดเป็นเอกสารสำหรับพนักงานใหม่","session_id":"test"}' ได้ event ครบเหมือนข้อแรก

เสร็จแล้วสรุป: ไฟล์ที่แก้/สร้าง, plan ที่ได้, จำนวน citation ในเอกสาร และเวลาที่ใช้ของแต่ละคำขอ
```

---

## Workshop 2 · Step 5 · Activity & progress

```text
อ่าน AGENTS.md, backend/app/events.py, backend/app/research.py, backend/app/tools.py, backend/app/agents/orchestrator.py และ frontend/components/ActivityPanel.tsx ก่อน แล้วทำงานนี้ให้เสร็จโดยไม่ต้องถามกลับ

งาน: ให้ทุก agent ส่ง activity ที่คนอ่านรู้เรื่อง เพื่อให้ Activity panel แสดงความคืบหน้าแยกตาม task

ข้อกำหนด
1. แก้ได้เฉพาะ backend/app/research.py, backend/app/tools.py, backend/app/agents/orchestrator.py, backend/app/agents/docs_writer.py และ backend/app/events.py ห้ามแก้ frontend
2. ส่งต่อ bus และ task_id ไปถึงทุกฟังก์ชันที่ต้องส่ง event (research, tools, docs_writer) ทุก event ต้องมี task_id
3. activity ที่ต้องมี (message เป็นภาษาไทยสั้น ไม่เกิน 120 ตัวอักษร ห้ามใส่ prompt, JSON ดิบ หรือข้อความจาก chunk):
   - research เริ่ม: kind "thinking" เช่น "เริ่มค้นหัวข้อ: สิทธิลาพักผ่อน"
   - ก่อนค้นเอกสาร: kind "tool_call" เช่น "ค้นเอกสาร: ลาพักผ่อน สะสมวันลา"
   - หลังคัด chunk: kind "tool_result" เช่น "เจอ 6 ส่วน ใช้ 2 ส่วน (รอบที่ 1)"
   - เรียก hr tool: kind "tool_call" เช่น "ดึงวันลาคงเหลือจากระบบ HR" และผลเป็น "tool_result"
   - research จบ: kind "note" เช่น "ได้ข้อมูล 3 ข้อ ขาด 1 ประเด็น"
   - task ล้ม: kind "error" บอกว่าอะไรล้มและผลกระทบ เช่น "ติดต่อระบบ HR ไม่ได้ เอกสารจะระบุว่าข้อมูลส่วนนี้ขาด"
   - planner: agent "planner" task_id "plan" บอกจำนวนหัวข้อที่แตกได้
   - docs writer: agent "docs" kind "thinking" ตอนเริ่มเขียน และ "note" ตอนเขียนเสร็จพร้อมจำนวนหัวข้อ
4. progress: ตรวจว่า orchestrator ส่งทุกครั้งที่ task เริ่มและจบ current_task เป็นชื่อหัวข้อ ไม่ใช่ id
5. events.py: ถ้า stream() ยังไม่มี keepalive ให้ส่ง ": ping\n\n" ทุก 15 วินาทีที่ไม่มี event เพื่อกัน proxy ตัด SSE ถ้ามีอยู่แล้วไม่ต้องแก้
6. ห้ามเปลี่ยน shape ของ event หรือชื่อ field จาก contract

ทดสอบ (รันเองทั้งหมด ถ้าไม่ผ่านให้แก้จนผ่าน)
- docker compose exec backend python scripts/try_orchestrator.py "สรุปสิทธิการลาทั้งหมดเป็นเอกสารสำหรับพนักงานใหม่ รวมวันลาคงเหลือของพนักงาน E001"
  ทุก activity ต้องมี task_id, ไม่มี message ใดยาวเกิน 120 ตัวอักษรหรือมี "{" หรือ "role", และต้องเห็น kind ครบ thinking, tool_call, tool_result, note
- docker compose stop hr-mcp แล้วรันคำสั่งเดิมอีกครั้ง ต้องเห็น activity kind "error" ของ task นั้น และยังได้ document กับ done จากนั้น docker compose start hr-mcp
- เปิด http://localhost:3000 ส่งคำขอเดิม แล้วตรวจว่า Activity panel แสดงแต่ละ task และ progress ขึ้นจนครบ (ถ้าตรวจผ่าน browser ไม่ได้ ให้บอกว่าข้ามข้อนี้)

เสร็จแล้วสรุป: ไฟล์ที่แก้ ตัวอย่าง activity 10 บรรทัดแรกจากการทดสอบ และผลของกรณี hr-mcp ล่ม
```
