from __future__ import annotations

from backend.app.agent.nodes.helpers import append_log, publish_agent_state
from backend.app.agent.state import AuditFinding, AuditState


SEVERITY_TO_CVSS = {
    "CRITICAL": 9.8,
    "HIGH": 8.5,
    "MEDIUM": 6.2,
    "LOW": 3.7,
}


def deduplicate_findings(items: list[AuditFinding]) -> list[AuditFinding]:
    deduped: dict[tuple[str, str, int], AuditFinding] = {}
    for item in items:
        key = (str(item["title"]), str(item["file_path"]), int(item["line_number"]))
        candidate = dict(item)
        candidate["cvss_score"] = SEVERITY_TO_CVSS.get(str(item["severity"]).upper(), 0.0)
        deduped[key] = candidate
    return sorted(deduped.values(), key=lambda item: (-float(item["cvss_score"]), str(item["title"])))


async def run(state: AuditState) -> dict[str, object]:
    await publish_agent_state(state["task_id"], "RiskValidate", "running", "正在去重并计算风险评分", 88)

    merged = [*state["scan_results"], *state["llm_results"]]
    findings = deduplicate_findings(merged)
    message = f"风险归并完成，最终保留 {len(findings)} 条漏洞"

    await publish_agent_state(state["task_id"], "RiskValidate", "completed", message, 92)
    return {
        "findings": findings,
        "logs": append_log(state, message),
    }
