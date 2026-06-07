from __future__ import annotations

from pathlib import Path

from backend.app.scanners.utils import scan_text_patterns


def run(project_path: Path) -> list[dict[str, object]]:
    patterns = [
        (
            "os.system(",
            "HIGH",
            "Command Execution Sink",
            "检测到 os.system 调用，如参数可控可能形成远程命令执行。",
        ),
        (
            "shell=True",
            "HIGH",
            "Shell Injection Risk",
            "subprocess 使用 shell=True 时，如果输入未严格限制，容易被拼接执行。",
        ),
        (
            "pickle.loads(",
            "HIGH",
            "Unsafe Deserialization",
            "pickle.loads 处理不可信数据时，可能触发任意代码执行。",
        ),
        (
            "hashlib.md5(",
            "MEDIUM",
            "Weak Password Hashing",
            "检测到使用 MD5 处理敏感凭据，无法满足现代身份认证保护要求。",
        ),
    ]
    return scan_text_patterns(project_path, "Bandit", patterns)
