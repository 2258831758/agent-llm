from __future__ import annotations

import re
from pathlib import Path

from backend.app.scanners.utils import should_skip_text_scan


def run(project_path: Path) -> list[dict[str, object]]:
    rules = (
        (
            re.compile(r"\bSECRET_KEY\b\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
            "HIGH",
            "Hardcoded Secret Key",
            "疑似应用密钥被直接写入源代码文件。",
        ),
        (
            re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
            "HIGH",
            "AWS Access Key Exposure",
            "仓库中发现疑似 AWS Access Key 标识，需立即确认并轮换。",
        ),
        (
            re.compile(r"(?i)\b(password|passwd|pwd)\b\s*[:=]\s*['\"][^'\"\r\n]{4,}['\"]"),
            "MEDIUM",
            "Hardcoded Password",
            "账号口令不应直接提交到应用代码中。",
        ),
    )

    results: list[dict[str, object]] = []
    for file_path in project_path.rglob("*"):
        if not file_path.is_file():
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if should_skip_text_scan(file_path, content):
            continue

        relative_path = file_path.relative_to(project_path).as_posix()
        lines = content.splitlines()
        for index, line in enumerate(lines, start=1):
            for pattern, severity, title, description in rules:
                match = pattern.search(line)
                if match is None:
                    continue
                results.append(
                    {
                        "source": "Gitleaks",
                        "severity": severity,
                        "title": title,
                        "description": description,
                        "file_path": relative_path,
                        "line_number": index,
                        "cvss_score": 0.0,
                        "metadata": {"needle": match.group(0)},
                    }
                )

    return results
