"""ทดสอบ CitationRegistry: docker compose exec backend python check_registry.py"""
from app.registry import CitationRegistry

r = CitationRegistry()
a = {"doc_id": "leave-handbook", "filename": "leave-handbook.pdf", "page": 2, "text": "ลาพักผ่อน 10 วัน"}
b = {"doc_id": "leave-handbook", "filename": "leave-handbook.pdf", "page": 3, "text": "ลาป่วย 3 วัน"}

assert r.register(a) == 1
assert r.register(b) == 2
assert r.register(dict(a)) == 1, "chunk เดิมต้องได้ id เดิม"
assert r.get(2)["page"] == 3
assert r.ids() == {1, 2}
assert [c["id"] for c in r.validate("x [2] y [1] z [9]")] == [1, 2], "ต้องตัด [9] ที่ไม่มีอยู่จริง"
assert r.validate("ไม่ได้อ้างอะไร") == []
print("ALL PASSED")
