"""Ported generation scheme from the predecessor's
`pyluadec/test_generated_semantic_cases.py` (M4 task 5). Mechanism-equivalent
rewrite (spec §8): same deterministic source generator (`_generate_case_source`
below is a verbatim port, only the `unittest`-side plumbing changed);
`DecompilerPipeline.decompile_source` + a subprocess `lua -` call ->
`oracle.compile_source` + `structure.structured.emit_certified_chunk` +
`oracle.run_bytes`.

This is a differential-execution corpus fuzzer, not a structuring-coverage
gate: each case only asserts that the ORIGINAL and the DECOMPILED source
produce byte-identical stdout (and both exit 0). It deliberately does NOT
assert `certs["main"].level == "L3"` -- unlike `test_semantic_regressions.py`'s
five named cases, this generator's whole purpose is orig-vs-decompiled
equivalence regardless of whether the artifact that shipped was structured or
fallback, both of which are exercised across the CASE_COUNT cases.

## `PYLUADEC_GENERATED_CASE_LIMIT`

Honored exactly as upstream: an integer in `[1, CASE_COUNT]` selects how many
of the `CASE_COUNT` deterministic cases run; unset or unparseable falls back
to `DEFAULT_LIMIT`. Unlike upstream (whose unset default was the full
`CASE_COUNT` = 24), `DEFAULT_LIMIT` here is deliberately small: CLAUDE.md /
this milestone's brief make suite speed a standing directive (400 tests /
~33.9s against a 45s ceiling with more tasks still to land), and this task's
own budget is <=3s. Measured 2026-08-11: ~0.06s/case end to end (compile
original, run original, decompile+certify, run decompiled, diff stdout), so
`DEFAULT_LIMIT` cases add well under a second to the default suite; the full
24-case sweep (~1.7s, also measured 2026-08-11) is a documented manual
command rather than part of the default run:

    PYLUADEC_GENERATED_CASE_LIMIT=24 uv run pytest tests/test_generated_semantic_cases.py -v

(also recorded in docs/runbooks/structured-pipeline.md's "Run the suite").
"""
from __future__ import annotations

import os

import pytest

from pyluadec import oracle
from pyluadec.ingest import load_bytes
from pyluadec.structure.structured import emit_certified_chunk

CASE_COUNT = 24
DEFAULT_LIMIT = 3


def _generate_case_source(case_id: int) -> str:
    n_ops = 10 + (case_id % 8)
    arr_len = 180 + (case_id % 90)
    loop2 = 80 + (case_id % 40)
    closure_n = 6 + (case_id % 6)
    seed_a = 17 + (case_id * 13) % 97
    seed_b = 23 + (case_id * 19) % 89
    seed_c = 31 + (case_id * 29) % 73

    lines: list[str] = []
    lines.append("local branch_gen = {0,0,0,0,0}")
    lines.append("local branch_sum = {0,0,0,0}")
    lines.append("local op_dispatch_hits = {}")
    lines.append("local op_inner_hits = {0,0,0}")
    lines.append(f"for i=1,{n_ops} do op_dispatch_hits[i]=0 end")
    lines.append("")
    lines.append("local function make_counter(base, twist)")
    lines.append("    local total = base")
    lines.append("    return function(v)")
    lines.append("        total = (total + v * twist + (v % 13)) % 1000003")
    lines.append("        if total % 2 == 0 then")
    lines.append("            total = total + twist")
    lines.append("        else")
    lines.append("            total = total - (twist % 7)")
    lines.append("        end")
    lines.append("        if total < 0 then")
    lines.append("            total = total + 1000003")
    lines.append("        end")
    lines.append("        return total")
    lines.append("    end")
    lines.append("end")
    lines.append("")
    lines.append("local counters = {}")
    lines.append(f"for i = 1, {closure_n} do")
    lines.append("    counters[i] = make_counter((i * 17 + 3) % 97, (i * 9 + 5) % 23 + 1)")
    lines.append("end")
    lines.append("")
    lines.append("local function fib(n, memo)")
    lines.append("    local t = memo[n]")
    lines.append("    if t ~= nil then")
    lines.append("        return t")
    lines.append("    end")
    lines.append("    local out")
    lines.append("    if n < 2 then")
    lines.append("        out = n")
    lines.append("    else")
    lines.append("        out = fib(n - 1, memo) + fib(n - 2, memo)")
    lines.append("    end")
    lines.append("    memo[n] = out")
    lines.append("    return out")
    lines.append("end")
    lines.append("")
    for op in range(1, n_ops + 1):
        mul_a = 3 + ((op * 5 + case_id) % 19)
        mul_b = 7 + ((op * 9 + case_id * 3) % 17)
        bias = 41 + ((op * 11 + case_id * 7) % 251)
        lines.append(f"local function op_{op}(x, y)")
        lines.append(f"    local r = (x * {mul_a} + y * {mul_b} + {bias}) % 1000003")
        lines.append("    if r % 5 == 0 then")
        lines.append("        op_inner_hits[1] = op_inner_hits[1] + 1")
        lines.append("        r = r + (x % 17)")
        lines.append("    elseif r % 5 == 1 then")
        lines.append("        op_inner_hits[2] = op_inner_hits[2] + 1")
        lines.append("        r = r - (y % 19)")
        lines.append("    else")
        lines.append("        op_inner_hits[3] = op_inner_hits[3] + 1")
        lines.append("        r = r + ((x + y) % 23)")
        lines.append("    end")
        lines.append("    if r < 0 then")
        lines.append("        r = r + 1000003")
        lines.append("    end")
        lines.append("    return r")
        lines.append("end")
        lines.append("")

    lines.append("local data = {}")
    lines.append(f"for i = 1, {arr_len} do")
    lines.append(f"    local v = (i * {seed_a} + (i % 11) * {seed_b} + (i % 7) * {seed_c}) % 997")
    lines.append("    local m = i % 5")
    lines.append("    if m == 0 then")
    lines.append("        branch_gen[1] = branch_gen[1] + 1")
    lines.append("        data[i] = v + i")
    lines.append("    elseif m == 1 then")
    lines.append("        branch_gen[2] = branch_gen[2] + 1")
    lines.append("        data[i] = v - (i % 7)")
    lines.append("    elseif m == 2 then")
    lines.append("        branch_gen[3] = branch_gen[3] + 1")
    lines.append("        data[i] = v * 2 - (i % 5)")
    lines.append("    elseif m == 3 then")
    lines.append("        branch_gen[4] = branch_gen[4] + 1")
    lines.append("        data[i] = v + (i % 13) - (i % 3)")
    lines.append("    else")
    lines.append("        branch_gen[5] = branch_gen[5] + 1")
    lines.append("        data[i] = v * 3 - (i % 11)")
    lines.append("    end")
    lines.append("end")
    lines.append("")
    lines.append("local sum = 0")
    lines.append("for i, v in ipairs(data) do")
    lines.append("    local c = counters[(i % #counters) + 1]")
    lines.append("    local t = c(v)")
    lines.append(f"    local idx = ((i + t) % {n_ops}) + 1")
    lines.append("    op_dispatch_hits[idx] = op_dispatch_hits[idx] + 1")
    lines.append("    local merged = 0")
    for op in range(1, n_ops + 1):
        if op == 1:
            lines.append(f"    if idx == {op} then")
        else:
            lines.append(f"    elseif idx == {op} then")
        lines.append(f"        merged = op_{op}(t, i)")
    lines.append("    else")
    lines.append("        merged = op_1(t, i)")
    lines.append("    end")
    lines.append("    if merged % 4 == 0 then")
    lines.append("        branch_sum[1] = branch_sum[1] + 1")
    lines.append("        sum = sum + merged")
    lines.append("    elseif merged % 4 == 1 then")
    lines.append("        branch_sum[2] = branch_sum[2] + 1")
    lines.append("        sum = sum - (merged % 97)")
    lines.append("    elseif merged % 4 == 2 then")
    lines.append("        branch_sum[3] = branch_sum[3] + 1")
    lines.append("        sum = sum + (merged % 53)")
    lines.append("    else")
    lines.append("        branch_sum[4] = branch_sum[4] + 1")
    lines.append("        sum = sum - (merged % 41)")
    lines.append("    end")
    lines.append("end")
    lines.append("")
    lines.append("local memo = {}")
    lines.append("local i = 1")
    lines.append(f"while i <= {loop2} do")
    lines.append("    sum = sum + fib((i + 3) % 12, memo)")
    lines.append("    if sum % 19 == 0 then")
    lines.append("        sum = sum + i")
    lines.append("    else")
    lines.append("        sum = sum - (i % 5)")
    lines.append("    end")
    lines.append("    i = i + 1")
    lines.append("end")
    lines.append("")
    lines.append("for j = 1, 40 do")
    lines.append("    local x = data[(j % #data) + 1]")
    lines.append("    if x % 2 == 0 then")
    lines.append("        sum = sum + (x % 31)")
    lines.append("    else")
    lines.append("        sum = sum - (x % 27)")
    lines.append("    end")
    lines.append("end")
    lines.append("")
    lines.append("for i = 1, 5 do")
    lines.append("    if branch_gen[i] == 0 then")
    lines.append("        error('branch_gen_not_reached:' .. i)")
    lines.append("    end")
    lines.append("end")
    lines.append("for i = 1, 4 do")
    lines.append("    if branch_sum[i] == 0 then")
    lines.append("        error('branch_sum_not_reached:' .. i)")
    lines.append("    end")
    lines.append("end")
    lines.append("for i = 1, #op_dispatch_hits do")
    lines.append("    if op_dispatch_hits[i] == 0 then")
    lines.append("        error('dispatch_not_reached:' .. i)")
    lines.append("    end")
    lines.append("end")
    lines.append("for i = 1, 3 do")
    lines.append("    if op_inner_hits[i] == 0 then")
    lines.append("        error('op_inner_not_reached:' .. i)")
    lines.append("    end")
    lines.append("end")
    lines.append("")
    lines.append(f"print(string.format('CASE:%03d:%d', {case_id}, sum))")
    return "\n".join(lines) + "\n"


def _resolve_limit() -> int:
    raw = os.environ.get("PYLUADEC_GENERATED_CASE_LIMIT", "").strip()
    if not raw:
        return DEFAULT_LIMIT
    try:
        parsed = int(raw)
    except ValueError:
        return DEFAULT_LIMIT
    if parsed <= 0:
        return DEFAULT_LIMIT
    return min(parsed, CASE_COUNT)


@pytest.mark.parametrize("case_id", range(1, _resolve_limit() + 1))
def test_generated_semantic_case(case_id: int) -> None:
    source = _generate_case_source(case_id)
    bc = oracle.compile_source(source.encode(), strip=True)
    orig = oracle.run_bytes(bc, is_source=False)
    out = emit_certified_chunk(load_bytes(bc))
    dec = oracle.run_bytes(out.source, is_source=True)
    assert orig.returncode == 0, orig.stderr.decode(errors="replace")
    assert dec.returncode == 0, dec.stderr.decode(errors="replace")
    assert orig.stdout == dec.stdout, (
        f"generated case {case_id} mismatch\n"
        f"level={out.certs['main'].level}\n"
        f"orig stdout: {orig.stdout!r}\n"
        f"decompiled stdout: {dec.stdout!r}\n"
        f"decompiled stderr: {dec.stderr.decode(errors='replace')!r}"
    )
