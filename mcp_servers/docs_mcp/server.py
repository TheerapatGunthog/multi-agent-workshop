"""docs-mcp: MCP server สำหรับค้นเอกสาร — ทำไว้ให้แล้ว (Step 2 code tour)

ย้าย search() จาก workshop 1 มาเป็น MCP tool โดยยังคืน doc_id, filename, page ครบ
citation จึงยังเชื่อถือได้แม้ tool จะอยู่คนละ container กับ agent

Tools:
  search_docs(query, k=5) -> {"chunks": [{doc_id, filename, page, text, score}]}
  get_page(doc_id, page)  -> {doc_id, filename, page, text}
"""
import os
import re
import sys
from pathlib import Path

import pymupdf
from mcp.server.fastmcp import FastMCP
from openai import OpenAI
from qdrant_client import QdrantClient

from textnorm import clean_thai

if os.getenv("IN_DOCKER") != "1":
    sys.exit("[docs-mcp] ต้องรันผ่าน Docker เท่านั้น: docker compose up --build")


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


LLM_BASE_URL = _env("LLM_BASE_URL", "http://host.docker.internal:8001/v1")
EMBED_BASE_URL = _env("EMBED_BASE_URL") or LLM_BASE_URL
EMBED_API_KEY = _env("EMBED_API_KEY") or _env("LLM_API_KEY", "EMPTY")
EMBED_MODEL = _env("EMBED_MODEL")
QDRANT_URL = _env("QDRANT_URL", "http://qdrant:6333")
COLLECTION = _env("QDRANT_COLLECTION", "docs")
PDF_DIR = Path(_env("PDF_DIR", "/data/pdfs"))
DOC_ID = re.compile(r"^[A-Za-z0-9_-]+$")

_embed = OpenAI(base_url=EMBED_BASE_URL, api_key=EMBED_API_KEY)
_qdrant = QdrantClient(url=QDRANT_URL)

mcp = FastMCP(
    "docs-mcp",
    instructions="ค้นหาข้อความจากเอกสาร PDF ขององค์กร ผลลัพธ์มีชื่อไฟล์และเลขหน้าสำหรับอ้างอิง",
    host="0.0.0.0",
    port=int(os.getenv("PORT", "8000")),
)


@mcp.tool()
def search_docs(query: str, k: int = 5) -> dict:
    """ค้นหาข้อความที่เกี่ยวข้องจากเอกสาร PDF ขององค์กร (ระเบียบ คู่มือ สวัสดิการ) ใช้เมื่อคำถามต้องการข้อมูลจากเอกสาร
    คืน chunks ที่มี doc_id, filename, page (1-based), text และ score"""
    if not EMBED_MODEL:
        raise RuntimeError("ยังไม่ได้ตั้ง EMBED_MODEL ใน .env")
    vector = _embed.embeddings.create(model=EMBED_MODEL, input=[query]).data[0].embedding
    hits = _qdrant.query_points(
        collection_name=COLLECTION, query=vector, limit=max(1, min(k, 20)), with_payload=True
    ).points
    return {
        "chunks": [
            {
                "doc_id": h.payload["doc_id"],
                "filename": h.payload["filename"],
                "page": int(h.payload["page"]),
                "text": h.payload["text"],
                "score": float(h.score),
            }
            for h in hits
        ]
    }


@mcp.tool()
def get_page(doc_id: str, page: int) -> dict:
    """อ่านข้อความทั้งหน้าจากเอกสาร ใช้เมื่อต้องการบริบทรอบข้างของ chunk ที่ค้นเจอ (page เริ่มที่ 1)"""
    if not DOC_ID.match(doc_id):
        raise ValueError("doc_id ไม่ถูกต้อง")
    path = PDF_DIR / f"{doc_id}.pdf"
    if not path.is_file():
        raise ValueError(f"ไม่พบเอกสาร {doc_id}")
    with pymupdf.open(path) as doc:
        if not 1 <= page <= doc.page_count:
            raise ValueError(f"{doc_id} มี {doc.page_count} หน้า")
        text = " ".join(clean_thai(doc[page - 1].get_text()).split())
    return {"doc_id": doc_id, "filename": path.name, "page": page, "text": text}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
