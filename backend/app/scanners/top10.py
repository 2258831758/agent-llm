from __future__ import annotations

from pathlib import Path


AUTH_HINTS = (
    "depends(",
    "login_required",
    "current_user",
    "authorize",
    "permission",
    "require_role",
    "jwt",
    "token",
    "auth",
)

SOURCE_SUFFIXES = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".php", ".yml", ".yaml", ".json"}


def _build_finding(
    *,
    title: str,
    description: str,
    severity: str,
    relative_path: str,
    line_number: int,
    evidence: str,
) -> dict[str, object]:
    return {
        "source": "Top10Heuristic",
        "severity": severity,
        "title": title,
        "description": description,
        "file_path": relative_path,
        "line_number": line_number,
        "cvss_score": 0.0,
        "metadata": {"needle": evidence},
    }


def run(project_path: Path) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []

    for file_path in project_path.rglob("*"):
        if not file_path.is_file() or file_path.suffix.lower() not in SOURCE_SUFFIXES:
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        lines = content.splitlines()
        lowered_lines = [line.lower() for line in lines]
        relative_path = file_path.relative_to(project_path).as_posix()
        lowered_content = content.lower()

        if 'allow_origins=["*"]' in lowered_content or "allow_origins = [\"*\"]" in lowered_content:
            line_number = next(
                (index for index, line in enumerate(lowered_lines, start=1) if "allow_origins" in line and "*" in line),
                1,
            )
            results.append(
                _build_finding(
                    title="Overly Permissive CORS Configuration",
                    description="检测到过度开放的跨域配置，可能扩大未授权调用面。",
                    severity="MEDIUM",
                    relative_path=relative_path,
                    line_number=line_number,
                    evidence=lines[line_number - 1].strip(),
                )
            )

        for index, line in enumerate(lines, start=1):
            lowered_line = line.lower()
            stripped = line.strip()

            if (
                "@app.get(\"/admin" in lowered_line
                or "@app.post(\"/admin" in lowered_line
                or "@router.get(\"/admin" in lowered_line
                or "@router.post(\"/admin" in lowered_line
            ):
                window = "\n".join(lowered_lines[index - 1 : index + 8])
                if not any(hint in window for hint in AUTH_HINTS):
                    results.append(
                        _build_finding(
                            title="Missing Admin Authorization Check",
                            description="管理接口附近未发现显式鉴权或权限校验，存在越权访问风险。",
                            severity="HIGH",
                            relative_path=relative_path,
                            line_number=index,
                            evidence=stripped,
                        )
                    )

            if "debug=true" in lowered_line or "app.debug = true" in lowered_line:
                results.append(
                    _build_finding(
                        title="Debug Mode Enabled",
                        description="生产环境保留调试模式会扩大错误信息暴露与攻击面。",
                        severity="MEDIUM",
                        relative_path=relative_path,
                        line_number=index,
                        evidence=stripped,
                    )
                )

            if "verify=false" in lowered_line:
                results.append(
                    _build_finding(
                        title="TLS Verification Disabled",
                        description="检测到关闭 TLS 证书校验，可能遭受中间人攻击。",
                        severity="MEDIUM",
                        relative_path=relative_path,
                        line_number=index,
                        evidence=stripped,
                    )
                )

            if "hashlib.md5(" in lowered_line or "hashlib.sha1(" in lowered_line:
                results.append(
                    _build_finding(
                        title="Weak Credential Hashing",
                        description="使用弱散列算法处理凭据，不符合当前身份认证保护要求。",
                        severity="MEDIUM",
                        relative_path=relative_path,
                        line_number=index,
                        evidence=stripped,
                    )
                )

            if lowered_line.strip() == "except exception:" and index < len(lines) and lines[index].strip() == "pass":
                results.append(
                    _build_finding(
                        title="Exception Swallowed Without Logging",
                        description="捕获异常后直接忽略，可能导致安全事件无法被及时发现。",
                        severity="LOW",
                        relative_path=relative_path,
                        line_number=index,
                        evidence=f"{stripped} / {lines[index].strip()}",
                    )
                )

    return results
