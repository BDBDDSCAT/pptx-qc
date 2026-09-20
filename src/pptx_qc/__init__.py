"""pptx-qc — pre-delivery QC linter for PowerPoint decks."""

from __future__ import annotations

__version__ = "0.1.0"

from . import rules as _rules  # noqa: E402,F401  (import registers the catalogue)
from .config import Settings  # noqa: E402
from .findings import RULES, Finding, Report, Severity  # noqa: E402
from .loader import Doc  # noqa: E402
from .runner import lint_file  # noqa: E402

__all__ = [
    "Doc",
    "Finding",
    "RULES",
    "Report",
    "Settings",
    "Severity",
    "__version__",
    "lint_file",
]
