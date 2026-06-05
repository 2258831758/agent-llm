from __future__ import annotations

from pathlib import Path

from backend.app.agent.nodes.helpers import append_log, publish_agent_state
from backend.app.agent.state import AuditState


def detect_stack(project_path: Path) -> tuple[str, str, str]:
    files = {path.name: path for path in project_path.rglob("*") if path.is_file()}

    if "package.json" in files:
        content = files["package.json"].read_text(encoding="utf-8", errors="ignore").lower()
        framework = "nextjs" if '"next"' in content else "nodejs"
        return "javascript", framework, "package.json"

    if "go.mod" in files:
        return "go", "go", "go.mod"

    if "composer.json" in files:
        content = files["composer.json"].read_text(encoding="utf-8", errors="ignore").lower()
        framework = "laravel" if "laravel" in content else "php"
        return "php", framework, "composer.json"

    if "cargo.toml" in {name.lower(): path for name, path in files.items()}:
        return "rust", "rust", "Cargo.toml"

    py_files = [path for path in project_path.rglob("*.py")]
    if py_files:
        framework = "python"
        entrypoint = py_files[0].relative_to(project_path).as_posix()

        for file_path in py_files:
            content = file_path.read_text(encoding="utf-8", errors="ignore").lower()
            if "from fastapi import" in content:
                framework = "fastapi"
                entrypoint = file_path.relative_to(project_path).as_posix()
                break
            if "from flask import" in content:
                framework = "flask"
                entrypoint = file_path.relative_to(project_path).as_posix()
                break
            if "django" in content:
                framework = "django"
                entrypoint = file_path.relative_to(project_path).as_posix()
                break

        return "python", framework, entrypoint

    return "unknown", "unknown", ""


async def run(state: AuditState) -> dict[str, object]:
    await publish_agent_state(state["task_id"], "DetectStack", "running", "正在识别项目语言和框架", 30)

    language, framework, entrypoint = detect_stack(Path(state["project_path"]))
    message = f"识别结果：语言={language}，框架={framework}，入口={entrypoint or '无'}"

    await publish_agent_state(state["task_id"], "DetectStack", "completed", message, 35)
    return {
        "language": language,
        "framework": framework,
        "entrypoint": entrypoint,
        "logs": append_log(state, message),
    }
