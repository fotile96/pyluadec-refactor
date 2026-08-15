"""动态键表构造器重建 -- M7 任务 6（机制 G，诊断于 config.lua:main）。

`luac` 把任何 hash 条目的构造器编成 `NEWTABLE`（带 B/C 尺寸提示）＋一串
`SETTABLE`，其中键是常量时 `isk(B)`、是**寄存器**时 `B < 256`。重建器的折叠
条件此前要求 `isk(ri.b)` —— 常量键折叠成 `{k = v}` / `{["k"] = v}`，动态键
掉进语句路径：表寄存器被迫物化为 `local l0_x = {}`，后续本可折叠的构造器也
被拖成对同名 local 的重赋值。config.lua:main（57 条指令、三个直接赋给全局
的构造器，其一 12 个动态键）因此 `mismatch: maxstacksize` + `mismatch: code`
（`NEWTABLE` 尺寸提示 C=12 对 C=0）整文件塌落为 fallback。

修法：折叠接纳寄存器键（键表达式 `_read_reg(ri.b)`），打印层已有的
`[<expr>] = <val>` 语法承担输出。证据：本文件的合成用例 + config.lua 全文件
翻盘（见任务提交）。
"""
from __future__ import annotations

from pyluadec.ingest import load_bytes
from pyluadec.oracle import compile_source
from pyluadec.pipeline import decompile_chunk


def _levels_of(source: bytes) -> dict[str, str]:
    root = load_bytes(compile_source(source, strip=True))
    return decompile_chunk(root).levels


def test_dynamic_key_constructor_certifies():
    src = (b'X = {[f] = "a", [g] = "b", [h] = "c", [i] = "d", '
           b'[j] = "e", [k] = "l"}\n')
    assert _levels_of(src) == {"main": "L3"}


def test_dynamic_key_with_register_value_certifies():
    # key AND value both register-carried: {[f] = g}
    src = (b'X = {[f] = g, [g] = h, [i] = j, [k] = l, [m] = n, [o] = p}\n')
    assert _levels_of(src) == {"main": "L3"}


def test_reused_table_register_certifies():
    # The config.lua shape: two constructor expressions through the SAME
    # register, each consumed by a SETGLOBAL -- no local may materialize.
    src = (b'A = {[f] = "a", [g] = "b", [h] = "c", [i] = "d", [j] = "e", [k] = "l"}\n'
           b'B = {run = run, wait = wait, msg = msg, save = save, load = load, x = y}\n')
    assert _levels_of(src) == {"main": "L3"}


def test_config_shape_three_tables_certifies():
    src = (b'A = {[f] = "a", [g] = "b", [h] = "c", [i] = "d", [j] = "e", [k] = "l"}\n'
           b'B = {f = f, g = g, h = h, i = i, j = j, k = k}\n'
           b'C = {m = "disc0:/x.prx", n = "script/y.lua"}\n')
    assert _levels_of(src) == {"main": "L3"}
