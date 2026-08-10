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
