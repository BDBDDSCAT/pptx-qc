from __future__ import annotations

import pytest

from pptx_qc.config import Settings, load_settings


@pytest.mark.parametrize("section", ["", "[pptx-qc]\n"])
def test_load_valid_settings(tmp_path, section):
    path = tmp_path / "config.toml"
    path.write_text(
        section
        + 'ignore = ["PPTX003", "PPTX501"]\n'
        'severity = { PPTX205 = " Warning " }\n'
        'dummy_patterns = ["【仮】", "[会社名]"]\n'
        "min_font_size = 12\n"
        "min_image_dpi = 150.0\n"
        "overflow_tolerance = 1.08\n"
        "max_font_families = 4\n"
        'fail_on = " NONE "\n'
        "show_info = false\n",
        encoding="utf-8",
    )
    assert load_settings(path) == Settings(
        ignore={"PPTX003", "PPTX501"},
        severity_overrides={"PPTX205": "warning"},
        dummy_patterns=("【仮】", "[会社名]"),
        min_font_size=12,
        min_image_dpi=150,
        overflow_tolerance=1.08,
        max_font_families=4,
        fail_on="none",
        show_info=False,
    )


def test_zero_thresholds_and_empty_lists_are_valid(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(
        "[pptx-qc]\nmin_font_size = 0\nmin_image_dpi = 0\nmax_font_families = 0\n"
        "ignore = []\ndummy_patterns = []\nseverity = {}\n",
        encoding="utf-8",
    )
    settings = load_settings(path)
    assert settings.min_font_size == 0
    assert settings.min_image_dpi == 0
    assert settings.max_font_families == 0
    assert settings.ignore == set()
    assert settings.dummy_patterns == ()
    assert settings.severity_overrides == {}


@pytest.mark.parametrize(
    ("content", "field"),
    [
        ('pptx-qc = "disabled"', "pptx-qc"),
        ('min_font_size = "small"', "min_font_size"),
        ("min_font_size = true", "min_font_size"),
        ("min_font_size = -1", "min_font_size"),
        ("min_font_size = nan", "min_font_size"),
        ("min_image_dpi = -1", "min_image_dpi"),
        ("min_image_dpi = inf", "min_image_dpi"),
        ("overflow_tolerance = 0", "overflow_tolerance"),
        ("overflow_tolerance = -1", "overflow_tolerance"),
        ("overflow_tolerance = nan", "overflow_tolerance"),
        ("max_font_families = -1", "max_font_families"),
        ("max_font_families = 1.5", "max_font_families"),
        ("max_font_families = true", "max_font_families"),
        ('show_info = "false"', "show_info"),
        ('fail_on = "erorr"', "fail_on"),
        ("fail_on = false", "fail_on"),
        ('ignore = "PPTX001"', "ignore"),
        ("ignore = [1]", "ignore"),
        ('dummy_patterns = "[会社名]"', "dummy_patterns"),
        ("dummy_patterns = [true]", "dummy_patterns"),
        ('dummy_patterns = [""]', "dummy_patterns"),
        ('dummy_patterns = ["   "]', "dummy_patterns"),
        ('severity = ["warning"]', "severity"),
        ('severity = { PPTX001 = "warn" }', "severity.PPTX001"),
        ("severity = { PPTX001 = 1 }", "severity.PPTX001"),
    ],
)
def test_invalid_settings_name_the_offending_field(tmp_path, content, field):
    path = tmp_path / "config.toml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match=field):
        load_settings(path)


def test_unknown_settings_remain_ignored(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("[pptx-qc]\nfuture_option = true\n", encoding="utf-8")
    assert load_settings(path) == Settings()


def test_no_config_returns_defaults():
    assert load_settings(None) == Settings()
