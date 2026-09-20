"""Finding model and rule registry."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .context import Context
    from .loader import Doc


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    @property
    def rank(self) -> int:
        return {"error": 2, "warning": 1, "info": 0}[self.value]

    @classmethod
    def parse(cls, value: str) -> Severity:
        try:
            return cls(value.strip().lower())
        except ValueError as exc:  # pragma: no cover - argparse guards this
            raise ValueError(f"unknown severity: {value!r}") from exc


SEVERITY_ORDER = (Severity.ERROR, Severity.WARNING, Severity.INFO)

_ICON = {Severity.ERROR: "x", Severity.WARNING: "!", Severity.INFO: "i"}


@dataclass
class Finding:
    """A single issue reported by a rule."""

    rule: str
    severity: Severity
    message: str
    slide: int | None = None
    shape: str | None = None
    hint: str | None = None

    @property
    def icon(self) -> str:
        return _ICON[self.severity]

    @property
    def location(self) -> str:
        parts: list[str] = []
        if self.slide is not None:
            parts.append(f"slide {self.slide}")
        if self.shape:
            parts.append(self.shape)
        return " / ".join(parts)

    def to_dict(self) -> dict:
        data: dict = {
            "rule": self.rule,
            "severity": self.severity.value,
            "message": self.message,
        }
        if self.slide is not None:
            data["slide"] = self.slide
        if self.shape:
            data["shape"] = self.shape
        if self.hint:
            data["hint"] = self.hint
        return data


@dataclass
class RuleMeta:
    id: str
    title: str
    default_severity: Severity
    description: str
    check: Callable[[Doc, Context], Iterable[Finding]] | None = None


RULES: dict[str, RuleMeta] = {}


def rule(id: str, title: str, severity: Severity, description: str):
    """Register a check function. Returns the function unchanged."""

    def decorator(func):
        if id in RULES:  # pragma: no cover - programming error
            raise RuntimeError(f"duplicate rule id: {id}")
        RULES[id] = RuleMeta(
            id=id,
            title=title,
            default_severity=severity,
            description=description,
            check=func,
        )
        return func

    return decorator


@dataclass
class Report:
    path: str
    findings: list[Finding] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        out = {s.value: 0 for s in SEVERITY_ORDER}
        for f in self.findings:
            out[f.severity.value] += 1
        return out

    @property
    def worst(self) -> Severity | None:
        if not self.findings:
            return None
        return min(self.findings, key=lambda f: -f.severity.rank).severity
