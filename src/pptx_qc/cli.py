"""Command line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import Settings, find_config, load_settings
from .findings import RULES
from .report import exit_code, findings_for_stdout
from .runner import discover, lint_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pptx-qc",
        description=(
            "PowerPoint 納品前チェック / pre-delivery QC for .pptx decks. "
            "Detects dummy text, missing or unsafe fonts, estimated text overflow, "
            "simplified-Chinese contamination, low-resolution images and more."
        ),
    )
    parser.add_argument("targets", nargs="*", help=".pptx files or directories")
    parser.add_argument(
        "-f",
        "--format",
        choices=("text", "json", "markdown"),
        default="text",
        help="output format (default: text)",
    )
    parser.add_argument(
        "--fail-on",
        choices=("error", "warning", "none"),
        default=None,
        help="exit with status 1 when a finding of this severity exists (default: error)",
    )
    parser.add_argument("--min-font-size", type=float, default=None, help="flag runs below this pt")
    parser.add_argument("--min-dpi", type=float, default=None, help="flag images below this dpi")
    parser.add_argument(
        "--overflow-tolerance",
        type=float,
        default=None,
        help="estimated/available height ratio that counts as overflow (default 1.08)",
    )
    parser.add_argument(
        "--ignore",
        action="append",
        default=None,
        metavar="RULE[,RULE]",
        help="rule ids to silence, repeatable",
    )
    parser.add_argument("--config", type=Path, default=None, help="path to .pptxqc.toml")
    parser.add_argument("--no-config", action="store_true", help="ignore config files")
    parser.add_argument("--no-color", action="store_true", help="disable ANSI colours")
    parser.add_argument("--quiet", action="store_true", help="hide info-level findings")
    parser.add_argument("--list-rules", action="store_true", help="print the rule catalogue")
    parser.add_argument("--version", action="version", version=f"pptx-qc {__version__}")
    return parser


def _list_rules() -> str:
    lines = ["", "pptx-qc rules", ""]
    for rule_id, meta in sorted(RULES.items()):
        lines.append(f"  {rule_id}  [{meta.default_severity.value:7}] {meta.title}")
        lines.append(f"           {meta.description}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_rules:
        print(_list_rules())
        return 0

    if not args.targets:
        parser.error("no input files given (try: pptx-qc deck.pptx)")

    settings = Settings()
    if not args.no_config:
        config_path = args.config or find_config(Path(args.targets[0]))
        if config_path is not None:
            try:
                settings = load_settings(config_path)
            except Exception as exc:
                print(f"pptx-qc: config error in {config_path}: {exc}", file=sys.stderr)
                return 2

    extra_ignore: set[str] = set()
    for chunk in args.ignore or []:
        extra_ignore.update(part.strip() for part in chunk.split(",") if part.strip())

    settings = settings.with_overrides(
        min_font_size=args.min_font_size,
        min_image_dpi=args.min_dpi,
        overflow_tolerance=args.overflow_tolerance,
        fail_on=args.fail_on,
        show_info=False if args.quiet else None,
    )
    settings.ignore |= extra_ignore

    unknown = {r for r in settings.ignore if r not in RULES}
    if unknown:
        print(f"pptx-qc: unknown rule id(s): {', '.join(sorted(unknown))}", file=sys.stderr)

    files = discover(args.targets)
    if not files:
        print("pptx-qc: no .pptx files found", file=sys.stderr)
        return 2

    reports = []
    for path in files:
        try:
            reports.append(lint_file(path, settings))
        except Exception as exc:
            print(f"pptx-qc: failed to read {path}: {exc}", file=sys.stderr)
            return 2

    color = not args.no_color and args.format == "text" and sys.stdout.isatty()
    print(findings_for_stdout(args.format, reports, color=color))
    return exit_code(reports, settings.fail_on)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
