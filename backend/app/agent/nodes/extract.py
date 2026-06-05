from __future__ import annotations

from pathlib import Path

from backend.app.agent.nodes.helpers import append_log, publish_agent_state
from backend.app.agent.state import AuditState
from backend.app.services.files import extract_project, list_project_files


async def run(state: AuditState) -> dict[str, object]:
    await publish_agent_state(state["task_id"], "ExtractProject", "running", "正在解压并准备上传的项目", 15)

    project_path = extract_project(state["task_id"], Path(state["file_path"]))
    file_count = len(list_project_files(project_path))
    message = f"项目已解压到 {project_path}，共发现 {file_count} 个文件"

    await publish_agent_state(state["task_id"], "ExtractProject", "completed", message, 20)
    return {
        "project_path": str(project_path),
        "logs": append_log(state, message),
    }
