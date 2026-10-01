"""ทดสอบ EventBus: docker compose exec backend python check_events.py"""
import asyncio

from app.events import EventBus


async def main() -> None:
    bus = EventBus()
    await bus.activity("research", "t1", "tool_call", "ค้นเอกสาร: ลาพักผ่อน")
    await bus.progress(1, 4, "สิทธิลาพักผ่อน")
    await bus.close()
    await bus.emit("token", {"text": "หลัง close ต้องไม่ถูกส่ง"})
    out = [e async for e in bus.stream()]
    assert len(out) == 2, out
    assert out[0].startswith("event: activity") and '"task_id": "t1"' in out[0]
    assert out[1].startswith("event: progress")
    print("ALL PASSED")


asyncio.run(main())
