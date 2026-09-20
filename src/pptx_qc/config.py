"""Configuration: defaults, TOML loading, CLI overrides."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field, replace
from pathlib import Path

if sys.version_info >= (3, 11):  # pragma: no cover - trivial
    import tomllib
else:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:  # pragma: no cover
        tomllib = None  # type: ignore[assignment]

CONFIG_FILENAMES = (".pptxqc.toml", "pptxqc.toml")

#: Text that almost always means "I forgot to replace the placeholder".
DEFAULT_DUMMY_PATTERNS: tuple[str, ...] = (
    "クリックして編集",
    "クリックしてテキスト",
    "Click to edit",
    "此处输入",
    "ダミー",
    "ダミーテキスト",
    "サンプルテキスト",
    "サンプルデータ",
    "テストテキスト",
    "テキストを入力",
    "あいうえお",
    "かきくけこ",
    "lorem ipsum",
    "Lorem ipsum",
    "dummy text",
    "sample text",
    "TODO",
    "TBD",
    "FIXME",
    "XXXX",
    "〇〇株式会社",
    "株式会社サンプル",
    "サンプル株式会社",
    "山田太郎",
    "鈴木太郎",
    "テスト太郎",
    "担当者名",
    "会社名を入力",
    "ここに説明",
    "【要確認】",
    "［要確認］",
    "[要確認]",
    "（仮）",
    "(仮)",
    "仮置き",
    "仮データ",
)

#: Fonts that only ship with Windows and are therefore not safe to rely on
#: when the recipient opens the deck on macOS or Google Slides.
WINDOWS_ONLY_FONTS: frozenset[str] = frozenset(
    f.lower()
    for f in (
        "Meiryo",
        "Meiryo UI",
        "ＭＳ Ｐゴシック",
        "ＭＳ ゴシック",
        "MS PGothic",
        "MS Gothic",
        "MS Mincho",
        "MS PMincho",
        "MS UI Gothic",
        "游ゴシック",
        "游明朝",
        "Yu Gothic",
        "Yu Gothic UI",
        "Yu Mincho",
        "Yu Mincho Light",
        "BIZ UDPGothic",
        "BIZ UDPMincho",
        "HGPゴシックM",
        "HG創英角ゴシックUB",
        "HG丸ｺﾞｼｯｸM-PRO",
        "UD デジタル 教科書体 NP-R",
        "Segoe UI",
        "Segoe UI Semibold",
        "Malgun Gothic",
        "SimSun",
        "Microsoft YaHei",
        "PMingLiU",
        "FangSong",
        "SimHei",
        "Segoe Print",
        "Candara",
        "Constantia",
        "Corbel",
        "Franklin Gothic Book",
        "Candara",
        "Simplified Arabic",
    )
)

#: Latin-oriented families. Applying them to Japanese text makes the metrics
#: and the glyph shapes fall back to whatever the opening device picks.
LATIN_ONLY_FONTS: frozenset[str] = frozenset(
    f.lower()
    for f in (
        "Arial",
        "Helvetica",
        "Calibri",
        "Aptos",
        "Aptos Display",
        "Times New Roman",
        "Verdana",
        "Tahoma",
        "Georgia",
        "Garamond",
        "Cambria",
        "Trebuchet MS",
        "Consolas",
        "Courier New",
        "Impact",
        "Century Gothic",
        "Comic Sans MS",
        "Futura",
        "Gill Sans",
        "Optima",
        "Palatino",
        "Rockwell",
        "Inter",
        "Roboto",
        "Lato",
        "Open Sans",
        "Montserrat",
        "Poppins",
        "Nunito",
        "Source Sans Pro",
    )
)

#: Families considered universally available on Win/macOS/Linux/Google Slides.
SAFE_FONTS: frozenset[str] = frozenset(
    f.lower()
    for f in (
        "Arial",
        "Helvetica",
        "Helvetica Neue",
        "Times New Roman",
        "Courier New",
        "Verdana",
        "Georgia",
        "Calibri",
        "Roboto",
        "Noto Sans",
        "Noto Sans JP",
        "Noto Sans CJK JP",
        "Noto Serif JP",
        "源ノ角ゴシック",
        "Source Han Sans",
        "Hiragino Sans",
        "ヒラギノ角ゴシック",
        "Hiragino Kaku Gothic ProN",
        "Hiragino Mincho ProN",
        "メイリオ",
        "Meiryo",
        "Yu Gothic",
        "游ゴシック",
        "DejaVu Sans",
        "Liberation Sans",
        "Arial Unicode MS",
        "IPAexGothic",
        "IPAGothic",
        "IPAPGothic",
        "TakaoGothic",
    )
)


@dataclass
class Settings:
    #: rule ids to silence
    ignore: set[str] = field(default_factory=set)
    #: rule id -> severity name
    severity_overrides: dict[str, str] = field(default_factory=dict)
    #: report runs smaller than this (pt)
    min_font_size: float = 10.0
    #: warn when an image is displayed below this effective dpi
    min_image_dpi: float = 120.0
    #: estimated_required / available above this ratio is reported as overflow
    overflow_tolerance: float = 1.08
    #: report when more distinct font families than this are used
    max_font_families: int = 5
    #: extra placeholder patterns
    dummy_patterns: tuple[str, ...] = ()
    #: exit non-zero on: "error" | "warning" | "none"
    fail_on: str = "error"
    #: print every finding, including info
    show_info: bool = True

    def all_dummy_patterns(self) -> tuple[str, ...]:
        return DEFAULT_DUMMY_PATTERNS + tuple(self.dummy_patterns)

    def with_overrides(self, **kwargs) -> Settings:
        clean = {k: v for k, v in kwargs.items() if v is not None}
        return replace(self, **clean)


def find_config(start: Path | None = None) -> Path | None:
    """Look for a config file next to the target, then in the cwd."""
    candidates: list[Path] = []
    if start is not None:
        base = start if start.is_dir() else start.parent
        candidates.extend(base / name for name in CONFIG_FILENAMES)
    here = Path.cwd()
    candidates.extend(here / name for name in CONFIG_FILENAMES)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def load_settings(path: Path | None) -> Settings:
    if path is None:
        return Settings()
    if tomllib is None:  # pragma: no cover
        raise RuntimeError("TOML support requires Python 3.11+ or the 'tomli' package")
    with open(path, "rb") as fh:
        raw = tomllib.load(fh)

    data = raw.get("pptx-qc", raw)
    settings = Settings()
    if "ignore" in data:
        settings.ignore = {str(x) for x in data["ignore"]}
    if "severity" in data:
        settings.severity_overrides = {str(k): str(v) for k, v in data["severity"].items()}
    if "dummy_patterns" in data:
        settings.dummy_patterns = tuple(str(x) for x in data["dummy_patterns"])
    for key in (
        "min_font_size",
        "min_image_dpi",
        "overflow_tolerance",
        "max_font_families",
        "fail_on",
        "show_info",
    ):
        if key in data:
            setattr(settings, key, data[key])
    return settings
