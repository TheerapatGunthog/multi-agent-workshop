"use client";

import { Fragment, type ReactNode } from "react";
import { citationMap, parseAnswer } from "@/lib/citations";
import type { Citation, DocumentPayload } from "@/lib/types";

// ทำไว้ให้แล้ว: render markdown แบบพื้นฐาน (หัวข้อ ย่อหน้า bullet ตัวหนา) และแปลง [n] เป็นปุ่ม citation
// [n] ที่ไม่มีใน citations (ถูก validate ตัดทิ้ง) จะไม่แสดง เหมือน Answer.tsx

type Props = {
  doc: DocumentPayload;
  citations: Citation[];
  streaming: boolean;
  activeId: string | null;
  onOpenCitation: (c: Citation) => void;
};

type Block =
  | { kind: "h"; level: number; text: string }
  | { kind: "p"; text: string }
  | { kind: "ul" | "ol"; items: string[] };

function parseBlocks(markdown: string): Block[] {
  const blocks: Block[] = [];
  let para: string[] = [];
  const flush = () => {
    if (para.length) blocks.push({ kind: "p", text: para.join(" ") });
    para = [];
  };
  for (const raw of markdown.replace(/\r\n/g, "\n").split("\n")) {
    const line = raw.trim();
    const heading = line.match(/^(#{1,4})\s+(.*)$/);
    const bullet = line.match(/^[-*]\s+(.*)$/);
    const numbered = line.match(/^\d+[.)]\s+(.*)$/);
    if (!line) flush();
    else if (heading) {
      flush();
      blocks.push({ kind: "h", level: heading[1].length, text: heading[2] });
    } else if (bullet || numbered) {
      flush();
      const kind = bullet ? "ul" : "ol";
      const text = (bullet ?? numbered)![1];
      const prev = blocks[blocks.length - 1];
      if (prev && prev.kind === kind) prev.items.push(text);
      else blocks.push({ kind, items: [text] });
    } else para.push(line);
  }
  flush();
  return blocks;
}

export default function DocumentView({ doc, citations, streaming, activeId, onOpenCitation }: Props) {
  const map = citationMap(citations);

  const inline = (text: string): ReactNode =>
    text.split(/(\*\*[^*]+\*\*)/g).map((piece, i) => {
      const bold = piece.startsWith("**") && piece.endsWith("**") && piece.length > 4;
      const body = bold ? piece.slice(2, -2) : piece;
      const nodes = parseAnswer(body).map((part, j) => {
        if (part.kind === "text") return <Fragment key={j}>{part.text}</Fragment>;
        const c = map.get(part.id);
        if (c) {
          const active = activeId === `${c.doc_id}:${c.id}`;
          return (
            <button
              key={j}
              className={`cite${active ? " cite-active" : ""}`}
              onClick={() => onOpenCitation(c)}
              title={`${c.filename} หน้า ${c.page}`}
              aria-label={`เปิดแหล่งอ้างอิง ${c.id}: ${c.filename} หน้า ${c.page}`}
            >
              {c.id}
            </button>
          );
        }
        return streaming ? (
          <span key={j} className="cite-pending">
            {part.raw}
          </span>
        ) : null;
      });
      return bold ? <strong key={i}>{nodes}</strong> : <Fragment key={i}>{nodes}</Fragment>;
    });

  return (
    <article className="doc" aria-label={doc.title}>
      <h2 className="doc-title">{doc.title}</h2>
      {parseBlocks(doc.markdown).map((b, i) => {
        if (b.kind === "h") {
          // # ในเอกสารถือเป็นระดับรองจากชื่อเอกสาร
          const Tag = (b.level <= 2 ? "h3" : "h4") as "h3" | "h4";
          return (
            <Tag key={i} className="doc-h">
              {inline(b.text)}
            </Tag>
          );
        }
        if (b.kind === "p") return <p key={i}>{inline(b.text)}</p>;
        const List = b.kind;
        return (
          <List key={i}>
            {b.items.map((item, j) => (
              <li key={j}>{inline(item)}</li>
            ))}
          </List>
        );
      })}
    </article>
  );
}
