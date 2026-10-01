"""ทดสอบ validate_citations: docker compose exec backend python check_validate.py"""
from app.agent import validate_citations

C = [{"id": i, "doc_id": "d", "filename": "d.pdf", "page": 1, "quote": "q"} for i in (1, 2, 3)]

assert [c["id"] for c in validate_citations("a [1] b [2]", C)] == [1, 2]
assert validate_citations("a [4]", C) == []
assert validate_citations("ไม่มีอ้างอิง", C) == []
print("ALL PASSED")
