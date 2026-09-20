# Changelog

## 0.1.0 — 2026-09-20

First release.

- 19 rules covering content, fonts, layout geometry, embedded media and typography.
- `PPTX004` detects Simplified-Chinese-only characters leaking into Japanese decks and
  prints the Japanese equivalent (`实` → `実`).
- `PPTX101` / `PPTX102` catch Windows-only and Latin-only fonts that break rendering on
  macOS and Google Slides.
- `PPTX201` estimates text overflow from glyph-class widths and box insets (heuristic).
- Text, JSON and Markdown output; config via `.pptxqc.toml`; CI-friendly exit codes.
