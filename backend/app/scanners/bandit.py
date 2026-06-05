from __future__ import annotations

from pathlib import Path

from backend.app.scanners.utils import scan_text_patterns


def run(project_path: Path) -> list[dict[str, object]]:
    patterns = [
        (
            "os.system(",
            "HIGH",
            "系统命令执行",
            "检测到 os.system 调用，如参数可控可能形成远程命令执行。",
        ),
        (
            "shell=True",
            "HIGH",
            "Shell 注入风险",
            "subprocess 使用 shell=True 时，需要严格限制输入内容。",
        ),
        (
            "pickle.loads(",
            "HIGH",
            "不安全的反序列化",
            "pickle.loads 处理不可信数据时，可能导致任意代码执行。",
        ),
    ]
    return scan_text_patterns(project_path, "Bandit", patterns)
