from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from backend.app.core.config import settings
from backend.app.services.vulnerability_catalog import build_top10_summary


SEVERITY_LABELS = {
    "CRITICAL": "严重",
    "HIGH": "高危",
    "MEDIUM": "中危",
    "LOW": "低危",
}


def build_report_payload(
    task_id: str,
    task_name: str,
    language: str,
    framework: str,
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    localized_findings: list[dict[str, Any]] = []
    for item in findings:
        localized = dict(item)
        severity = str(localized.get("severity", "")).upper()
        localized["severity"] = severity
        localized["severity_label"] = SEVERITY_LABELS.get(severity, severity or "未知")
        localized["line_number"] = int(localized.get("line_number", 1) or 1)
        localized["cvss_score"] = float(localized.get("cvss_score", 0.0) or 0.0)
        localized["reproduction_steps"] = list(localized.get("reproduction_steps") or [])
        localized["related_files"] = list(localized.get("related_files") or [])
        localized["references"] = list(localized.get("references") or [])
        localized_findings.append(localized)

    localized_findings.sort(key=lambda item: (-float(item["cvss_score"]), str(item["title"])))
    severities = Counter(item["severity"] for item in localized_findings)

    return {
        "report_title": "代码审计报告",
        "task_id": task_id,
        "task_name": task_name,
        "language": language or "unknown",
        "framework": framework or "unknown",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "labels": {
            "task_id": "任务 ID",
            "language": "语言",
            "framework": "框架",
            "total": "漏洞总数",
            "critical": "严重风险",
            "high": "高危风险",
            "medium": "中危风险",
            "low": "低危风险",
            "source": "来源",
            "location": "位置",
            "description": "描述",
            "impact": "影响",
            "recommendation": "修复建议",
            "related_files": "关联文件",
            "owasp": "OWASP Top 10",
            "reproduction": "复现步骤",
            "evidence": "证据",
            "related_cves": "关联 CVE",
            "ctf": "CTF 常见利用点",
            "references": "参考资料",
        },
        "summary": {
            "total": len(localized_findings),
            "critical": severities.get("CRITICAL", 0),
            "high": severities.get("HIGH", 0),
            "medium": severities.get("MEDIUM", 0),
            "low": severities.get("LOW", 0),
        },
        "top10_summary": build_top10_summary(localized_findings),
        "findings": localized_findings,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    labels = payload["labels"]
    summary = payload["summary"]
    lines = [
        f"# {payload['report_title']} - {payload['task_name']}",
        "",
        f"- {labels['task_id']}: `{payload['task_id']}`",
        f"- {labels['language']}: `{payload['language']}`",
        f"- {labels['framework']}: `{payload['framework']}`",
        f"- 生成时间: `{payload['generated_at']}`",
        f"- {labels['total']}: `{summary['total']}`",
        f"- {labels['critical']}: `{summary['critical']}`",
        f"- {labels['high']}: `{summary['high']}`",
        f"- {labels['medium']}: `{summary['medium']}`",
        f"- {labels['low']}: `{summary['low']}`",
        "",
        "## OWASP Top 10 覆盖",
        "",
    ]

    for item in payload["top10_summary"]:
        lines.append(f"- `{item['owasp_id']}` {item['owasp_name_zh']}: `{item['count']}`")

    lines.extend(["", "## 漏洞详情", ""])

    if not payload["findings"]:
        lines.append("未发现有效漏洞。")
        return "\n".join(lines)

    for item in payload["findings"]:
        lines.extend(
            [
                f"### [{item['severity_label']}] {item['title']}",
                f"- {labels['source']}: `{item['source']}`",
                f"- {labels['owasp']}: `{item.get('owasp_label', '未分类')}`",
                f"- CWE: `{item.get('cwe_id', 'N/A')}`",
                f"- {labels['location']}: `{item['file_path']}:{item['line_number']}`",
                f"- CVSS: `{item['cvss_score']}`",
                f"- {labels['description']}: {item['description']}",
                f"- {labels['impact']}: {item.get('impact', 'N/A')}",
                f"- {labels['recommendation']}: {item.get('recommendation', 'N/A')}",
            ]
        )

        if item.get("evidence"):
            lines.append(f"- {labels['evidence']}: `{item['evidence']}`")
        if item.get("related_files"):
            lines.append(f"- {labels['related_files']}: `{', '.join(item['related_files'])}`")
        if item.get("related_cves"):
            lines.append(f"- {labels['related_cves']}: `{', '.join(item['related_cves'])}`")

        if item.get("code_snippet"):
            lines.extend(["", "```text", item["code_snippet"], "```"])

        if item.get("reproduction_steps"):
            lines.append("")
            lines.append(f"**{labels['reproduction']}**")
            for step in item["reproduction_steps"]:
                lines.append(f"- {step}")

        if item.get("ctf_scenarios"):
            lines.append("")
            lines.append(f"**{labels['ctf']}**")
            for scenario in item["ctf_scenarios"]:
                lines.append(f"- {scenario}")

        if item.get("references"):
            lines.append("")
            lines.append(f"**{labels['references']}**")
            for reference in item["references"]:
                lines.append(f"- {reference}")

        lines.append("")

    return "\n".join(lines)


def render_html(payload: dict[str, Any]) -> str:
    env = Environment(
        loader=FileSystemLoader(settings.template_root),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("report.html.j2")
    return template.render(payload=payload)


def write_reports(
    task_id: str,
    task_name: str,
    language: str,
    framework: str,
    findings: list[dict[str, Any]],
) -> dict[str, str]:
    settings.ensure_directories()
    report_dir = settings.report_root / task_id
    report_dir.mkdir(parents=True, exist_ok=True)

    payload = build_report_payload(task_id, task_name, language, framework, findings)
    markdown = render_markdown(payload)
    html = render_html(payload)
    json_text = json.dumps(payload, indent=2, ensure_ascii=False)

    markdown_path = report_dir / "report.md"
    html_path = report_dir / "report.html"
    json_path = report_dir / "report.json"

    markdown_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")
    json_path.write_text(json_text, encoding="utf-8")

    return {
        "report_dir": str(report_dir),
        "markdown": str(markdown_path),
        "html": str(html_path),
        "json": str(json_path),
    }
