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
