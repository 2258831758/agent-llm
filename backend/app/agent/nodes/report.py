from __future__ import annotations

from backend.app.agent.nodes.helpers import append_log, publish_agent_state
from backend.app.agent.state import AuditState
from backend.app.services.reports import write_reports


async def run(state: AuditState) -> dict[str, object]:
    await publish_agent_state(state["task_id"], "GenerateReport", "running", "正在生成报告文件", 96)

    report_paths = write_reports(
        task_id=state["task_id"],
        task_name=state["task_name"],
        language=state["language"],
        framework=state["framework"],
        findings=[dict(item) for item in state["findings"]],
    )
    message = f"报告已生成，目录：{report_paths['report_dir']}"

    await publish_agent_state(state["task_id"], "GenerateReport", "completed", message, 99)
    return {
        "report_paths": report_paths,
        "status": "completed",
        "logs": append_log(state, message),
    }
