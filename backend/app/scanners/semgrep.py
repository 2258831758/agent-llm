from __future__ import annotations

from pathlib import Path

from backend.app.scanners.utils import scan_text_patterns


def run(project_path: Path) -> list[dict[str, object]]:
    patterns = [
        (
            "SELECT * FROM users WHERE username = '",
            "HIGH",
            "SQL 注入",
            "检测到直接拼接 SQL 字符串，存在注入风险。",
        ),
        (
            "requests.get(url)",
            "MEDIUM",
            "潜在 SSRF",
            "外部请求直接使用变量 URL，建议增加白名单或协议校验。",
        ),
        (
            "yaml.load(",
            "HIGH",
            "不安全的 YAML 解析",
            "yaml.load 未使用安全加载器时，可能执行任意对象。",
        ),
    ]
    return scan_text_patterns(project_path, "Semgrep", patterns)
