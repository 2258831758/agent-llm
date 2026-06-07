from __future__ import annotations

from pathlib import Path

from backend.app.scanners.utils import scan_text_patterns


def run(project_path: Path) -> list[dict[str, object]]:
    patterns = [
        (
            "SELECT * FROM users WHERE username = '",
            "HIGH",
            "SQL Injection",
            "检测到用户输入直接拼接到 SQL 语句中，存在注入风险。",
        ),
        (
            "requests.get(url)",
            "HIGH",
            "Potential SSRF",
            "外部请求直接使用变量 URL，可能被利用访问内网或元数据服务。",
        ),
        (
            "yaml.load(",
            "HIGH",
            "Unsafe YAML Deserialization",
            "yaml.load 未使用安全加载器时，可能触发任意对象构造或执行。",
        ),
        (
            "verify=False",
            "MEDIUM",
            "TLS Verification Disabled",
            "网络请求关闭证书校验，会降低对中间人攻击的防护能力。",
        ),
    ]
    return scan_text_patterns(project_path, "Semgrep", patterns)
