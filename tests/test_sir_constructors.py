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


# ---- M7 task 10: the statement-built table's DECLARATION POSITION --------
#
# A hint-0 NEWTABLE whose next touch is a store TO its register is a
# statement-built table (`local t = {}` + stores). Task 9's gate
# materialized it at the FIRST STORE -- which orders the `local t = {}`
# after any statement the original placed between the NEWTABLE and that
# store, and the recompile then swaps the declaration order (and with it
# every register above the table). Task 10's fast path materializes at the
# NEWTABLE itself: `local t = {}` lands exactly where the original put it.

def test_statement_table_declares_before_an_intervening_local():
    # `t` is declared first in the source; `n` is read twice, so it
    # materializes as its own `local` between the NEWTABLE and the first
    # store -- the position the close-at-store path used to lose.
    src = (b"local t = {}\n"
           b"local n = 0\n"
           b"t[n] = 1\n"
           b"t[n] = 2\n"
           b"return t, n\n")
    assert _levels_of(src) == {"main": "L3"}


def test_statement_table_declares_before_an_open_range():
    # The snr_common:main_29 shape: the first store sits inside a loop, past
    # an open `CALL`/`VARARG` whose open region is based ABOVE the table's
    # register. The lookahead must see through those (reg < base means the
    # open instruction does not touch the register) and still find the
    # store; the any-open-flag version of the scan refused here and the
    # declaration landed at the close, swapping R10/R11.
    src = (b"local function f(...)\n"
           b"  local t = {}\n"
           b"  local n = 0\n"
           b'  if 0 < select("#", ...) then n = select("#", ...) / 4 end\n'
           b'  for i = 1, select("#", ...) do t[i] = select(i, ...) end\n'
           b"  return t, n\n"
           b"end\n"
           b"return f\n")
    assert _levels_of(src) == {"main": "L3", "main_0": "L3"}


def test_an_empty_literal_consumed_as_a_value_still_folds():
    # Narrowness: hint 0 + next touch a READ (the `{}` consumed by the
    # call) keeps the pop-once staged literal. Materializing here would add
    # a `local` the original never had and cost the certification. The
    # carrier is `f({}, 1)` with the result read twice into a multi-value
    # return, NOT `return f({})` -- the latter compiles to a TAILCALL
    # against the original's CALL+RETURN and is `L1` for that unrelated
    # reason (verified before this test was written).
    src = (b"local x = f({}, 1)\n"
           b"return x, 2\n")
    assert _levels_of(src) == {"main": "L3"}


def test_neutering_the_lookahead_costs_the_position(monkeypatch):
    """Neuter proof: without the NEWTABLE-side fast path the
    intervening-local repro degrades to `L1` (the close-at-store path
    re-emits the declaration late and the recompile swaps the register
    pair). Cache cleared across runs -- certification memoizes."""
    from pyluadec.express import reconstruct
    from pyluadec.structure.structured import clear_certification_cache

    src = (b"local t = {}\n"
           b"local n = 0\n"
           b"t[n] = 1\n"
           b"t[n] = 2\n"
           b"return t, n\n")
    clear_certification_cache()
    assert _levels_of(src) == {"main": "L3"}
    monkeypatch.setattr(reconstruct.Reconstructor, "_next_touch_is_store_to",
                        lambda self, reg, pc: False)
    clear_certification_cache()
    assert _levels_of(src) == {"main": "L1"}
    monkeypatch.undo()
    clear_certification_cache()
    assert _levels_of(src) == {"main": "L3"}
