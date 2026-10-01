"""Citation registry — ทำไว้ให้แล้ว ห้ามแก้ (ดู AGENTS.md)

หนึ่ง request มี registry เดียว ทุก agent ขอเลข [n] จากที่นี่
chunk เดิม (doc_id, page, text) ได้ id เดิมเสมอ จึงไม่มี [1] สองตัวที่ชี้คนละที่
"""
import re
from typing import Any

CITE = re.compile(r"\[(\d+)\]")


def _get(chunk: Any, key: str) -> Any:
    return chunk[key] if isinstance(chunk, dict) else getattr(chunk, key)


class CitationRegistry:
    def __init__(self) -> None:
        self._by_key: dict[tuple[str, int, str], int] = {}
        self._items: dict[int, dict] = {}

    def register(self, chunk: Any) -> int:
        """รับ dict หรือ object ที่มี doc_id, filename, page, text แล้วคืน id (เริ่มที่ 1)"""
        key = (str(_get(chunk, "doc_id")), int(_get(chunk, "page")), str(_get(chunk, "text")))
        if key in self._by_key:
            return self._by_key[key]
        cid = len(self._items) + 1
        self._by_key[key] = cid
        self._items[cid] = {
            "id": cid,
            "doc_id": key[0],
            "filename": str(_get(chunk, "filename")),
            "page": key[1],  # 1-based
            "quote": key[2][:200],
        }
        return cid

    def get(self, cid: int) -> dict:
        return dict(self._items[cid])

    def ids(self) -> set[int]:
        return set(self._items)

    def validate(self, markdown: str) -> list[dict]:
        """คืน citation ของ id ที่ถูกอ้างใน markdown และมีอยู่ใน registry จริง เรียงตาม id"""
        cited = {int(n) for n in CITE.findall(markdown)}
        return [self.get(cid) for cid in sorted(cited & self.ids())]
