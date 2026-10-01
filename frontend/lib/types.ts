// ต้องตรงกับ contract/chat-response.json และ contract/document-response.json — ห้ามเปลี่ยน shape
export type Citation = {
  id: number;
  doc_id: string;
  filename: string;
  page: number; // 1-based
  quote: string;
};

// ---------- event ใหม่ของ workshop 2 (ดู AGENTS.md) ----------

export type PlanTask = { id: string; agent: "research" | "docs" | string; title: string };

export type ActivityKind = "thinking" | "tool_call" | "tool_result" | "note" | "error";

export type Activity = { agent: string; task_id: string; kind: ActivityKind | string; message: string };

export type Progress = { done: number; total: number; current_task: string };

export type DocumentPayload = { title: string; markdown: string };

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  status: "streaming" | "done" | "error";
  error?: string;
  plan?: PlanTask[];
  activities?: Activity[];
  progress?: Progress;
  document?: DocumentPayload;
};

// citation ที่ถูกเปิดอยู่ใน viewer (nonce ทำให้คลิกซ้ำแล้ว scroll ใหม่ได้)
export type ActiveCitation = Citation & { nonce: number };
