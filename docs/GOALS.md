# Development goals

Updated: 2026-10-07

The next improvements prioritize reproducible QC accuracy and configuration
reliability before adding more rules. Findings should help a reviewer inspect a
deck without being distracted by errors in the linter itself.

## First iteration: font embedding and autofit accuracy

- [x] Read embedded font names from `p:embeddedFont/p:font/@typeface`.
- [x] Suppress `PPTX101` for the embedded Windows font while continuing to report
  Windows fonts when another family is embedded.
- [x] Suppress `PPTX103` when font embedding is declared.
- [x] Normalize `fontScale` and `lnSpcReduction` using DrawingML's 100000 = 100%
  representation, including shrink settings without a line-spacing reduction.
- [x] Verify saved and reloaded `.pptx` fixtures, full-size autofit, and positive
  estimated text height after shrinking.

Acceptance checks: `python -m pytest`, `ruff check .`, and `git diff --check`.
The implementation passes all 37 tests, including 10 new regression cases.
Font checks inspect the embedded-font declarations; they do not validate glyph
data or whether a recipient can use a particular embedded font.

## Next goals

1. **Support TOML configuration on every advertised Python version.**
   Python 3.10 falls back to `tomli`, but the package does not declare that
   dependency. Add a conditional dependency and verify loading the same config
   on Python 3.10 and 3.11+.
2. **Reject invalid configuration before running rules.**
   `load_settings` currently assigns numeric and severity values without checking
   them. Invalid thresholds can produce rule-execution warnings instead of a
   config error. Validate types, ranges, and severity values with actionable
   errors and exit status 2.
3. **Apply nearby configuration per deck in batch checks.**
   The CLI currently finds configuration next to only the first target. Resolve
   configuration per discovered file, while preserving explicit `--config`,
   `--no-config`, and CLI override precedence. Verify two directories with
   different thresholds in one invocation.
4. **Resolve inherited text formatting for font checks.**
   Many PowerPoint runs inherit their family or size from paragraph, placeholder,
   layout, master, or theme styles. The loader currently reads only run/paragraph
   font names and explicit run sizes. Add inheritance fixtures and effective
   formatting resolution so `PPTX101`, `PPTX102`, and `PPTX204` cover those runs.
