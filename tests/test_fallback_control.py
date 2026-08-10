CONTROL_CASES = [
    'local i = 0 while i < 5 do i = i + 1 end print(i)',
    'for i = 1, 5 do print(i) end',
    'for i = 10, 1, -2 do print(i) end',
    'for i = 1.5, 3.7, 0.5 do print(i) end',
    'for i = 1, 0 do print("never") end print("after")',
    'local t = {10, 20, 30} for i, v in ipairs(t) do print(i, v) end',
    'local x = 5 if x > 3 then print("big") elseif x > 1 then print("mid") '
    'else print("small") end',
    'local a = false or 3 local b = a and "yes" print(a, b)',
    # TEST（真值测试且不赋值）——注意 and/or 赋值形态只产 TESTSET，必须用 `if <local> then`
    'local a = tonumber("1") if a then print("truthy") end',
    'local a = tonumber("1") local b = tonumber("2") if a and b then print("and") end',
    'local t = {} while t do t = nil end print("done")',
    'print(1 == 1, 1 ~= 2, 2 < 3, 3 <= 3, "a" < "b", "a" == "a")',
    'local x = nil if x == nil then print("is nil") end',
    'repeat local x = 1 until x == 1 print("done")',
    'for i = 1, 3 do if i == 2 then break end print(i) end',
    'local s = 0 for i = 1, 100 do s = s + i end print(s)',
    # NOTE: the 7 CLOSURE-dependent cases originally here (local/anonymous function
    # forms exercising open CALL/VARARG/SETLIST/TAILCALL via a callee) were moved to
    # Task 8's suite, which now implements CLOSURE (test_fallback_closures.py's
    # CLOSURE_CASES). They are reproduced verbatim in task-7-report.md so nothing
    # is lost, in particular the TAILCALL-via-recursion case (TAILCALL has only 3
    # occurrences in the whole 229-file corpus). Replaced below with closure-free
    # equivalents that exercise the identical opcodes, so Task 7 still self-verifies
    # every "open" form it owns without needing CLOSURE.
    'print(select(2, 10, 20, 30))',
    # open-arg CALL (B==0) into print; open-result CALL (C==0) from select
    'local t = {select(2, 10, 20, 30)} print(#t, t[1], t[2])',
    # open-result CALL (C==0) from select; open SETLIST (B==0) into t
    'local t = {1, 2, ...} print(#t, t[1], t[2])',
    # open VARARG (B==0) mixed with fixed elements; open SETLIST (B==0)
    'local t = {...} print(#t)',
    # open VARARG (B==0) alone (empty at this call site); open SETLIST (B==0)
    'return print(select(2, 10, 20, 30))',
    # TAILCALL with open args (the _call_expr `pre` branch); open-result CALL (C==0)
    'local t = {%s} print(#t, t[1], t[51], t[60])' % ", ".join(
        str(i) for i in range(1, 61)),                     # SETLIST 两轮 flush（>50，closed）
    'print((" "):rep(0) == "")',
    'while true do break end print("out")',
]


def test_control_flow_cases():
    from tests.diffexec import assert_fallback_roundtrip
    for src in CONTROL_CASES:
        assert_fallback_roundtrip(src)


def test_chunk_level_vararg():
    from tests.diffexec import assert_fallback_roundtrip
    assert_fallback_roundtrip("print(...)", args=("a1", "a2"))
    assert_fallback_roundtrip('local n = select("#", ...) print(n)', args=("x",))


def _vararg_b_values(src: str) -> list[int]:
    """解码 src 中所有 VARARG 指令的 B 操作数（含子 proto）——用于在断言差分执行
    之前先确认我们真的触发了目标 B 形态，而不是巧合触发了别的形态。"""
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.lift.opcodes import Op, decode
    bc = oracle.compile_source(src.encode())
    bs: list[int] = []
    stack = [load_bytes(bc, chunkname="=t")]
    while stack:
        p = stack.pop()
        for pc, word in enumerate(p.code, start=1):
            ri = decode(word, pc=pc)
            if ri.op is Op.VARARG:
                bs.append(ri.b)
        stack.extend(p.subprotos)
    return bs


def test_vararg_fixed_target_forms():
    """VARARG 的 B>=2（定数目标）形态在此前套件中零覆盖——所有既有 VARARG 用例都是
    B==0（open）。这两个用例经解码确认触发 B=3（2 目标）与 B=2（1 目标）。"""
    from tests.diffexec import assert_fallback_roundtrip
    src_b3 = "local function f(...) local a,b = ... return a,b end print(f(1,2,3))"
    assert _vararg_b_values(src_b3) == [3]
    assert_fallback_roundtrip(src_b3)

    src_b2 = "local a = ... print(a)"
    assert _vararg_b_values(src_b2) == [2]
    assert_fallback_roundtrip(src_b2, args=("x", "y"))


def test_vararg_needsarg_raises_confesses_not_guesses():
    """`function(...)` bodies that reference the Lua-5.0 compat `arg` table
    (as opposed to `...` itself) set VARARG_NEEDSARG (bit 4 of is_vararg;
    `luac` gives is_vararg=7 = HASARG|ISVARARG|NEEDSARG). `adjust_varargs`
    (lvm.c) materialises that `arg` table into R[numparams] at call time --
    the fallback emitter never initialises that register, so before this
    guard existed, `local function f(...) return type(arg) end print(f(1))`
    silently decompiled to a program that prints `nil` instead of `table`
    (confirmed by hand: exit 0 on both sides, so nothing in the L1 compile
    gate or a naive differential test would have caught it). Per this
    project's "confess, don't guess" discipline, this must raise EmitError,
    not emit something plausible.
    """
    import pytest
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.structure.fallback import EmitError, emit_chunk
    bc = oracle.compile_source(b"local function f(...) return type(arg) end print(f(1))")
    p = load_bytes(bc)
    assert p.subprotos[0].is_vararg & 4, p.subprotos[0].is_vararg   # VARARG_NEEDSARG set
    with pytest.raises(EmitError, match="VARARG_NEEDSARG"):
        emit_chunk(p)


def test_vararg_zero_target_form():
    """VARARG 的 B==1（零目标，_emit_simple 里的 no-op 分支）同样此前零覆盖。
    `local a = 1, ...` 里赋值目标已被 `1` 占满，末尾 `...` 贡献 0 个值
    （adjust_assign 的 extra 被截到 0，luaK_setreturns 设 B = extra+1 = 1）。"""
    from tests.diffexec import assert_fallback_roundtrip
    src = "local function f(...) local a = 1, ... return a end print(f(9,9))"
    assert _vararg_b_values(src) == [1]
    assert_fallback_roundtrip(src)


def test_runtime_error_parity():
    """运行期报错：两边 exit code 一致，且都非零（不比对 stderr 全文）。

    不经 pcall/闭包包装——直接让报错语句崩溃 main chunk，exit code 与 stdout
    仍是 assert_fallback_roundtrip 已经在比对的东西，三个错误类别都是本
    Task 的 opcode（算术/GETTABLE/FORPREP），且都不需要 CLOSURE。
    """
    from pyluadec import oracle
    from tests.diffexec import assert_fallback_roundtrip
    cases = [
        'local t = {} local x = t + 1',            # ADD on a table
        'local t = nil local x = t.k',              # GETTABLE on nil
        'local n = "x" for i = 1, n do end',        # FORPREP: non-numeric limit
    ]
    for src in cases:
        dec = assert_fallback_roundtrip(src)
        r1 = oracle.run_bytes(oracle.compile_source(src.encode()), is_source=False)
        r2 = oracle.run_bytes(dec, is_source=True)
        assert r1.returncode != 0, f"orig did not error: {src!r}"
        assert r2.returncode != 0, f"decompiled did not error: {src!r}"
