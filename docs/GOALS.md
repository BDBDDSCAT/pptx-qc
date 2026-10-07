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
At completion of this iteration, all 37 tests passed, including 10 new regression cases.
Font checks inspect the embedded-font declarations; they do not validate glyph
data or whether a recipient can use a particular embedded font.

## Second iteration: configuration reliability

- [x] Install `tomli` only on Python versions below 3.11, with the conditional
  dependency exercised through a fresh Python 3.10 installation.
- [x] Validate table/list shapes, boolean values, finite numeric thresholds,
  non-negative limits, positive overflow tolerance, and recognized severity names.
- [x] Report the offending setting and exit with status 2 before linting when
  a configuration value is invalid, including NaN and infinity.
- [x] Preserve root-level and `[pptx-qc]` configuration, zero font/image thresholds,
  CLI override precedence, merged ignores, and `--no-config` behavior.
- [x] Exercise valid configuration and error handling on Python 3.10 and 3.12.

Acceptance checks: 75 tests pass on both Python 3.10.21 (`tomli`) and Python 3.12
(`tomllib`); `ruff check .` and `git diff --check` pass. This iteration adds 38
configuration and CLI cases. Validation applies to loaded TOML configuration;
library callers still construct `Settings` directly.

## Next goals

1. **Apply nearby configuration per deck in batch checks.**
   The CLI currently finds configuration next to only the first target. Resolve
   configuration per discovered file, while preserving explicit `--config`,
   `--no-config`, and CLI override precedence. Verify two directories with
   different thresholds in one invocation.
2. **Resolve inherited text formatting for font checks.**
   Many PowerPoint runs inherit their family or size from paragraph, placeholder,
   layout, master, or theme styles. The loader currently reads only run/paragraph
   font names and explicit run sizes. Add inheritance fixtures and effective
   formatting resolution so `PPTX101`, `PPTX102`, and `PPTX204` cover those runs.
