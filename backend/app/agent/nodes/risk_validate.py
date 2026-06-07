from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.app.agent.nodes.helpers import append_log, publish_agent_state
from backend.app.agent.state import AuditFinding, AuditState
from backend.app.services.vulnerability_catalog import enrich_finding


SEVERITY_TO_CVSS = {
    "CRITICAL": 9.8,
    "HIGH": 8.5,
    "MEDIUM": 6.5,
    "LOW": 3.7,
}


def _merge_values(primary: Any, secondary: Any) -> Any:
    if isinstance(primary, list) and isinstance(secondary, list):
        merged: list[Any] = []
        for item in [*primary, *secondary]:
            if item not in merged:
                merged.append(item)
        return merged

    if isinstance(primary, dict) and isinstance(secondary, dict):
        merged = dict(primary)
        merged.update(secondary)
        return merged

    if primary in (None, "", [], {}):
        return secondary
    if secondary in (None, "", [], {}):
        return primary
    if isinstance(primary, str) and isinstance(secondary, str):
        return secondary if len(secondary) > len(primary) else primary
    return primary


def _merge_findings(existing: AuditFinding, candidate: AuditFinding) -> AuditFinding:
    merged: AuditFinding = dict(existing)
    existing_sources = {part.strip() for part in str(existing.get("source", "")).split(",") if part.strip()}
    candidate_sources = {part.strip() for part in str(candidate.get("source", "")).split(",") if part.strip()}
    merged["source"] = ", ".join(sorted(existing_sources | candidate_sources))

    for key in set(existing.keys()) | set(candidate.keys()):
        if key == "source":
            continue
        merged[key] = _merge_values(existing.get(key), candidate.get(key))

    existing_cvss = float(existing.get("cvss_score", 0.0))
    candidate_cvss = float(candidate.get("cvss_score", 0.0))
    merged["cvss_score"] = max(existing_cvss, candidate_cvss)

    severity_ranking = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    existing_severity = str(existing.get("severity", "LOW")).upper()
    candidate_severity = str(candidate.get("severity", "LOW")).upper()
    merged["severity"] = (
        existing_severity
        if severity_ranking.get(existing_severity, 0) >= severity_ranking.get(candidate_severity, 0)
        else candidate_severity
    )
    return merged


def deduplicate_findings(items: list[AuditFinding], project_root: Path) -> list[AuditFinding]:
    deduped: dict[tuple[str, str, int], AuditFinding] = {}
    for item in items:
        candidate = enrich_finding(dict(item), project_root)
        severity = str(candidate.get("severity", "LOW")).upper()
        candidate["severity"] = severity
        candidate["cvss_score"] = max(
            float(candidate.get("cvss_score", 0.0)),
            SEVERITY_TO_CVSS.get(severity, 0.0),
        )

        signature = str(candidate.get("cwe_id") or candidate.get("title") or "finding")
        key = (signature, str(candidate.get("file_path", "")), int(candidate.get("line_number", 1)))
        if key in deduped:
            deduped[key] = _merge_findings(deduped[key], candidate)
        else:
            deduped[key] = candidate

    return sorted(
        deduped.values(),
        key=lambda item: (-float(item.get("cvss_score", 0.0)), str(item.get("title", ""))),
    )


async def run(state: AuditState) -> dict[str, object]:
    await publish_agent_state(state["task_id"], "RiskValidate", "running", "正在归并结果、映射 OWASP Top 10 并补全复现信息", 88)

    merged = [*state["scan_results"], *state["llm_results"]]
    findings = deduplicate_findings(merged, Path(state["project_path"]))
    message = f"风险归并完成，最终保留 {len(findings)} 条漏洞"

    await publish_agent_state(state["task_id"], "RiskValidate", "completed", message, 92)
    return {
        "findings": findings,
        "logs": append_log(state, message),
    }
