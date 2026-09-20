"""Output formatters: text, JSON, Markdown."""

from __future__ import annotations

import json
from pathlib import Path

from .findings import SEVERITY_ORDER, Report, Severity

_COLORS = {
    Severity.ERROR: "\033[31m",
    Severity.WARNING: "\033[33m",
    Severity.INFO: "\033[36m",
}
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"

_LABELS = {
    Severity.ERROR: "ERROR",
    Severity.WARNING: "WARN ",
    Severity.INFO: "INFO ",
}


def _paint(text: str, severity: Severity, color: bool) -> str:
    if not color:
        return text
    return f"{_COLORS[severity]}{text}{_RESET}"


def render_text(reports: list[Report], color: bool = True) -> str:
    lines: list[str] = []
    total = {s.value: 0 for s in SEVERITY_ORDER}

    for report in reports:
        counts = report.counts()
        for key, value in counts.items():
            total[key] += value

        lines.append("")
        lines.append(f"{_BOLD}{report.path}{_RESET}" if color else report.path)
        if not report.findings:
            ok = "\033[32m✓ 問題なし\033[0m" if color else "OK: no findings"
            lines.append(f"  {ok}")
            continue

        for finding in report.findings:
            tag = _paint(_LABELS[finding.severity], finding.severity, color)
            location = f" {_DIM}[{finding.location}]{_RESET}" if finding.location and color else (
                f" [{finding.location}]" if finding.location else ""
            )
            lines.append(f"  {tag} {finding.rule}{location} {finding.message}")
            if finding.hint:
                prefix = f"{_DIM}      → " if color else "      -> "
                suffix = _RESET if color else ""
                lines.append(f"{prefix}{finding.hint}{suffix}")

    summary = " / ".join(f"{v} {k}" for k, v in total.items())
    lines.append("")
    lines.append(f"{_BOLD}合計: {summary}{_RESET}" if color else f"total: {summary}")
    lines.append("")
    return "\n".join(lines)


def render_json(reports: list[Report]) -> str:
    total = {s.value: 0 for s in SEVERITY_ORDER}
    files = []
    for report in reports:
        counts = report.counts()
        for key, value in counts.items():
            total[key] += value
        files.append(
            {
                "path": report.path,
                "counts": counts,
                "findings": [f.to_dict() for f in report.findings],
            }
        )
    payload = {"version": 1, "summary": total, "files": files}
    return json.dumps(payload, ensure_ascii=False, indent=2)


def render_markdown(reports: list[Report]) -> str:
    total = {s.value: 0 for s in SEVERITY_ORDER}
    lines = ["# pptx-qc レポート", ""]
    for report in reports:
        counts = report.counts()
        for key, value in counts.items():
            total[key] += value
        lines.append(f"## {Path(report.path).name}")
        lines.append("")
        if not report.findings:
            lines.append("問題は検出されませんでした。")
            lines.append("")
            continue
        lines.append("| 重要度 | ルール | 位置 | 内容 |")
        lines.append("| --- | --- | --- | --- |")
        for finding in report.findings:
            message = finding.message.replace("|", "\\|")
            lines.append(
                f"| {finding.severity.value} | {finding.rule} | {finding.location or '-'} | {message} |"
            )
        lines.append("")
    summary = " / ".join(f"{v} {k}" for k, v in total.items())
    lines.append(f"**合計**: {summary}")
    lines.append("")
    return "\n".join(lines)


def findings_for_stdout(renderer: str, reports: list[Report], color: bool = True) -> str:
    if renderer == "json":
        return render_json(reports)
    if renderer == "markdown":
        return render_markdown(reports)
    return render_text(reports, color=color)


def worst_severity(reports: list[Report]) -> Severity | None:
    worst: Severity | None = None
    for report in reports:
        for finding in report.findings:
            if worst is None or finding.severity.rank > worst.rank:
                worst = finding.severity
    return worst


def exit_code(reports: list[Report], fail_on: str) -> int:
    threshold = fail_on.strip().lower()
    if threshold == "none":
        return 0
    needed = Severity.ERROR if threshold == "error" else Severity.WARNING
    for report in reports:
        for finding in report.findings:
            if finding.severity.rank >= needed.rank:
                return 1
    return 0
