from __future__ import annotations

from backend.app.agent.state import AuditState
from backend.app.services.events import event_bus


async def publish_agent_state(task_id: str, agent: str, status: str, message: str, progress: int) -> None:
    await event_bus.publish(task_id, {"event": "agent", "agent": agent, "status": status, "message": message})
    await event_bus.publish(task_id, {"event": "progress", "value": progress, "message": message})


def append_log(state: AuditState, message: str) -> list[str]:
    return [*state["logs"], message]

