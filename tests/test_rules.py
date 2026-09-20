from __future__ import annotations

import pytest

from pptx_qc import Settings, lint_file
from pptx_qc.findings import Severity

from .conftest import INCH, new_deck, save, set_text, tiny_png  # noqa: F401


def rules_of(report) -> set[str]:
    return {f.rule for f in report.findings}


def check(deck, tmp_path, name="deck.pptx", settings=None) -> object:
    path = save(deck, tmp_path / name)
    return lint_file(path, settings or Settings())


def test_dummy_text_is_an_error(tmp_path):
    prs, slide = new_deck()
    set_text(slide.placeholders[1], "売上推移（ダミーテキスト）")
    report = check(prs, tmp_path)
    assert "PPTX001" in rules_of(report)
    assert any(f.severity is Severity.ERROR for f in report.findings)


def test_simplified_chinese_is_detected_with_japanese_equivalent(tmp_path):
    prs, slide = new_deck()
    set_text(slide.placeholders[1], "实現に向けた施策")
    report = check(prs, tmp_path)
    finding = next(f for f in report.findings if f.rule == "PPTX004")
    assert "实" in finding.message and "実" in finding.message


def test_pure_japanese_text_is_not_flagged_as_simplified(tmp_path):
    prs, slide = new_deck()
    set_text(slide.placeholders[1], "実現に向けた施策を実施します。")
    report = check(prs, tmp_path)
    assert "PPTX004" not in rules_of(report)


def test_windows_only_font_is_reported(tmp_path):
    prs, slide = new_deck()
    set_text(slide.placeholders[1], "日本語のテキスト", font="Meiryo")
    report = check(prs, tmp_path)
    assert "PPTX101" in rules_of(report)


def test_latin_font_on_japanese_text(tmp_path):
    prs, slide = new_deck()
    set_text(slide.placeholders[1], "日本語のテキスト", font="Arial")
    report = check(prs, tmp_path)
    assert "PPTX102" in rules_of(report)


def test_safe_font_is_not_reported(tmp_path):
    prs, slide = new_deck()
    set_text(slide.placeholders[1], "日本語のテキスト", font="Noto Sans JP")
    report = check(prs, tmp_path)
    assert "PPTX101" not in rules_of(report)
    assert "PPTX102" not in rules_of(report)


def test_empty_title_placeholder(tmp_path):
    prs, slide = new_deck()
    set_text(slide.placeholders[1], "本文だけ")
    report = check(prs, tmp_path)
    assert "PPTX002" in rules_of(report)


def test_halfwidth_katakana(tmp_path):
    prs, slide = new_deck()
    set_text(slide.placeholders[1], "担当 ﾃｽﾄ")
    report = check(prs, tmp_path)
    assert "PPTX104" in rules_of(report)


def test_small_font(tmp_path):
    prs, slide = new_deck()
    set_text(slide.placeholders[1], "脚注です", size=8)
    report = check(prs, tmp_path)
    assert "PPTX204" in rules_of(report)


def test_small_font_can_be_disabled(tmp_path):
    prs, slide = new_deck()
    set_text(slide.placeholders[1], "脚注です", size=8)
    report = check(prs, tmp_path, settings=Settings(min_font_size=0))
    assert "PPTX204" not in rules_of(report)


def test_overflow_is_estimated(tmp_path):
    prs, slide = new_deck()
    box = slide.shapes.add_textbox(INCH(0.5), INCH(0.5), INCH(1.0), INCH(0.3))
    box.text_frame.word_wrap = True
    box.text_frame.text = "日本語のテキストを非常に小さな箱に無理やり入れようとすると溢れます。"
    report = check(prs, tmp_path)
    assert "PPTX201" in rules_of(report)


def test_overflow_tolerance_can_be_raised(tmp_path):
    prs, slide = new_deck()
    box = slide.shapes.add_textbox(INCH(0.5), INCH(0.5), INCH(1.0), INCH(0.3))
    box.text_frame.word_wrap = True
    box.text_frame.text = "日本語のテキストを非常に小さな箱に無理やり入れようとすると溢れます。"
    report = check(prs, tmp_path, settings=Settings(overflow_tolerance=100.0))
    assert "PPTX201" not in rules_of(report)


def test_offslide_shape(tmp_path):
    prs, slide = new_deck()
    box = slide.shapes.add_textbox(INCH(11.5), INCH(0.2), INCH(2.0), INCH(0.5))
    box.text_frame.text = "はみ出し"
    report = check(prs, tmp_path)
    assert "PPTX203" in rules_of(report)


def test_low_resolution_image(tmp_path):
    prs, slide = new_deck()
    png = tiny_png(tmp_path / "tiny.png")
    slide.shapes.add_picture(str(png), INCH(1), INCH(1), width=INCH(6))
    report = check(prs, tmp_path)
    assert "PPTX401" in rules_of(report)


def test_clean_deck_reports_no_errors_or_warnings(tmp_path):
    prs, slide = new_deck()
    set_text(slide.shapes.title, "2026年度 事業計画")
    set_text(
        slide.placeholders[1],
        "既存事業の拡大と新規事業の立ち上げを並行して進めます。",
        font="Noto Sans JP",
        size=18,
    )
    report = check(prs, tmp_path)
    bad = [f for f in report.findings if f.severity in (Severity.ERROR, Severity.WARNING)]
    assert bad == [], [f"{f.rule} {f.message}" for f in bad]


def test_ignore_silences_a_rule(tmp_path):
    prs, slide = new_deck()
    set_text(slide.placeholders[1], "ダミーテキスト")
    report = check(prs, tmp_path, settings=Settings(ignore={"PPTX001"}))
    assert "PPTX001" not in rules_of(report)


def test_severity_can_be_overridden(tmp_path):
    prs, slide = new_deck()
    set_text(slide.placeholders[1], "ダミーテキスト")
    settings = Settings(severity_overrides={"PPTX001": "info"})
    report = check(prs, tmp_path, settings=settings)
    finding = next(f for f in report.findings if f.rule == "PPTX001")
    assert finding.severity is Severity.INFO


def test_custom_dummy_pattern(tmp_path):
    prs, slide = new_deck()
    set_text(slide.placeholders[1], "【仮】数値を後日反映")
    report = check(prs, tmp_path, settings=Settings(dummy_patterns=("【仮】",)))
    assert "PPTX001" in rules_of(report)


@pytest.mark.parametrize("text", ["売上は増加、コストは減少, 利益は増"])
def test_punctuation_mixing(tmp_path, text):
    prs, slide = new_deck()
    set_text(slide.placeholders[1], text)
    report = check(prs, tmp_path)
    assert "PPTX502" in rules_of(report)
