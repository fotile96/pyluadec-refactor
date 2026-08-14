"""fallback 文本的可读性 -- M7 任务 5（spec §4）。

红线的第二次作用域修订（human partner 批准 2026-08-15，作为独立决定）：
可逆 UTF-8 呈现判定从 `emit/lua.py::_str_lit`（M5 task 7 唯一落点）扩展到
`structure/fallback.py::str_lit`。判定本体单一归属在 `structure/fallback.py`，
`emit/lua.py::_str_lit` 是薄委托（`emit → structure.fallback` 的 import 方向在
M5 就已存在——escape 回退——沿用它不产生环）。

机器检验与第一次修订同形：两种拼写编译出相同常量，认证裁决不变
（`tests/test_emit_readability.py` 的裁决不变性测试对新拼写继续成立；
`run_corpus.py` 重生成后台账逐字节不变，见任务提交）。
"""
from __future__ import annotations

from pathlib import Path

from pyluadec import ingest, oracle
from pyluadec.structure.fallback import emit_chunk

_JP = "【直哉】"                       # the M4-report readability exemplar
_LONE_CONT = b"\xff\xfe"              # not UTF-8 in any position
_TRUNCTED = b"\xe3\x81"               # first two bytes of a 3-byte char


def _fallback_text(source: bytes) -> bytes:
    root = ingest.load_bytes(oracle.compile_source(source, strip=True))
    return emit_chunk(root)


def test_fallback_prints_reversible_utf8_raw():
    out = _fallback_text('f("【直哉】")\n'.encode())
    assert "【直哉】".encode() in out
    assert b"\\227\\128\\144" not in out


def test_fallback_still_escapes_non_utf8():
    # A constant that is not valid UTF-8 keeps the decimal escape: the
    # judgment is reversible-UTF-8-only (evidence for this path is synthetic
    # by construction -- the corpus measured 0 non-UTF-8 of 49063).
    from pyluadec.structure import fallback as fb

    assert fb.str_lit(_LONE_CONT) == '"\\255\\254"'
    assert fb.str_lit(_TRUNCTED) == '"\\227\\129"'


def test_both_spellings_compile_to_the_same_constant():
    """The amendment's machine-checkable invariance, at the constant level:
    raw spelling vs escape-only spelling of the same bytes."""
    from pyluadec.structure import fallback as fb

    raw = "【直哉】".encode()
    a = oracle.compile_source(b"f(" + fb.str_lit(raw).encode() + b")\n",
                              strip=True)
    b = oracle.compile_source(b"f(" + fb._escape_only(raw).encode() + b")\n",
                              strip=True)
    assert ingest.load_bytes(a).constants == ingest.load_bytes(b).constants


def test_emit_delegates_to_the_single_judgment():
    """One implementation, two call sites: `_str_lit` IS `str_lit`."""
    from pyluadec.emit import lua as emit_lua
    from pyluadec.structure import fallback as fb

    assert emit_lua._str_lit("【直哉】".encode()) == fb.str_lit("【直哉】".encode())
    assert emit_lua._str_lit(b"\xff\xfe") == fb.str_lit(b"\xff\xfe")


def test_pure_ascii_fallback_unchanged():
    out = _fallback_text(b'f("plain")\n')
    assert b'"plain"' in out
