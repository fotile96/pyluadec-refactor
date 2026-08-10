CLOSURE_CASES = [
    # upvalue 读写（GETUPVAL/SETUPVAL + 盒共享）
    'local c = 0 local function inc() c = c + 1 return c end '
    'print(inc(), inc(), c)',
    # 逐迭代捕获：循环体尾 CLOSE 换盒
    'local fs = {} for i = 1, 3 do fs[i] = function() return i end end '
    'print(fs[1](), fs[2](), fs[3]())',
    # 两个独立计数器：同一工厂两次实例化互不串盒
    'local function counter() local n = 0 return function() n = n + 1 return n end end '
    'local a, b = counter(), counter() print(a(), a(), b())',
    # do-end 块尾 CLOSE
    'local x = 1 local f do local y = 2 f = function() return x + y end end print(f())',
    # GETUPVAL 伪指令：孙函数经中间层转递 upvalue
    'local function outer() local v = 10 '
    'local function mid() local function inner() return v end return inner end '
    'return mid()() end print(outer())',
    # upvalue 写穿透两层
    'local n = 0 local function bump() local function go() n = n + 1 end go() end '
    'bump() bump() print(n)',
    # 闭包与寄存器复用：CLOSE 后同 slot 新变量不得污染旧闭包
    'local fs = {} for i = 1, 2 do local v = i * 10 fs[i] = function() return v end end '
    'print(fs[1](), fs[2]())',
    # 混合：捕获的循环变量被闭包内自增
    'local fs = {} for i = 1, 2 do fs[i] = function() i = i + 100 return i end end '
    'print(fs[1](), fs[1](), fs[2]())',
    # 下方为 Task 7 遗留的 CLOSURE 依赖用例（原文逐字保留）
    'local function f(...) return ... end print(f(1, nil, 3))',
    'local function g() return 1, 2, 3 end print(g())',
    'local function g() return 1, 2 end local t = {g()} print(#t, t[1], t[2])',
    'local function g() return 1, 2 end print("x", g())',
    'print(select("#", (function(...) return ... end)(1, nil, nil)))',
    'local function tail(n) if n == 0 then return "done" end return tail(n - 1) end print(tail(10))',
    'local t = {(function() return 7, 8, 9 end)()} print(#t, t[3])',
]


def test_closure_cases():
    from tests.diffexec import assert_fallback_roundtrip
    for src in CLOSURE_CASES:
        assert_fallback_roundtrip(src)


def test_deep_nesting_factory_table():
    """嵌套 5 层 + 同层多兄弟：工厂表命名路径唯一性。"""
    from tests.diffexec import assert_fallback_roundtrip
    src = (
        "local function l1() local a = 1\n"
        "  local function l2() local b = 2\n"
        "    local function l3() local c = 3\n"
        "      local function l4() local d = 4\n"
        "        local function l5() return a + b + c + d end\n"
        "        return l5() end\n"
        "      return l4() end\n"
        "    return l3() end\n"
        "  return l2() end\n"
        "local function sibling() return 100 end\n"
        "print(l1() + sibling())\n")
    dec = assert_fallback_roundtrip(src)
    assert dec.count(b'__pld_F["main_') >= 6          # 工厂逐一登记


def test_emitted_helper_names_cannot_collide_with_globals():
    """`__pld_` 前缀是发射器辅助名与字节码全局名之间的唯一防线。"""
    import pytest
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.structure.fallback import EmitError, emit_chunk
    # 正常情形：全局名照常按标识符发射，产物可编译
    bc = oracle.compile_source(b"local x = 1 local f = function() return x end print(f())")
    dec = emit_chunk(load_bytes(bc))
    assert b"print" in dec
    oracle.compile_source(dec)
    # 冲突情形：字节码里出现 __pld_ 前缀的全局名 → 必须 hard fail，绝不静默串名
    bad = oracle.compile_source(b"__pld_R = 1 return __pld_R")
    with pytest.raises(EmitError):
        emit_chunk(load_bytes(bad))


def test_all_38_opcodes_reachable_in_emitter():
    """公理层完整性：每个 opcode 至少被一个差分用例吃过（含语料未用的 5 个）。"""
    from pyluadec.lift.opcodes import Op
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.lift import lift_proto
    from tests.diffexec import assert_fallback_roundtrip
    from tests.test_fallback_basic import STRAIGHT_LINE_CASES
    from tests.test_fallback_control import CONTROL_CASES
    seen: set[Op] = set()

    def collect(p):
        fn = lift_proto(p)
        seen.update(li.ri.op for li in fn.instrs.values())
        for s in p.subprotos:
            collect(s)

    # 语义补充用例（不为 opcode 覆盖，三份 CASES 已达 38/38——见下方实测注记）：
    # 元方法路径与浮点格式化是发射器最容易悄悄失真的两处。
    extra = [
        'local t = setmetatable({}, {__index = function() return "mm" end}) print(t.k)',
        'io.write(tostring(2 ^ 0.5):sub(1, 6), "\\n")',
    ]
    for src in [*STRAIGHT_LINE_CASES, *CONTROL_CASES, *CLOSURE_CASES, *extra]:
        assert_fallback_roundtrip(src)
        collect(load_bytes(oracle.compile_source(src.encode())))
    missing = {op.name for op in Op} - {op.name for op in seen}
    assert not missing, f"opcodes never exercised: {sorted(missing)}"
