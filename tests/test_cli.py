from __future__ import annotations

import json

import pytest

from pptx_qc.cli import main

from .conftest import new_deck, save, set_text


@pytest.fixture()
def bad_deck(tmp_path):
    prs, slide = new_deck()
    set_text(slide.placeholders[1], "ダミーテキストです")
    return save(prs, tmp_path / "bad.pptx")


def test_text_output_and_exit_code(bad_deck, capsys):
    code = main([str(bad_deck), "--no-color"])
    out = capsys.readouterr().out
    assert code == 1
    assert "PPTX001" in out


def test_fail_on_none_returns_zero(bad_deck):
    assert main([str(bad_deck), "--fail-on", "none", "--no-color"]) == 0


def test_json_output_is_parseable(bad_deck, capsys):
    main([str(bad_deck), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["error"] >= 1
    assert payload["files"][0]["findings"]


def test_markdown_output_has_table(bad_deck, capsys):
    main([str(bad_deck), "--format", "markdown"])
    out = capsys.readouterr().out
    assert "| 重要度 | ルール |" in out


def test_ignore_flag(bad_deck, capsys):
    main([str(bad_deck), "--ignore", "PPTX001", "--no-color"])
    assert "PPTX001" not in capsys.readouterr().out


def test_list_rules(capsys):
    assert main(["--list-rules"]) == 0
    assert "PPTX001" in capsys.readouterr().out


def test_missing_target():
    with pytest.raises(SystemExit):
        main([])


def test_directory_discovery(tmp_path, bad_deck):
    # bad_deck lives inside tmp_path
    assert main([str(tmp_path), "--no-color"]) == 1


@pytest.mark.parametrize(
    ("content", "field"),
    [
        ('min_font_size = "small"', "min_font_size"),
        ("min_image_dpi = nan", "min_image_dpi"),
        ('severity = { PPTX001 = "warn" }', "severity.PPTX001"),
        ('fail_on = "erorr"', "fail_on"),
        ('ignore = "PPTX001"', "ignore"),
        ('dummy_patterns = [""]', "dummy_patterns"),
    ],
)
def test_invalid_config_returns_config_error(bad_deck, tmp_path, capsys, content, field):
    path = tmp_path / "config.toml"
    path.write_text("[pptx-qc]\n" + content, encoding="utf-8")
    assert main([str(bad_deck), "--config", str(path)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert f"config error in {path}:" in captured.err
    assert field in captured.err


def test_no_config_bypasses_invalid_nearby_config(bad_deck, tmp_path, capsys):
    (tmp_path / ".pptxqc.toml").write_text('min_font_size = "small"', encoding="utf-8")
    assert main([str(bad_deck), "--no-config", "--format", "json"]) == 1
    captured = capsys.readouterr()
    assert json.loads(captured.out)["summary"]["error"] >= 1
    assert captured.err == ""


def test_cli_overrides_valid_config_and_merges_ignore(bad_deck, tmp_path, capsys):
    prs, slide = new_deck()
    set_text(slide.placeholders[1], "Footnote", size=8)
    small_deck = save(prs, tmp_path / "small.pptx")
    config = tmp_path / "config.toml"
    config.write_text(
        '[pptx-qc]\nfail_on = "none"\nmin_font_size = 1\nignore = ["PPTX002"]\n', encoding="utf-8"
    )
    assert main(
        [
            str(bad_deck), str(small_deck), "--config", str(config), "--fail-on", "warning",
            "--min-font-size", "10", "--ignore", "PPTX001", "--format", "json",
        ]
    ) == 0
    payload = json.loads(capsys.readouterr().out)
    findings = [f for file in payload["files"] for f in file["findings"]]
    assert any(f["rule"] == "PPTX204" for f in findings)
    assert not any(f["rule"] in {"PPTX001", "PPTX002"} for f in findings)
    assert main([str(bad_deck), "--config", str(config), "--fail-on", "error", "--quiet", "--format", "json"]) == 1
    assert json.loads(capsys.readouterr().out)["summary"]["info"] == 0
