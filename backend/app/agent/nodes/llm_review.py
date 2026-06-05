from __future__ import annotations

from backend.app.agent.nodes.helpers import append_log, publish_agent_state
from backend.app.agent.state import AuditFinding, AuditState


def _derive_llm_findings(scan_results: list[AuditFinding]) -> list[AuditFinding]:
    llm_findings: list[AuditFinding] = []

    for item in scan_results:
        title = str(item["title"])
        if "SQL 注入" in title or "SQL Injection" in title:
            llm_findings.append(
                {
                    "source": "LLMReview",
                    "severity": "HIGH",
                    "title": "业务逻辑中的 SQL 注入路径",
                    "description": "当前查询拼接方式说明未受信输入可能在未参数化的情况下进入 SQL 执行流程。",
                    "file_path": str(item["file_path"]),
                    "line_number": int(item["line_number"]),
                    "cvss_score": 0.0,
                }
            )
        if "命令" in title or "Command" in title or "Shell" in title:
            llm_findings.append(
                {
                    "source": "LLMReview",
                    "severity": "HIGH",
                    "title": "潜在的远程命令执行链路",
                    "description": "运行时命令执行与用户输入处理组合出现时，需要重点人工验证是否存在 RCE 风险。",
                    "file_path": str(item["file_path"]),
                    "line_number": int(item["line_number"]),
                    "cvss_score": 0.0,
                }
            )
        if "密钥" in title or "密码" in title or "Secret" in title or "Password" in title:
            llm_findings.append(
                {
                    "source": "LLMReview",
                    "severity": "MEDIUM",
                    "title": "凭据泄露风险",
                    "description": "硬编码密钥会扩大泄露后的影响范围，也会增加后续轮换和收敛成本。",
                    "file_path": str(item["file_path"]),
                    "line_number": int(item["line_number"]),
                    "cvss_score": 0.0,
                }
            )

    return llm_findings


async def run(state: AuditState) -> dict[str, object]:
    await publish_agent_state(state["task_id"], "LLMReview", "running", "正在汇总 AI 审计结论", 75)

    llm_results = _derive_llm_findings(state["scan_results"])
    message = f"AI 审计补充了 {len(llm_results)} 条结果"

    await publish_agent_state(state["task_id"], "LLMReview", "completed", message, 80)
    return {
        "llm_results": llm_results,
        "logs": append_log(state, message),
    }
