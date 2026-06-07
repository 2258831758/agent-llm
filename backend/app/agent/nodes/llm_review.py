from __future__ import annotations

from pathlib import Path

from backend.app.agent.nodes.helpers import append_log, publish_agent_state
from backend.app.agent.state import AuditFinding, AuditState
from backend.app.services.llm_review_service import review_project_with_llm


def _derive_llm_findings(scan_results: list[AuditFinding]) -> list[AuditFinding]:
    llm_findings: list[AuditFinding] = []

    for item in scan_results:
        title = str(item.get("title", ""))
        file_path = str(item.get("file_path", ""))
        line_number = int(item.get("line_number", 1))

        if "sql injection" in title.lower():
            llm_findings.append(
                {
                    "source": "LLMReview",
                    "severity": "HIGH",
                    "title": "Untrusted Input Reaches SQL Execution Path",
                    "description": "该查询路径显示未受信输入可能在未参数化的情况下进入 SQL 执行流程，需要优先人工复核。",
                    "file_path": file_path,
                    "line_number": line_number,
                    "cvss_score": 0.0,
                    "metadata": {"analysis_type": "heuristic", "parent_title": title},
                }
            )

        if any(keyword in title.lower() for keyword in ("command", "shell")):
            llm_findings.append(
                {
                    "source": "LLMReview",
                    "severity": "HIGH",
                    "title": "Possible Remote Command Execution Chain",
                    "description": "命令执行点与用户输入处理组合出现时，需要重点确认是否存在可实际利用的 RCE 链路。",
                    "file_path": file_path,
                    "line_number": line_number,
                    "cvss_score": 0.0,
                    "metadata": {"analysis_type": "heuristic", "parent_title": title},
                }
            )

        if any(keyword in title.lower() for keyword in ("secret", "password", "credential", "hashing")):
            llm_findings.append(
                {
                    "source": "LLMReview",
                    "severity": "MEDIUM",
                    "title": "Credential Exposure and Authentication Weakness",
                    "description": "硬编码凭据或弱认证处理会扩大泄露后的影响范围，也会增加后续轮换和修复成本。",
                    "file_path": file_path,
                    "line_number": line_number,
                    "cvss_score": 0.0,
                    "metadata": {"analysis_type": "heuristic", "parent_title": title},
                }
            )

        if "authorization" in title.lower() or "access control" in title.lower():
            llm_findings.append(
                {
                    "source": "LLMReview",
                    "severity": "HIGH",
                    "title": "Sensitive Route May Miss Server-Side Authorization",
                    "description": "如果敏感接口只在前端隐藏而没有后端鉴权，低权限用户可能直接访问管理能力。",
                    "file_path": file_path,
                    "line_number": line_number,
                    "cvss_score": 0.0,
                    "metadata": {"analysis_type": "heuristic", "parent_title": title},
                }
            )

    return llm_findings


async def run(state: AuditState) -> dict[str, object]:
    await publish_agent_state(state["task_id"], "LLMReview", "running", "正在调用大模型进行语义审计", 75)

    try:
        llm_results, message = await review_project_with_llm(
            task_id=state["task_id"],
            user_id=state["user_id"],
            task_name=state["task_name"],
            project_path=Path(state["project_path"]),
            language=state["language"],
            framework=state["framework"],
            entrypoint=state["entrypoint"],
            scan_results=state["scan_results"],
        )
    except Exception as exc:
        llm_results = []
        message = f"真实模型调用失败，回退到启发式审计: {exc}"

    if not llm_results:
        heuristic_findings = _derive_llm_findings(state["scan_results"])
        if "回退" not in message and "跳过" not in message:
            message = f"{message}，已回退到启发式审计"
        llm_results = heuristic_findings
        message = f"{message}，最终生成 {len(llm_results)} 条结果"

    await publish_agent_state(state["task_id"], "LLMReview", "completed", message, 80)
    return {
        "llm_results": llm_results,
        "logs": append_log(state, message),
    }
