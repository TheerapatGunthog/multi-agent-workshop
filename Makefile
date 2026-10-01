# ทางลัดของคำสั่ง docker compose (Windows ที่ไม่มี make ใช้คำสั่งใน README ได้เลย)
.PHONY: up down logs ingest restart shell-backend check

.env:
	cp .env.example .env

up: .env
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f backend docs-mcp hr-mcp

ingest: .env
	docker compose run --rm backend python ingest.py

restart:
	docker compose restart backend

shell-backend:
	docker compose exec backend bash

# ตรวจของที่ทำไว้ให้ (registry, events, MCP servers)
check:
	docker compose exec backend python check_registry.py
	docker compose exec backend python check_events.py
	docker compose exec backend python scripts/check_mcp.py
