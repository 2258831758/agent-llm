from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any

from backend.app.agent.state import AuditFinding


SKILL_ROOT = Path(__file__).resolve().parents[1] / "skills" / "code_security_review"
RESOURCE_ROOT = SKILL_ROOT / "resources"
CPP_EXTENSIONS = {".c", ".cc", ".cpp", ".h"}


@dataclass(frozen=True)
class CodeSecuritySkillResources:
    audit_prompt: str
    filtering_rules: str
    hard_exclusion_patterns: str


@dataclass(frozen=True)
class HardExclusionMatch:
    reason: str


_DOS_PATTERNS = (
    re.compile(r"\b(denial of service|dos attack|resource exhaustion)\b", re.IGNORECASE),
    re.compile(r"\b(exhaust|overwhelm|overload).*?(resource|memory|cpu)\b", re.IGNORECASE),
    re.compile(r"\b(infinite|unbounded).*?(loop|recursion)\b", re.IGNORECASE),
)
_RATE_LIMIT_PATTERNS = (
    re.compile(r"\b(missing|lack of|no)\s+rate\s+limit", re.IGNORECASE),
    re.compile(r"\brate\s+limiting\s+(missing|required|not implemented)", re.IGNORECASE),
    re.compile(r"\b(implement|add)\s+rate\s+limit", re.IGNORECASE),
    re.compile(r"\bunlimited\s+(requests|calls|api)", re.IGNORECASE),
)
_RESOURCE_MANAGEMENT_PATTERNS = (
    re.compile(r"\b(resource|memory|file)\s+leak\s+potential", re.IGNORECASE),
    re.compile(r"\bunclosed\s+(resource|file|connection)", re.IGNORECASE),
    re.compile(r"\b(close|cleanup|release)\s+(resource|file|connection)", re.IGNORECASE),
    re.compile(r"\bpotential\s+memory\s+leak", re.IGNORECASE),
    re.compile(r"\b(database|thread|socket|connection)\s+leak", re.IGNORECASE),
)
_OPEN_REDIRECT_PATTERNS = (
    re.compile(r"\b(open redirect|unvalidated redirect)\b", re.IGNORECASE),
    re.compile(r"\b(redirect.(attack|exploit|vulnerability))\b", re.IGNORECASE),
    re.compile(r"\b(malicious.redirect)\b", re.IGNORECASE),
)
_MEMORY_SAFETY_PATTERNS = (
    re.compile(r"\b(buffer overflow|stack overflow|heap overflow)\b", re.IGNORECASE),
    re.compile(r"\b(oob)\s+(read|write|access)\b", re.IGNORECASE),
    re.compile(r"\b(out.?of.?bounds?)\b", re.IGNORECASE),
    re.compile(r"\b(memory safety|memory corruption)\b", re.IGNORECASE),
    re.compile(r"\b(use.?after.?free|double.?free|null.?pointer.?dereference)\b", re.IGNORECASE),
    re.compile(r"\b(segmentation fault|segfault|memory violation)\b", re.IGNORECASE),
    re.compile(r"\b(bounds check|boundary check|array bounds)\b", re.IGNORECASE),
    re.compile(r"\b(integer overflow|integer underflow|integer conversion)\b", re.IGNORECASE),
    re.compile(r"\barbitrary.?(memory read|pointer dereference|memory address|memory pointer)\b", re.IGNORECASE),
)
_REGEX_INJECTION_PATTERNS = (
    re.compile(r"\b(regex|regular expression)\s+injection\b", re.IGNORECASE),
    re.compile(r"\b(regex|regular expression)\s+denial of service\b", re.IGNORECASE),
    re.compile(r"\b(regex|regular expression)\s+flooding\b", re.IGNORECASE),
)
_SSRF_PATTERN = re.compile(r"\b(ssrf|server\s+.?side\s+.?request\s+.?forgery)\b", re.IGNORECASE)

_PATTERN_GROUPS = (
    ("Generic DOS/resource exhaustion finding (low signal)", _DOS_PATTERNS),
    ("Generic rate limiting recommendation", _RATE_LIMIT_PATTERNS),
    ("Resource management finding (not a security vulnerability)", _RESOURCE_MANAGEMENT_PATTERNS),
    ("Open redirect vulnerability (not high impact)", _OPEN_REDIRECT_PATTERNS),
    ("Regex injection finding (not applicable)", _REGEX_INJECTION_PATTERNS),
)


def _read_resource(name: str) -> str:
    path = RESOURCE_ROOT / name
    return path.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def load_code_security_skill_resources() -> CodeSecuritySkillResources:
    return CodeSecuritySkillResources(
        audit_prompt=_read_resource("audit-prompt.md"),
        filtering_rules=_read_resource("filtering-rules.md"),
        hard_exclusion_patterns=_read_resource("hard-exclusion-patterns.md"),
    )


def detect_hard_exclusion(
    *,
    title: str,
    description: str,
    file_path: str,
) -> HardExclusionMatch | None:
    suffix = PurePosixPath(file_path.lower()).suffix
    combined = f"{title}\n{description}"

    if suffix == ".md":
        return HardExclusionMatch("Finding in Markdown documentation file")

    if suffix == ".html" and _SSRF_PATTERN.search(combined):
        return HardExclusionMatch("SSRF finding in HTML file (not applicable to client-side code)")

    if suffix not in CPP_EXTENSIONS:
        for pattern in _MEMORY_SAFETY_PATTERNS:
            if pattern.search(combined):
                return HardExclusionMatch("Memory safety finding in non-C/C++ code (not applicable)")

    for reason, patterns in _PATTERN_GROUPS:
        for pattern in patterns:
            if pattern.search(combined):
                return HardExclusionMatch(reason)

    return None


def apply_hard_exclusion_filters(
    findings: list[AuditFinding],
) -> tuple[list[AuditFinding], list[dict[str, Any]]]:
    kept: list[AuditFinding] = []
    excluded: list[dict[str, Any]] = []

    for finding in findings:
        match = detect_hard_exclusion(
            title=str(finding.get("title", "")),
            description=str(finding.get("description", "")),
            file_path=str(finding.get("file_path", "")),
        )
        if match is None:
            kept.append(finding)
            continue

        excluded.append(
            {
                "title": str(finding.get("title", "")),
                "file_path": str(finding.get("file_path", "")),
                "reason": match.reason,
            }
        )

    return kept, excluded
