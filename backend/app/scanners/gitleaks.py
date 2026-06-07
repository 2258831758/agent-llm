from __future__ import annotations

from pathlib import Path

from backend.app.scanners.utils import scan_text_patterns


def run(project_path: Path) -> list[dict[str, object]]:
    patterns = [
        (
            "SECRET_KEY",
            "HIGH",
            "Hardcoded Secret Key",
            "疑似应用密钥被直接写入源代码文件。",
        ),
        (
            "AKIA",
            "HIGH",
            "AWS Access Key Exposure",
            "仓库中发现疑似 AWS Access Key 标识，需立即确认并轮换。",
        ),
        (
            "password =",
            "MEDIUM",
            "Hardcoded Password",
            "账号口令不应直接提交到应用代码中。",
        ),
    ]
    return scan_text_patterns(project_path, "Gitleaks", patterns)
