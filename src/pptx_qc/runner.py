"""Rule execution."""

from __future__ import annotations

from pathlib import Path

from .config import Settings
from .findings import RULES, Finding, Report, Severity
from .loader import Doc


def lint_file(path: str | Path, settings: Settings) -> Report:
    """Run every enabled rule against one deck."""
    doc = Doc(path)
    report = Report(path=str(path))

    for rule_id, meta in RULES.items():
        if rule_id in settings.ignore or meta.check is None:
            continue
        try:
            produced = list(meta.check(doc, settings))
        except Exception as exc:  # a broken rule must not kill the run
            report.findings.append(
                Finding(
                    rule=rule_id,
                    severity=Severity.WARNING,
                    message=f"ルール実行に失敗しました: {type(exc).__name__}: {exc}",
                    hint="pptx-qc の不具合です。Issue で報告してください。",
                )
            )
            continue

        override = settings.severity_overrides.get(rule_id)
        for finding in produced:
            if override:
                finding.severity = Severity.parse(str(override))
            if finding.severity is Severity.INFO and not settings.show_info:
                continue
            report.findings.append(finding)

    report.findings.sort(key=lambda f: (f.slide or 0, f.severity.rank * -1, f.rule))
    return report


def discover(targets: list[str]) -> list[Path]:
    """Expand files and directories into a sorted list of .pptx paths."""
    out: list[Path] = []
    for target in targets:
        path = Path(target)
        if path.is_dir():
            out.extend(sorted(path.glob("**/*.pptx")))
        elif path.is_file():
            out.append(path)
    # de-duplicate, keep order
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in out:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)
    return unique
