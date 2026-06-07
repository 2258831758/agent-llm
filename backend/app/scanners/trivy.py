from __future__ import annotations

from pathlib import Path


def run(project_path: Path) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []

    for dependency_file in project_path.rglob("*"):
        if not dependency_file.is_file():
            continue
        if dependency_file.name not in {"requirements.txt", "package.json", "go.mod"}:
            continue

        try:
            content = dependency_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        relative_path = dependency_file.relative_to(project_path).as_posix()
        lines = content.splitlines()

        vulnerable_markers = [
            (
                "requests==2.19.0",
                "HIGH",
                "Known Vulnerable Dependency",
                "requests 2.19.0 存在公开披露的安全问题，建议尽快升级。",
            ),
            (
                "flask==1.0",
                "MEDIUM",
                "Outdated Framework Dependency",
                "Flask 1.0 版本过旧，不适合安全敏感场景。",
            ),
            (
                '"lodash": "4.17.15"',
                "HIGH",
                "Known Vulnerable Dependency",
                "lodash 4.17.15 关联多个公开安全公告。",
            ),
        ]

        lowered_content = content.lower()
        for marker, severity, title, description in vulnerable_markers:
            if marker.lower() not in lowered_content:
                continue
            matched_line = 1
            for index, line in enumerate(lines, start=1):
                if marker.lower() in line.lower():
                    matched_line = index
                    break
            results.append(
                {
                    "source": "Trivy",
                    "severity": severity,
                    "title": title,
                    "description": description,
                    "file_path": relative_path,
                    "line_number": matched_line,
                    "cvss_score": 0.0,
                    "metadata": {"marker": marker},
                }
            )

    return results
