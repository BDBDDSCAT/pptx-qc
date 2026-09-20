# pptx-qc

Pre-delivery QC linter for PowerPoint decks. Catches the things that make a client
send a deliverable back: unreplaced placeholder text, fonts that only exist on the
author's machine, text that does not fit its box, Simplified-Chinese characters that
leaked into a Japanese deck, and low-resolution images.

```
$ pptx-qc examples/demo_bad.pptx

examples/demo_bad.pptx
  ERROR PPTX001 [slide 1 / Title 1] ダミーテキストの疑い: 「株式会社サンプル」
  ERROR PPTX001 [slide 1 / Content Placeholder 2] ダミーテキストの疑い: 「ダミーテキスト」
  ERROR PPTX004 [slide 1 / Content Placeholder 2] 簡体字「实」が混入（日本語表記は「実」）
  WARN  PPTX101 [slide 1 / Content Placeholder 2] Windows 専用フォント「Meiryo」が未埋め込み（他 1 箇所）
  WARN  PPTX002 [slide 2 / Title 1] 空のプレースホルダが残っています
  WARN  PPTX102 [slide 2 / Content Placeholder 2] 日本語テキストに欧文フォント「Arial」を指定
  WARN  PPTX104 [slide 2 / Content Placeholder 2] 半角カナを検出: 「担当: ﾃｽﾄﾀﾛｳ（ABC123）」
  INFO  PPTX204 [slide 2 / Content Placeholder 2] 8pt の文字（基準 10pt 未満）
  WARN  PPTX201 [slide 3 / TextBox 1] テキストが収まらない可能性: 必要 約505pt / 領域 約14pt（35.1倍）
  WARN  PPTX203 [slide 3 / TextBox 4] スライド外（またはほぼ外）に配置されています
  WARN  PPTX401 [slide 3 / Picture 3] 画像の実効解像度が約 10dpi（基準 120dpi 未満）
  INFO  PPTX003 [slide 3] タイトルプレースホルダがありません

total: 4 error / 8 warning / 5 info
```

Built by someone who ships slide decks for Japanese clients, after being bitten by
every one of these. It is not a prettifier and it is not an AI rewriter — it is the
checklist you run **before you press send**, automated.

Try it on the shipped sample without installing anything:

```bash
python examples/make_demo.py     # writes examples/demo_bad.pptx
pptx-qc examples/demo_bad.pptx
```

## Install

```bash
pip install pptx-qc
```

Or from source:

```bash
git clone https://github.com/BDBDDSCAT/pptx-qc
cd pptx-qc && pip install -e ".[dev]"
```

Repository: <https://github.com/BDBDDSCAT/pptx-qc>

## Usage

```bash
pptx-qc deck.pptx                     # check one file
pptx-qc slides/                       # check every .pptx under a directory
pptx-qc deck.pptx --fail-on warning   # strict: non-zero on warnings too
pptx-qc deck.pptx --format json       # machine readable
pptx-qc deck.pptx --format markdown   # paste straight into a delivery note
pptx-qc --list-rules                  # rule catalogue
```

Exit codes: `0` clean, `1` findings at or above `--fail-on` (default `error`),
`2` usage or read error.

## Rules

| ID | Severity | What it catches |
| --- | --- | --- |
| `PPTX001` | error | Dummy / placeholder text left in (`ダミー`, `TBD`, `サンプル株式会社`, `lorem ipsum`, `〇〇株式会社`, …) |
| `PPTX002` | warning | Empty title/body placeholders ("Click to edit" in edit mode) |
| `PPTX003` | info | Slide has no title placeholder (outline view, PDF bookmarks, screen readers) |
| `PPTX004` | error | Simplified-Chinese-only characters in Japanese text (`实`→`実`, `关`→`関`, …) with the JP equivalent |
| `PPTX101` | warning | Windows-only fonts that are not embedded (Meiryo, Yu Gothic, ＭＳ Ｐゴシック, Segoe UI, …) |
| `PPTX102` | warning | Latin-only family applied to Japanese text (glyphs and metrics shift per device) |
| `PPTX103` | info | Non-universal fonts used but nothing embedded |
| `PPTX104` | warning | Half-width katakana |
| `PPTX105` | info | More font families than the configured maximum |
| `PPTX201` | warning | Estimated text overflow (required height vs. shape height) |
| `PPTX202` | info | "Shrink text on overflow" already applied (font scale / line-spacing reduction) |
| `PPTX203` | warning | Shape placed outside the slide area (clipped on PDF export) |
| `PPTX204` | info | Runs below the minimum font size |
| `PPTX205` | info | Slide masters disagree on theme fonts (slides pasted from another deck) |
| `PPTX401` | warning | Effective image resolution below the dpi threshold |
| `PPTX402` | info | The same image stored several times |
| `PPTX403` | info | Image parts that nothing references any more |
| `PPTX501` | info | Full-width and half-width alphanumerics mixed, double spaces |
| `PPTX502` | info | Japanese and Latin punctuation mixed (`、` vs `,`, `。` vs `.`) |

## Configuration

`pptx-qc` reads `.pptxqc.toml` from the target file's directory (or the current
directory). CLI flags win over the file.

```toml
[pptx-qc]
min_font_size = 12.0        # 提案資料は本文12pt以上
min_image_dpi = 150.0
overflow_tolerance = 1.08
max_font_families = 4
fail_on = "warning"

ignore = ["PPTX003", "PPTX501"]
severity = { PPTX205 = "warning" }

# extra placeholder patterns for your own workflow
dummy_patterns = ["【仮】", "XXX株式会社", "[会社名]"]
```

## CI

```yaml
- run: pip install pptx-qc
- run: pptx-qc slides/ --fail-on warning --format markdown > pptx-qc-report.md
```

## Using it as a library

```python
from pptx_qc import Settings, lint_file

report = lint_file("deck.pptx", Settings(min_font_size=12))
for finding in report.findings:
    print(finding.severity.value, finding.rule, finding.location, finding.message)
```

## Roadmap / 実装したいもの

- [ ] 用語ゆれチェック（「顧客」と「お客様」が混在、など）
- [ ] SmartArt・グラフ・WordArt 内の文字を検査対象に
- [ ] 配色数のチェック（主色 3 + 補助色 2 以内）
- [ ] `--fix` による軽微な自動修正（半角カナ → 全角カナ、連続スペース）
- [ ] Google スライド取り込み時の崩れ予測

Issue で要望・誤検知の報告を歓迎します。

## Limitations

`PPTX201` (overflow) is a heuristic: it estimates glyph advance widths from
character classes and compares the required height against the shape box. It
deliberately errs toward reporting, and it cannot see through exotic text effects,
rotated text or SmartArt. Treat it as "look here", not as ground truth.

Text inside SmartArt, charts and WordArt is not inspected.

## 日本語

.pptx の**納品前チェック**をコマンド 1 つで回すツールです。

- ダミーテキスト・仮置き文字の残り（`ダミー` / `TBD` / `〇〇株式会社` …）
- **Windows 専用フォントの未埋め込み**（メイリオ・游ゴシック・ＭＳ Ｐゴシック など）→ Mac / Google スライドで崩れる原因
- **簡体字の混入**（`实` → `実`、`关` → `関`）を日本語表記つきで指摘
- テキストのはみ出し推定、スライド外配置、半角カナ、全角/半角の混在、約物の不統一
- 画像の実効解像度不足、重複埋め込み、未使用画像

```bash
pptx-qc 提案資料_v3.pptx
pptx-qc 提案資料_v3.pptx --format markdown > チェック結果.md   # 納品説明に添付
```

設定は `.pptxqc.toml`、CI では `--fail-on warning` で自動ゲートにできます。

## License

MIT
