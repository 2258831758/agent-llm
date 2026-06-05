from __future__ import annotations

from pathlib import Path

from backend.app.scanners.utils import scan_text_patterns


def run(project_path: Path) -> list[dict[str, object]]:
    patterns = [
        (
            "SECRET_KEY",
            "HIGH",
            "硬编码密钥",
            "疑似应用密钥被直接写入源码文件。",
        ),
        (
            "AKIA",
            "HIGH",
            "AWS 密钥泄露",
            "仓库中发现了疑似 AWS Access Key 的内容。",
        ),
        (
            "password =",
            "MEDIUM",
            "硬编码密码",
            "账号密码不应直接提交到应用代码中。",
        ),
    ]
    return scan_text_patterns(project_path, "Gitleaks", patterns)
