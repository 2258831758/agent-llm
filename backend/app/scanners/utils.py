from __future__ import annotations

from pathlib import Path


def scan_text_patterns(
    project_path: Path,
    source: str,
    patterns: list[tuple[str, str, str, str]],
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    ignored_suffixes = {".pyc", ".pyo", ".so", ".dll", ".exe", ".class", ".png", ".jpg", ".jpeg", ".gif", ".pdf"}

    for file_path in project_path.rglob("*"):
        if not file_path.is_file():
            continue
        if "__pycache__" in file_path.parts or file_path.suffix.lower() in ignored_suffixes:
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        lowered_content = content.lower()
        lines = content.splitlines()
        relative_path = file_path.relative_to(project_path).as_posix()

        for needle, severity, title, description in patterns:
            lowered_needle = needle.lower()
            if lowered_needle not in lowered_content:
                continue

            matched_line = 1
            for index, line in enumerate(lines, start=1):
                if lowered_needle in line.lower():
                    matched_line = index
                    break

            results.append(
                {
                    "source": source,
                    "severity": severity,
                    "title": title,
                    "description": description,
                    "file_path": relative_path,
                    "line_number": matched_line,
                    "cvss_score": 0.0,
                    "metadata": {"needle": needle},
                }
            )

    return results
