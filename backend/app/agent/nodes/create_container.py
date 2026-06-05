from __future__ import annotations

from backend.app.agent.nodes.helpers import append_log, publish_agent_state
from backend.app.agent.state import AuditState
from backend.app.services.sandbox import get_sandbox_runner


async def run(state: AuditState) -> dict[str, object]:
    await publish_agent_state(state["task_id"], "CreateSandbox", "running", "正在准备沙箱接口", 45)

    sandbox = await get_sandbox_runner().create(state["task_id"])
    message = sandbox.message

    await publish_agent_state(state["task_id"], "CreateSandbox", "completed", message, 50)
    return {
        "sandbox_id": sandbox.sandbox_id,
        "logs": append_log(state, message),
    }
