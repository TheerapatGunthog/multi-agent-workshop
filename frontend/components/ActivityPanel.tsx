"use client";

import { useEffect, useState } from "react";
import type { Activity, Message, PlanTask } from "@/lib/types";

// ทำไว้ให้แล้ว (Step 5 code tour): แสดง plan + progress + timeline ของ activity แยกตาม task_id

type TaskStatus = "waiting" | "running" | "done" | "failed";

const STATUS_LABEL: Record<TaskStatus, string> = {
  waiting: "รอ",
  running: "กำลังทำ",
  done: "เสร็จ",
  failed: "ไม่สำเร็จ",
};

const KIND_LABEL: Record<string, string> = {
  thinking: "เริ่ม",
  tool_call: "เรียก tool",
  tool_result: "ผลลัพธ์",
  note: "สรุป",
  error: "ผิดพลาด",
};

function statusOf(task: PlanTask, items: Activity[], message: Message): TaskStatus {
  if (items.some((a) => a.kind === "error")) return "failed";
  if (task.agent === "docs" && message.document) return "done";
  if (items.some((a) => a.kind === "note")) return "done";
  if (items.length > 0) return "running";
  return message.status === "streaming" ? "waiting" : "done";
}

export default function ActivityPanel({ message }: { message: Message }) {
  const streaming = message.status === "streaming";
  const [open, setOpen] = useState(true);

  // พับเก็บเองเมื่อทำงานเสร็จ ผู้ใช้กดเปิดดูย้อนหลังได้
  useEffect(() => {
    if (!streaming) setOpen(false);
  }, [streaming]);

  const activities = message.activities ?? [];
  const plan = message.plan ?? [];
  if (plan.length === 0 && activities.length === 0) return null;

  const byTask = new Map<string, Activity[]>();
  for (const a of activities) byTask.set(a.task_id, [...(byTask.get(a.task_id) ?? []), a]);

  // task ที่อยู่ใน plan ก่อน แล้วตามด้วย task อื่นที่มี activity (เช่น "plan" ของ planner)
  const planIds = new Set(plan.map((t) => t.id));
  const extra = [...byTask.keys()].filter((id) => !planIds.has(id));
  const tasks: PlanTask[] = [
    ...extra.map((id) => ({ id, agent: byTask.get(id)?.[0]?.agent ?? "", title: id === "plan" ? "วางแผนงาน" : id })),
    ...plan,
  ];

  const progress = message.progress;
  const total = progress?.total ?? plan.length;
  const done = progress?.done ?? 0;
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;
  const failed = tasks.filter((t) => statusOf(t, byTask.get(t.id) ?? [], message) === "failed").length;

  return (
    <section className={`activity${streaming ? " activity-live" : ""}`} aria-label="ความคืบหน้าของ agent">
      <button className="activity-head" onClick={() => setOpen((v) => !v)} aria-expanded={open}>
        <span className="activity-title">
          {streaming ? (progress?.current_task ? `กำลังทำ: ${progress.current_task}` : "กำลังวางแผน") : "ขั้นตอนที่ agent ทำ"}
        </span>
        <span className="activity-count">
          {done}/{total}
          {failed > 0 && <span className="activity-failed"> · ไม่สำเร็จ {failed}</span>}
        </span>
      </button>
      {total > 0 && (
        <div className="progress" role="progressbar" aria-valuemin={0} aria-valuemax={total} aria-valuenow={done}>
          <i style={{ width: `${pct}%` }} />
        </div>
      )}
      {open && (
        <ol className="tasks">
          {tasks.map((task) => {
            const items = byTask.get(task.id) ?? [];
            const status = statusOf(task, items, message);
            return (
              <li key={task.id} className={`task task-${status}`}>
                <div className="task-head">
                  <span className="task-name">{task.title}</span>
                  <span className={`task-status status-${status}`}>{STATUS_LABEL[status]}</span>
                </div>
                {items.length > 0 && (
                  <ul className="task-log">
                    {items.map((a, i) => (
                      <li key={i} className={`log log-${a.kind}`}>
                        <span className="log-kind">{KIND_LABEL[a.kind] ?? a.kind}</span>
                        <span className="log-msg">{a.message}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}
