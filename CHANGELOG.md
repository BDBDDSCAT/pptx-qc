# Changelog

## Unreleased

- Install `tomli` automatically on Python 3.10 so TOML configuration works on
  every supported Python version.
- Validate configuration types, numeric ranges, finite thresholds, and severity
  names before running rules. Invalid configuration now identifies the setting
  and returns exit status 2 instead of misleading QC or deck-read failures.
- Read embedded typefaces from the PowerPoint `p:font` declaration so embedded
  Windows and custom fonts no longer trigger false `PPTX101` / `PPTX103` findings.
- Interpret DrawingML autofit percentages correctly: an 80% font scale is reported
  as 80%, shrink-only settings are detected, and estimated heights remain positive
  when line spacing is reduced.

## 0.1.0 — 2026-09-20

First release.

- 19 rules covering content, fonts, layout geometry, embedded media and typography.
- `PPTX004` detects Simplified-Chinese-only characters leaking into Japanese decks and
  prints the Japanese equivalent (`实` → `実`).
- `PPTX101` / `PPTX102` catch Windows-only and Latin-only fonts that break rendering on
  macOS and Google Slides.
- `PPTX201` estimates text overflow from glyph-class widths and box insets (heuristic).
- Text, JSON and Markdown output; config via `.pptxqc.toml`; CI-friendly exit codes.
