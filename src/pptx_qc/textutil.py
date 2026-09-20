"""Text helpers: CJK detection, glyph width estimation, simplified-Chinese map."""

from __future__ import annotations

import unicodedata

# --- character classes -------------------------------------------------------


def is_kana(ch: str) -> bool:
    o = ord(ch)
    return 0x3040 <= o <= 0x30FF or 0x31F0 <= o <= 0x31FF or 0xFF66 <= o <= 0xFF9F


def is_ideograph(ch: str) -> bool:
    o = ord(ch)
    return (
        0x3400 <= o <= 0x4DBF
        or 0x4E00 <= o <= 0x9FFF
        or 0xF900 <= o <= 0xFAFF
        or 0x20000 <= o <= 0x2FA1F
    )


def is_wide(ch: str) -> bool:
    """True when the character occupies a full-width cell."""
    if is_kana(ch) or is_ideograph(ch):
        return True
    o = ord(ch)
    if 0x3000 <= o <= 0x303F:  # CJK punctuation
        return True
    if 0xFF01 <= o <= 0xFF60:  # fullwidth forms
        return True
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return True
    return False


def has_cjk(text: str) -> bool:
    return any(is_ideograph(c) or is_kana(c) for c in text)


def is_halfwidth_katakana(ch: str) -> bool:
    return 0xFF66 <= ord(ch) <= 0xFF9F or ord(ch) == 0xFF9E or ord(ch) == 0xFF9F


def has_halfwidth_katakana(text: str) -> bool:
    return any(0xFF66 <= ord(c) <= 0xFF9F for c in text)


def is_fullwidth_alnum(ch: str) -> bool:
    o = ord(ch)
    return 0xFF10 <= o <= 0xFF19 or 0xFF21 <= o <= 0xFF3A or 0xFF41 <= o <= 0xFF5A


# --- width estimation (used for the overflow heuristic) ---------------------

_NARROW = set(" .,:;'\"!|()[]/\\-")


def char_width(ch: str) -> float:
    """Very rough advance width in em units."""
    if ch == "\t":
        return 2.0
    if is_wide(ch):
        return 1.0
    if ch in _NARROW:
        return 0.31
    if ch.isdigit():
        return 0.52
    if ch.isupper():
        return 0.62
    return 0.53


def text_width_em(text: str) -> float:
    return sum(char_width(c) for c in text)


# --- simplified Chinese detection -------------------------------------------
#
# Curated, deliberately conservative: every key is a character that is *not*
# used in Japanese orthography, so a hit is almost certainly a leak from a
# Simplified-Chinese source document. Values give the Japanese equivalent for
# a helpful message.

_PAIR_BLOB = """
实実 关関 开開 长長 见見 电電 员員 术術 报報 应応 问問 题題 说説 语語 发発 经経 营営 图図
标標 华華 义義 务務 车車 东東 贝貝 风風 马馬 鸟鳥 鱼魚 龙龍 书書 页頁 齐斉 齿歯 龟亀 头頭
买買 卖売 单単 张張 总総 结結 级級 给給 红紅 纪紀 约約 钢鋼 钱銭 银銀 钟鐘 铁鉄 对対 备備
复復 杂雑 权権 欢歓 汉漢 汤湯 测測 济済 满満 无無 聪聡 听聴 职職 连連 脑脳 计計 订訂 议議
论論 设設 访訪 话話 请請 读読 谁誰 调調 谈談 谢謝 贡貢 财財 货貨 质質 购購 贵貴 费費 赢贏
赞賛 轻軽 转転 轮輪 软軟 边辺 过過 远遠 运運 还還 这這 进進 迟遅 选選 递逓 邮郵 郑鄭 释釈
镇鎮 间間 闻聞 阅閲 队隊 阳陽 陆陸 陈陳 险険 难難 顺順 预預 领領 验験 鲜鮮 视視 规規 觉覚
顾顧 项項 额額 飞飛 饭飯 饮飲 饰飾 馆館 驾駕 骑騎 闹鬧 鸡鶏 鸣鳴 鹅鵞 变変 从從 众衆 优優
传伝 伟偉 伤傷 价価 为為 专専 业業 两両 个個 丰豊 临臨 丽麗 举挙 乌烏 乐楽 习習 乡郷 亚亜
产産 亲親 亿億 仅僅 仓倉 仪儀 们們 伪偽 坚堅 坛壇 处処 够夠 夹夾 夺奪 奋奮 妇婦 宁寧 宫宮
宾賓 导導 岁歳 岛島 帅帥 师師 带帯 帮幫 广広 归帰 录録 彻徹 忆憶 怀懐 态態 恶悪 战戦 户戸
扑撲 执執 扩拡 护護 拟擬 拥擁 择択 挂掛 换換 据拠 损損 摆擺 摄摂 敌敵 时時 显顕 机機 极極
构構 树樹 样様 检検 楼楼 杀殺 铁鉄 针針 钢鋼 锁鎖 锅鍋 镜鏡 长長 门門 问問 闲閑 间間 阅閲
"""


def _build_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for token in _PAIR_BLOB.split():
        if len(token) != 2:
            continue
        simplified, japanese = token[0], token[1]
        if simplified == japanese:
            continue
        mapping[simplified] = japanese
    return mapping


SIMPLIFIED_TO_JAPANESE: dict[str, str] = _build_map()


def find_simplified_chars(text: str) -> list[tuple[str, str]]:
    """Return (simplified, japanese_equivalent) pairs found in *text*."""
    seen: dict[str, str] = {}
    for ch in text:
        if ch in SIMPLIFIED_TO_JAPANESE:
            seen.setdefault(ch, SIMPLIFIED_TO_JAPANESE[ch])
    return list(seen.items())
