# Prompt สำหรับ Workshop 2

ทำตามลำดับ Step 1–5 โดยคัดลอกข้อความในกรอบของแต่ละขั้นไปสั่งงานทั้งก้อน งานแต่ละขั้นต้องทดสอบจริงก่อนถือว่าเสร็จ Prompt ช่วยลดรอบแก้ไข แต่ผลลัพธ์ยังขึ้นกับ LLM server, model และข้อมูลที่ ingest ไว้

## ก่อนเริ่ม

- เปิดทั้งโฟลเดอร์โปรเจกต์ อ่าน `AGENTS.md` และตรวจ diff ก่อน/หลังแก้ทุกครั้ง
- รันระบบและทดสอบผ่าน Docker เท่านั้น ห้ามติดตั้งหรือรัน Python/Node บน host
- เริ่มด้วย `docker compose ps` และ `docker compose exec backend python scripts/check_mcp.py` ถ้า Docker socket แจ้ง permission denied ต้องแก้สิทธิ์ของเซสชันก่อน ไม่ใช่แก้โค้ดเพื่อข้าม sandbox
- ต้องตั้ง `LLM_MODEL`, `EMBED_MODEL` และค่า endpoint/API key ใน `.env` แล้ว ingest PDF ด้วย `docker compose run --rm backend python ingest.py`
- ทดสอบ `/chat` กับระบบจริงต้องใช้ `MOCK_MODE=false` หากเปลี่ยน `.env` ให้ recreate backend ด้วย `docker compose up -d --build backend`
- LLM server ที่ใช้ใน workshop ไม่รองรับ JSON Schema keyword `uniqueItems` และจะตอบ HTTP 400: `Grammar error: Unimplemented keys: ["uniqueItems"]` อย่าใส่ keyword นี้ใน request; ตรวจค่าซ้ำใน Python แทน ยังคงใช้ `response_format` แบบ `json_schema`
- Chat template ของ model นี้รับ system message เพียงข้อความเดียวที่ต้น messages หาก memory มี system summary แยกอีกข้อความ ให้รวมเฉพาะก่อนเรียก API ไม่เปลี่ยน contract ของ build_messages มิฉะนั้นจะได้ HTTP 400: `System message must be at the beginning.`
- สำหรับ server Qwen ที่รองรับ `chat_template_kwargs` ตั้ง `LLM_ENABLE_THINKING=false` ใน `.env` เพื่อลดเวลารอในการ demo แล้ว recreate backend ตัวเลือกนี้ถูกอ่านผ่าน `settings.llm_request_options`; ทุก LLM call ต้องส่ง `**settings.llm_request_options` ด้วย หากเปลี่ยนไปใช้ provider ที่ไม่รองรับให้ลบ env ตัวนี้ เพื่อไม่ส่ง field เฉพาะ provider
- ถ้า LLM ตอบ 400 ให้ดู `docker compose logs --tail=100 --no-log-prefix backend` แยก error จากการรับ schema ออกจาก JSON ที่ model สร้างไม่ถูกต้อง อย่าเปลี่ยนไปใช้ `json_object` หรือซ่อน error ด้วย fallback จนดูเหมือนทดสอบผ่าน
- ทดสอบกับ model จริงก่อนสรุปผล การ compile หรือ mock test อย่างเดียวไม่ยืนยันว่าระบบทำงานครบ
- Step 1–2 เพิ่มความสามารถให้ Research agent เท่านั้น `/chat` ยังใช้ agent เดิมจนถึง Step 4 จึงต้องทดสอบสองขั้นแรกผ่านสคริปต์
- ห้ามเผยแพร่ `.env`, API key, raw prompt หรือ chunk ใน activity/UI
- งานที่ต้องหยุด HR ต้อง start กลับใน `finally` หรือ shell trap แม้ assertion ล้ม และต้องรอให้ server ตอบได้ก่อนทดสอบถัดไป

## สำรวจโปรเจกต์

```text
อ่าน AGENTS.md, backend/app/registry.py, backend/app/events.py, backend/app/agent.py และ contract/document-response.json
สรุป contract ของ citation, research note, plan และ SSE; อธิบายการใช้ CitationRegistry ร่วมกันต่อ request และระบุไฟล์ที่แก้ได้ในแต่ละขั้น ยังไม่แก้โค้ด
```

ถ้าเริ่มจาก solution tag เก่าที่ไม่มี `settings.llm_request_options` ให้เพิ่มตัวเลือกนี้ใน `backend/app/config.py` ก่อน: อ่าน `LLM_ENABLE_THINKING` จาก env; เมื่อว่างคืน `{}` เมื่อระบุให้คืน `{"extra_body":{"chat_template_kwargs":{"enable_thinking":bool}}}` โดยแปลง `false/0/no` เป็น false และเพิ่มคำอธิบายใน `.env.example` การเปลี่ยนนี้เป็นขั้นเตรียม ไม่ต้องเพิ่ม SDK หรือเปลี่ยนชื่อ model

## Step 1 · Agentic RAG

```text
อ่าน AGENTS.md, backend/app/registry.py, backend/app/retrieval.py, backend/app/config.py และ backend/app/agent.py ก่อน แล้วทำงานให้เสร็จโดยไม่ต้องถามกลับ

งาน: สร้าง Research agent และสคริปต์ทดสอบ แก้ได้เฉพาะ backend/app/research.py และ backend/scripts/try_research.py

ข้อกำหนด
1. async def run_research(task: dict, registry: CitationRegistry, bus=None) -> dict โดย task มี id, question; bus ยังไม่ต้องส่ง event
2. ใช้ AsyncOpenAI จาก settings.llm_base_url, llm_api_key, llm_model ห้าม hard-code model/URL
   ส่ง **settings.llm_request_options ทุก call เพื่อเคารพตัวเลือก thinking จาก env
3. ทุก call ที่คืน JSON ใช้ response_format={"type":"json_schema","json_schema":{"name":ชื่อ,"schema":schema}} และ json.loads; ตรวจชนิด/field ด้วย Python ด้วย ห้ามใช้ uniqueItems ใน schema เพราะ grammar server ไม่รองรับ
   JSON หรือ schema ของผลตอบกลับผิดให้ลองใหม่หนึ่งครั้งแล้วใช้ fallback; API connection/HTTP error ต้องรายงานแยก ไม่อ้างว่าค้นไม่พบเอกสาร
4. MAX_ROUNDS=3 แต่ละรอบ:
   a. ให้ LLM รับ question, สรุปสิ่งที่พบ และประเด็นที่ขาด คืน {"queries":[ข้อความ 1–3 ข้อ]}; แยกคำถามหลายส่วนและเลือกคำที่น่าจะอยู่ในเอกสาร fallback เป็น [task["question"]]
   b. ค้นทุก query ด้วย await asyncio.to_thread(search, q, 5)
   c. ตัด chunk ซ้ำด้วย (doc_id,page,text) และข้าม chunk ที่เลือกไว้แล้วในรอบก่อน
   d. คัด chunk ใหม่ใน LLM call เดียว ส่งเลขลำดับเริ่ม 1 คืน {"relevant":[ลำดับ],"enough":bool,"missing":[str]}; fallback เลือกทั้งหมดและ enough=true
   e. ตรวจ index ว่าเป็น int จริง ไม่ใช่ bool และอยู่ในช่วง; relevant เท่านั้นที่ registry.register(chunk)
   f. หยุดเมื่อ enough=true มิฉะนั้นค้นต่อจนครบสามรอบ
5. เขียน note ด้วย JSON call ส่ง chunk เป็น "[registry_id] (filename หน้า page)\ntext"
   คืน {"findings":[{"text":str,"citations":[int]}],"gaps":[str]}
   ใช้เฉพาะ chunk ตอบไทย ทุก finding ต้องมี id ของ chunk ที่ task นี้เลือกอย่างน้อยหนึ่งตัว สิ่งที่ถามแต่ไม่พบอยู่ใน gaps ห้ามใช้ความรู้ภายนอก
   ถ้า note parse ไม่ได้หลัง retry ให้ findings=[] และ gaps=[question] ไม่คัดทั้ง chunk มาแสร้งเป็นคำตอบ
6. กรอง citation ให้เหลือเฉพาะ id ที่ task นี้เลือก แม้ registry มี id ของ task อื่น; ตัด finding ที่ไม่เหลือ citation
   ไม่มี relevant chunk: findings=[] และ gaps=[question]
7. คืน {"task_id":task["id"],"findings":[...],"data":[],"gaps":[...]}; ห้ามเพิ่ม field จำนวนรอบลง contract ให้บันทึกรอบใน log แทน
8. try_research.py รับ question จาก argv สร้าง registry ใหม่ เรียก task id t1 พิมพ์ JSON ensure_ascii=False, indent=2 และ registry.get(id) ของทุก id ที่อ้าง พร้อม assert ว่า id อยู่ใน registry

ทดสอบจริงผ่าน Docker และแก้จนผ่าน
- docker compose exec backend python scripts/try_research.py "ลาพักผ่อนกี่วัน และลาป่วยกี่วันต้องมีใบแพทย์"
  findings ต้องครอบคลุมสองส่วน พร้อม citation ที่ถูกต้อง
- docker compose exec backend python scripts/try_research.py "ลาคลอดได้กี่วัน"
  findings=[] และ gaps ไม่ว่าง ห้ามนำข้อมูลลาป่วยมาตอบแทน
- docker compose exec backend python -m py_compile app/research.py scripts/try_research.py
- เพิ่มการตรวจแบบจำลองสำหรับ JSON เสียสองครั้ง, index หลุดช่วง, chunk ซ้ำ, citation จาก task อื่น และการหยุดไม่เกินสามรอบ โดยไม่เรียกบริการจริงใน unit check

สรุปไฟล์ที่แก้ จำนวนรอบและ note จริงของแต่ละคำถาม ถ้ารันไม่ได้ให้ระบุ blocker ห้ามแต่งผลผ่าน
```

## Step 2 · MCP client

```text
อ่าน AGENTS.md, backend/app/research.py, backend/app/config.py, docker-compose.yml และ mcp_servers/ ก่อน แล้วทำงานให้เสร็จโดยไม่ต้องถามกลับ

งาน: แก้เฉพาะ backend/app/tools.py, backend/app/research.py และ backend/scripts/try_tools.py
ใช้ mcp==1.30.0 เดิม ห้ามเปลี่ยน major version และไม่เพิ่ม agent framework

ข้อกำหนด
1. ToolHub ใช้ ClientSession และ streamablehttp_client จาก mcp.client.streamable_http ต่อ settings.docs_mcp_url / settings.hr_mcp_url
2. connect(): เปิดแต่ละ server ผ่าน AsyncExitStack, initialize, list_tools เก็บชื่อและ inputSchema (รองรับ pagination)
   ห้ามให้ HR ที่ปิดอยู่ทำให้ docs ใช้ไม่ได้ ทั้งกรณีเคยเชื่อมแล้วและกรณี process ใหม่เริ่มขณะ HR ปิด
3. สำคัญ: MCP SDK ใช้ AnyIO cancel scope ต้อง enter/exit context ใน asyncio task เดียวกันตลอดอายุ session
   ใช้ owner task แยกต่อ server กับ queue/future หรือ lifecycle ที่รักษาเงื่อนไขนี้ได้จริง ห้ามเปิด session ใน request หนึ่งแล้วปิดจาก task อื่น
   close() ต้องปิด resource ครบ ไม่มี Task exception was never retrieved หรือ cancel-scope traceback; timeout/cancellation ต้องไม่กลืน CancelledError ของผู้เรียก
4. openai_tools(prefix=None) คืน OpenAI function tools มี name,description,parameters=inputSchema ชื่อ prefix docs__ / hr__ ห้ามมีจุด กรองทั้ง "hr" และ "hr__" ได้
5. call(name,arguments): ตรวจชื่อ ตัด prefix แล้วเรียก server ที่ถูกต้อง timeout 20 วินาทีต่อ tool call
   result.isError ต้อง raise RuntimeError พร้อมข้อความจาก content
   ใช้ structuredContent ถ้าไม่ใช่ None (รวม {}); ไม่เช่นนั้น json.loads(content[0].text), ถ้าไม่ใช่ JSON คืนข้อความ
   Connection error ให้ reconnect server นั้นและ retry หนึ่งครั้ง; tool/business error ไม่ retry; ห้าม reconnect อีก server โดยไม่จำเป็น
6. get_tool_hub(): process singleton พร้อม asyncio.Lock ป้องกัน connect ซ้ำ และต้องปลอดภัยเมื่อ research หลาย task เรียกพร้อมกัน
7. Research ใช้ await hub.call("docs__search_docs", {"query":q,"k":5}) ผลอยู่ใน chunks; การ deduplicate/register และ note contract คงเดิม
8. Query JSON รอบแรกเพิ่ม tool_calls เป็น [{"name":str,"arguments":object}] พร้อมส่งรายชื่อ HR tools, description, parameters ให้ LLM
   เลือกเฉพาะ tool ที่ขึ้นต้น hr__ และอยู่ใน allowlist เมื่อคำถามต้องใช้ข้อมูลรายบุคคล ใช้ employee_id ที่ผู้ใช้ระบุ ห้ามเดา
   เรียกเฉพาะรอบแรกและตัด calls ซ้ำ; fallback tool_calls=[]
9. HR result อยู่ใน data เป็น {"source":"hr-mcp","text":ข้อความไทยสั้นพร้อมค่าตัวเลข} ห้าม register และห้ามมี [n]
   ส่ง system_data ให้ขั้นตรวจความครบถ้วนด้วย หาก HR ตอบแล้วไม่ต้องค้นซ้ำสามรอบหรือเพิ่ม gaps ว่าไม่พบข้อมูลรายบุคคลในเอกสาร; ห้ามนำ data ไปสร้าง findings
   ขั้นเขียน note ต้องรู้ประเด็นที่ system_data ตอบแล้วเช่นกัน เพื่อไม่เขียน gap ซ้ำซ้อน; ใช้ data ตรวจความครบถ้วนเท่านั้น ไม่ใช่หลักฐาน citation
   จัดการทั้ง transport failure, isError, payload ที่มี error และ field ที่ขาด โดยเพิ่ม gaps ว่า "ดึงข้อมูลจากระบบ HR ไม่สำเร็จ" แล้วทำงานต่อ
   เมื่อ HR ปิดตั้งแต่เริ่ม ใช้ metadata ที่ cache ไว้ หรือ descriptor ของ leave_balance ตาม contract เพื่อให้เลือก tool และรายงาน failure ได้ ห้าม hard-code คำตอบ E001
10. try_tools.py พิมพ์ tool ทั้งหมด เรียก docs__search_docs(query="ลาพักผ่อน",k=5), hr__leave_balance(employee_id="E001") พร้อม assert และ close ใน finally

ทดสอบจริง
- docker compose exec backend python scripts/try_tools.py
  ต้องมี docs__search_docs, docs__get_page, hr__leave_balance และผลสอง server
- docker compose exec backend python scripts/try_research.py "ลาพักผ่อนได้กี่วัน และพนักงาน E001 เหลือกี่วัน"
  findings เป็นสิทธิลามี citation, data จาก HR ระบุคงเหลือ 6 วัน ไม่มี citation
- docker compose exec backend python scripts/try_research.py "ลาพักผ่อนกี่วัน และลาป่วยกี่วันต้องมีใบแพทย์"
- หยุด HR ด้วย docker compose stop hr-mcp แล้วทดสอบ E001 ใน process ใหม่ ต้องยังค้นเอกสารและได้ gaps โดยไม่ crash
  ต้อง docker compose start hr-mcp ใน finally/trap เสมอ แล้วตรวจว่า HR กลับมาเรียกได้
- ทดสอบ reconnect หลังเคยเชื่อมแล้ว และ concurrent calls พร้อม py_compile ของไฟล์ที่แก้

สรุป tools ที่ค้นพบ ผลทดสอบทั้งกรณีปกติ/HR ปิด/กู้คืน และย้ำว่า /chat จะต่อ Research agent ใน Step 4
```

## Step 3 · Memory

```text
อ่าน AGENTS.md, backend/app/main.py, backend/app/agent.py และ backend/app/config.py ก่อน แล้วทำงานให้เสร็จโดยไม่ต้องถามกลับ

แก้เฉพาะ backend/app/memory.py, backend/app/agent.py, backend/app/main.py และ backend/scripts/try_memory.py

ข้อกำหนด
1. count_tokens(text)=ceil(len(text)/2.5) พร้อม comment ว่าเป็นค่าประมาณ ไม่ใช่ tokenizer จริง
2. MEMORY_TOKEN_BUDGET อ่าน env default 1500 ต้องเป็นจำนวนบวก; ห้ามแก้ config.py นอก scope ใช้ settings สำหรับ LLM ตามเดิม
3. ConversationMemory มี summary:str, turns:list[{user,assistant}], last_prompt_tokens และ lock ต่อ session
4. add_turn ตัด regex r"\[\d+\]" ก่อนเก็บ assistant และข้อความ user ที่อาจ quote citation เก่า
5. compact(): เมื่อ turns เกิน budget (หรือ summary+turns รวมเกิน) เลือก turn เก่าจนเหลือไม่เกิน 60% budget
   ส่ง **settings.llm_request_options ใน summary call และทุก call ของ agent ด้วย
   เรียก LLM หนึ่งครั้งรวม summary เดิมกับ turn ที่เลือก ให้สรุปไทยไม่เกิน 800 ตัวอักษร เก็บชื่อ แผนก สิ่งที่ขอ และหัวข้อที่คุย ห้ามแต่งข้อมูลหรือมี [n]
   อย่าลบ turns ก่อนมี summary หรือ fallback ที่ปลอดภัย ถ้า LLM ล้มใช้ข้อความย่อจากข้อมูลเดิมและ log โดยไม่ทำให้ SSE ที่ส่ง done แล้วล้ม
   ล้าง citation และ enforce ความยาว summary หลัง LLM ตอบด้วย
6. build_messages(system_prompt,user_message) คืน system, system summary ถ้ามี, คู่ user/assistant ล่าสุดตามลำดับ, user_message
   งบ memory ต้องรวม summary และ prefix "สรุปบทสนทนาก่อนหน้า: " ด้วย เก็บคู่ turn ทั้งคู่ ไม่ตัดเหลือแต่ assistant
   หากยังเกินให้จำกัด window ตอน build ด้วย ไม่ทำลายข้อมูลที่เก็บไว้
   last_prompt_tokens เป็นผลรวม count_tokens ของ content ที่ build จริง ไม่รวม tool results ที่เพิ่มภายหลัง
7. get_memory(session_id) เป็น dict ระดับ process; แต่ละ session แยกกัน รีสตาร์ท process แล้ว memory หายตามธรรมชาติ
8. ChatRequest เพิ่ม session_id="default"; run_agent(message,history,session_id="default") ใช้ memory แทน frontend history โดยคง parameter เพื่อ compatibility
   ล็อกทั้ง request ของ session เดียว หลัง yield done ให้ add_turn ด้วยคำตอบเต็มและ await compact
   ปรับ system prompt ให้ชื่อ/แผนกตอบจาก memory ได้โดยไม่ต้อง citation แต่ข้อมูลนโยบายต้องค้นใหม่ ห้ามใช้ citation ข้าม request
   ก่อนส่ง API รวม leading system prompt กับ system summary เป็น system message เดียวเพื่อรองรับ chat template ของ model นี้ โดย build_messages และ last_prompt_tokens ยังเป็น contract เดิม
9. try_memory.py ใช้ session ใหม่ ส่ง 10 turn ผ่าน run_agent และ parse SSE จริง ต้อง consume generator จนจบ ไม่ break เมื่อเห็น done เพราะ compact ทำหลัง done
   turn 1: "สวัสดี ผมชื่อสมชาย อยู่แผนกบัญชี"
   turn 2–9: ถามลาพักผ่อน ลาป่วย ขั้นตอนขอลา สลับกันพร้อมรายละเอียดตามเอกสาร
   turn 10: "ผมชื่ออะไร และอยู่แผนกไหน"
   พิมพ์ตาราง prompt tokens, budget ที่อนุญาต, summary chars และคำตอบ turn 10 พร้อม assert

ทดสอบ
- docker compose exec backend python scripts/try_memory.py
  ทุก turn <= budget+count_tokens(system_prompt)+count_tokens(คำถามล่าสุด), summary ไม่ว่างภายใน turn 10, <=800 ตัวอักษร และคำตอบสุดท้ายมี สมชาย และ บัญชี
- summary และทุก turn ต้องไม่มี [n]; session ใหม่ต้องว่าง
- ทดสอบ long single turn, summary+turns เต็ม budget และ summarizer ล้ม ด้วย mock
- ทดสอบ /chat ผ่าน HTTP จากใน Docker เมื่อ MOCK_MODE=false ต้องมี token,citations,done
- py_compile ไฟล์ที่แก้; สรุปตารางจริง ห้ามใส่ตัวเลขที่ไม่ได้รัน
```

## Step 4 · Multi-agent

```text
อ่าน AGENTS.md, research.py, tools.py, memory.py, registry.py, events.py, main.py ใน backend/app และ backend/app/agents/ ก่อน แล้วทำงานให้เสร็จโดยไม่ต้องถามกลับ

แก้เฉพาะ backend/app/agents/planner.py, backend/app/agents/orchestrator.py, backend/app/agents/docs_writer.py, backend/app/main.py และ backend/scripts/try_orchestrator.py

Planner
1. async make_plan(message,context)->dict ใช้ AsyncOpenAI จาก settings และ response_format json_schema
   ส่ง **settings.llm_request_options ทั้ง planner และ docs writer เพื่อใช้ตัวเลือกเดียวกันกับ research/memory
   shape: {"goal":str,"tasks":[{"id":str,"agent":"research"|"docs","question"?:str,"outline"?:[str],"depends_on":[str]}]}
   ห้าม uniqueItems ใน schema; ตรวจค่าซ้ำใน Python เพราะ LLM server ของ workshop ไม่รองรับ keyword นี้
2. คำถามทั่วไป: research เดียว ไม่มี docs; ขอเอกสาร สรุป คู่มือ รายงาน: research ตามหัวข้อไม่เกิน 4 แล้ว docs เดียว depends_on ทุก research พร้อม outline ภาษาไทย
   คำขอหลายหัวข้อต้องแตกหลาย research; research question ต้องสมบูรณ์ด้วยตัวเองโดยใช้ context แก้คำอ้างถึง
3. validate หลัง parse: ชนิดถูก, id ไม่ว่างและไม่ซ้ำ, deps ไม่ซ้ำและมีจริง, ไม่มีวงจร, ไม่เกิน 5 task, research มี question, docs มี outline ไม่ว่าง
   คำถาม chat ที่ไม่มี context ใช้ข้อความเดิมเป็น research question ไม่ให้ planner เติมเรื่องกฎหมายหรือเงื่อนไขเอง
   ตรวจรหัสพนักงาน E001 หรือรหัสอื่นที่ระบุใน message ว่าอยู่ใน research question จริง ไม่ใช่อยู่เฉพาะ goal/outline
   ขอเอกสาร "ทั้งหมด" ต้องมีอย่างน้อยสอง research และเมื่อขอ HR ให้แยกหัวข้อนั้นชัดเจน ใช้ temperature=0 สำหรับ structured calls เพื่อลดความแปรปรวน
   research ห้ามขึ้นกับ docs; โหมด chat ต้อง research เดียว; โหมดเอกสารต้อง docs เดียวขึ้นกับทุก research
4. JSON/plan ไม่ผ่านลองใหม่หนึ่งครั้ง แล้วย้อนเป็น {"goal":message,"tasks":[{"id":"t1","agent":"research","question":message,"depends_on":[]}]}
   HTTP/API error ต้องเก็บ traceback ใน backend log และแจ้งประเภทปัญหาอย่างปลอดภัย ห้ามซ่อนโดยอ้างว่าแผนผ่าน

Docs writer
5. async write_document(goal,outline,notes,registry)->str ใช้ LLM stream=True สะสม markdown ไทยทั้งฉบับ หัวข้อ ## ใช้ชื่อและลำดับ outline ครบทุกข้อ
6. async write_answer(question,notes,registry)->AsyncIterator[str] stream คำตอบสั้นทีละชิ้น
7. ใช้เฉพาะ findings/data จาก notes: findings มี [id] ที่อยู่ทั้งใน note และ registry, data HR เขียนว่า "จากระบบ HR" แยกประโยค ไม่มี citation, gaps ระบุ "ไม่พบข้อมูลในเอกสาร" ห้ามเดา
   กรอง id ไม่ถูกต้องก่อนส่ง LLM และห้ามปล่อย citation ที่ไม่มีสิทธิ์อ้างเมื่อ stream รวมถึง citation ที่ถูกตัดข้าม delta
   ไม่มี findings ไม่ได้แปลว่าไม่มีสิทธิ์ ให้บอกว่าไม่พบข้อมูล

Orchestrator และ HTTP
8. async run(message,session_id,bus): registry ใหม่หนึ่งตัวต่อ request แชร์กับทุก research; memory=get_memory(session_id) และล็อก session; context=memory.build_messages("",message)[1:-1]
9. make_plan แล้ว emit plan {tasks:[{id,agent,title}]} title เป็น question หรือ "เขียนเอกสาร"
10. Chat: research เดียว -> write_answer -> token หลายครั้ง -> citations=registry.validate(คำตอบเต็ม) -> done
11. Document: แบ่ง research ตามระดับ dependency รันระดับเดียวกันด้วย asyncio.gather(...,return_exceptions=True)
    งานล้มแทนด้วย {task_id,findings:[],data:[],gaps:["ค้นข้อมูลหัวข้อนี้ไม่สำเร็จ"]} แล้วทำ task ที่เหลือต่อ
    เรียง notes ตาม plan เพื่อให้ผลเสถียร; failed task ถือว่าประมวลผลเสร็จเพื่อไม่ให้ scheduler ค้าง
12. ส่ง progress ตอนเริ่มและจบทุก task รวม docs (แม้ task ล้ม); total รวมทุก task; current_task ใช้ชื่อหัวข้อ ไม่ใช่ id; จำนวน done ต้องไม่ย้อนกลับ
    docs writer เสร็จ -> document {title:goal,markdown} -> citations=registry.validate(markdown) -> done
13. add_turn(message,คำตอบหรือ markdown) และ compact ก่อน close ใน finally; bus ต้องปิดทั้ง success/error/cancellation
    error ระดับบนส่งข้อความไทยสั้นที่แยก connection, timeout, HTTP status ได้โดยไม่ใส่ raw exception/prompt/credential
    done ส่งหนึ่งครั้ง และห้ามหลงเหลือ background task ที่ไม่ถูกดูแล
14. main.py: MOCK_MODE=false สร้าง EventBus แล้ว asyncio.create_task(run(...)) เก็บ strong reference จน task จบ คืน StreamingResponse(bus.stream(),media_type="text/event-stream") พร้อม Cache-Control:no-cache และ X-Accel-Buffering:no
    คง mock mode เดิม, รับ session_id เดิม, ห้ามใช้ frontend history แทน server memory
15. try_orchestrator.py รับ argv รัน background task+bus.stream พิมพ์ event ตามลำดับ ตัดเฉพาะ markdown ที่แสดงไม่เกิน 300 ตัวอักษร แต่ตรวจบน markdown เต็ม
    บันทึก plan เต็มเพื่อเช็ค outline, registry ของ request, เวลาจริง, จำนวน citation; assert รูปแบบ chat/document, progress ครบ, event done ครั้งเดียว, citation id ถูกและไม่ซ้ำ
    สคริปต์ต้องรองรับ activity ที่จะเพิ่ม Step 5 ไม่ยึดว่ามีเฉพาะ event เดิม

ทดสอบจริง
- docker compose exec backend python scripts/try_orchestrator.py "สรุปสิทธิการลาทั้งหมดเป็นเอกสารสำหรับพนักงานใหม่"
  research หลายตัว+docs เดียว, หัวข้อครบ outline, done==total
- docker compose exec backend python scripts/try_orchestrator.py "ลาพักผ่อนได้ปีละกี่วัน"
  มี token,citations,done ไม่มี document ต้องตอบ 10 วันและ citation ไม่ว่าง ห้ามให้ empty citations ผ่านแบบ vacuous assertion
- chunk ซ้ำระหว่าง research ต้องได้ registry id เดียว ตรวจ doc_id+page+quote ไม่ซ้ำต่าง id (ข้อมูลตัวอย่างนี้ไม่มี prefix quote ชนกัน)
- ส่งคำขอเอกสารเดียวกันผ่าน POST /chat session_id=test จาก HTTP client ภายใน Docker (curl ถ้ามี หรือ httpx ที่ติดตั้งแล้ว) ตรวจ SSE เต็มและไม่มี error; ต้อง MOCK_MODE=false
- ทดสอบ invalid/cyclic plans, fallback หลังสองครั้ง, research บางตัวล้ม, writer ล้ม และ shutdown ด้วย mock ไม่ต้องใช้ API
- py_compile และ git diff --check; สรุป plan, citations, เวลา จากการรันจริง
  หากเพิ่ม optional --expect-citations และ --expect-text ให้สคริปต์ได้ ให้ใช้ flags เหล่านี้ตรวจคำตอบ fixture ที่รู้ผลแน่นอน
```

## Step 5 · Activity และ progress

```text
อ่าน AGENTS.md, backend/app/events.py, research.py, tools.py, agents/orchestrator.py, agents/docs_writer.py และ frontend/components/ActivityPanel.tsx ก่อน แล้วทำงานให้เสร็จโดยไม่ต้องถามกลับ

แก้เฉพาะ backend/app/research.py, backend/app/tools.py, backend/app/agents/orchestrator.py, backend/app/agents/docs_writer.py และ backend/app/events.py ห้ามแก้ frontend

ข้อกำหนด
1. ส่ง bus และ task_id ถึง research/tools/docs writer โดยคงการเรียกแบบเดิมที่ไม่มี bus ให้ทำงานได้
   task_id เป็น argument ต่อ call ห้ามเก็บเป็น mutable state บน ToolHub singleton เพราะ task ขนานจะสลับ id กัน
   ทุก activity มี agent,task_id,kind,message ครบ; ห้ามเพิ่ม task_id ลง event อื่นที่ contract ไม่มี field นี้
2. message เป็นไทย <=120 ตัวอักษร ห้ามมี prompt, JSON, chunk, raw exception หรือ credential; ใช้ข้อความคงที่กับตัวเลข ถ้าใส่หัวข้อ/คำค้นต้อง sanitize และจำกัดความยาว
3. research thinking ตอนเริ่ม; tool_call ก่อนค้น; tool_result หลังคัดระบุจำนวนพบ/จำนวนเลือกเฉพาะรอบ/รอบที่เท่าไร; note สรุปจำนวน findings,data,gaps ตอนจบ
4. tools ส่ง HR tool_call และ tool_result; เมื่อ HR ล้มส่ง error ผูก task นั้นพร้อมผลกระทบ แต่ research ยังทำงานต่อและมี HR gap
   จัดการทั้ง HR ปิดตั้งแต่ process เริ่ม, connection หลุด, isError, business error, payload ไม่ครบ ห้ามส่ง success note ให้ task ที่ล้มทั้งก้อน
5. planner agent="planner", task_id="plan" แจ้งจำนวน research ที่แตกได้; ถ้าวางแผนไม่ได้ให้ข้อความแยกชนิด error/HTTP status อย่างปลอดภัยและเก็บ traceback ใน log
6. docs agent="docs" thinking ตอนเริ่ม และ note เมื่อเขียนเสร็จพร้อมจำนวนหัวข้อ; writer ล้มส่ง error ของ docs task ก่อนปิด stream
7. progress ทุกครั้งเริ่ม/จบ research/docs ใช้ชื่อหัวข้อเป็น current_task; done นับงานที่จบรวม failed และต้องถึง total เมื่อยังเขียนเอกสารต่อได้
8. events.stream ถ้ามี keepalive ทุก 15 วินาทีอยู่แล้วไม่ต้องแก้; ถ้ายังไม่มีเพิ่ม ": ping\n\n" เมื่อไม่มี event
   ห้ามเปลี่ยน event shape หรือชื่อ field ใน contract
9. ActivityPanel เดิมจัดกลุ่มตาม task_id และถือว่ามี error แล้ว task failed แม้มีผลบางส่วน ห้ามแก้ frontend เพื่อซ่อน error นี้

ทดสอบจริง (เขียน temporary harness ใน container ได้ ไม่แก้ไฟล์อื่นนอก scope)
- docker compose exec backend python scripts/try_orchestrator.py "สรุปสิทธิการลาทั้งหมดเป็นเอกสารสำหรับพนักงานใหม่ รวมวันลาคงเหลือของพนักงาน E001"
- parse ทุก activity และ assert task_id ไม่ว่าง, message <=120 ตัวอักษร, ไม่มี { หรือ role; ต้องมี thinking,tool_call,tool_result,note; research ids อยู่ใน plan
- docker compose stop hr-mcp แล้วรันคำขอเดิมใน process ใหม่ ต้องมี error ผูก HR task แต่ยังได้ document,citations,done และ progress ครบ
  คืน HR ด้วย docker compose start hr-mcp ใน finally/trap แม้ test ล้ม แล้วทดสอบเรียก HR อีกครั้ง
- เปิด http://localhost:3000 ส่งคำขอเดิม ตรวจ Activity panel แยก task และ progress ครบ; ถ้า browser ถูกปฏิเสธสิทธิ์/ไม่มีเครื่องมือ ให้ระบุว่าข้าม UI แต่ยังทดสอบ HTTP/SSE จริง
- ตรวจ keepalive, error path, task_id isolation ของ parallel research ด้วย mock และ py_compile

สรุปไฟล์ที่แก้, activity 10 บรรทัดแรกจากการรันจริง, ผล HR ล่ม/กู้คืน และผล browser ห้ามแต่ง log หรือบอกว่าผ่านถ้ายังไม่รัน
```

## ตรวจทั้งระบบหลังครบห้าขั้น

โค้ดฉบับนี้มี regression scripts ให้รันซ้ำได้ (โค้ดเริ่มต้นหรือ solution tag เก่าอาจยังไม่มี):

```bash
docker compose exec backend python scripts/check_workshop.py
docker compose exec backend python scripts/try_tools.py
docker compose exec backend python scripts/try_memory.py
docker compose exec backend python scripts/try_orchestrator.py --expect-citations --expect-text 10 "ลาพักผ่อนได้ปีละกี่วัน"
docker compose exec backend python scripts/try_http.py
docker compose exec backend python -m compileall -q app scripts
```

`check_workshop.py` ตรวจ edge cases โดยไม่เรียก LLM; `try_http.py` เรียก `/chat` จริงทั้งเอกสารและแชต และต้อง `MOCK_MODE=false` อย่าใช้ unit test แทน integration test หากแก้โค้ดแล้ว backend ไม่ reload บน bind mount ให้รอคำสั่งที่กำลังทดสอบจบ แล้ว `docker compose restart backend` ก่อนตรวจ HTTP อีกครั้ง
