"""Fallback 状态机发射器（spec §3 ③ 的保底路径）。

任何函数都发射为语义精确的 pc 派发循环。丑是特性：正确性来自逐 opcode 对照
lvm.c 的模板；可读性属于 M3+ 的结构化/美化层。语义模板与 lift/effects.py
共享同一套结论（no-frills PDF §per-opcode + lvm.c）。
"""
from __future__ import annotations

import re
import struct

from pyluadec.cfg import build_cfg
from pyluadec.ingest.proto import LuaNumber, Proto

from pyluadec.lift import LUA_KEYWORDS, LirInstr, Op, indexk, isk, lift_proto


class EmitError(Exception):
    pass


_IDENT_RE = re.compile(rb"[A-Za-z_][A-Za-z0-9_]*$")

PRELUDE = """\
local __pld_select, __pld_unpack, __pld_tonumber, __pld_error = select, unpack, tonumber, error
local __pld_pack = function(...) return {n = __pld_select('#', ...), ...} end
local __pld_get = function(R, B, i) local x = R[i] if B[i] then return x.v end return x end
local __pld_set = function(R, B, i, v) if B[i] then R[i].v = v else R[i] = v end end
local __pld_F = {}
"""


def num_lit(k: LuaNumber) -> str:
    v = struct.unpack("<d", k.payload)[0]
    if v != v:
        return "(0/0)"
    if v == float("inf"):
        return "(1/0)"
    if v == float("-inf"):
        return "(-1/0)"
    candidates = []
    if v == int(v) and abs(v) < 1e16:
        candidates.append("%d" % int(v))
    candidates += ["%.14g" % v, "%.17g" % v]
    for s in candidates:
        if struct.pack("<d", float(s)) == k.payload:
            return f"({s})" if s.startswith("-") else s
    raise EmitError(f"cannot render number payload {k.payload.hex()} losslessly")


def str_lit(bs: bytes) -> str:
    out = ['"']
    for byte in bs:
        if byte == 0x22:                  # '"'
            out.append('\\"')
        elif byte == 0x5C:                # '\\'
            out.append("\\\\")
        elif 32 <= byte <= 126:
            out.append(chr(byte))
        else:
            out.append("\\%03d" % byte)   # 定长三位，避免与后继数字字符粘连
    out.append('"')
    return "".join(out)


def const_lit(c) -> str:
    if c is None:
        return "nil"
    if c is True:
        return "true"
    if c is False:
        return "false"
    if isinstance(c, LuaNumber):
        return num_lit(c)
    if isinstance(c, bytes):
        return str_lit(c)
    raise EmitError(f"unexpected constant {c!r}")


_ARITH = {Op.ADD: "+", Op.SUB: "-", Op.MUL: "*", Op.DIV: "/", Op.MOD: "%", Op.POW: "^"}


class _FnEmitter:
    def __init__(self, path: str, proto: Proto):
        self.path = path
        self.proto = proto
        self.fn = lift_proto(proto)
        self.cfg = build_cfg(self.fn)
        self.boxed = self.fn.captured_regs
        self.lines: list[str] = []

    # ---- 访问助手 -------------------------------------------------------
    def rd(self, i: int) -> str:
        return f"__pld_R[{i}].v" if i in self.boxed else f"__pld_R[{i}]"

    def wr(self, i: int, expr: str) -> str:
        return f"{self.rd(i)} = {expr}"

    def rk(self, x: int) -> str:
        if isk(x):
            return const_lit(self.proto.constants[indexk(x)])
        return self.rd(x)

    def global_name(self, bx: int) -> str:
        k = self.proto.constants[bx]
        if (not isinstance(k, bytes) or not _IDENT_RE.fullmatch(k)
                or k.decode("ascii") in LUA_KEYWORDS or k.startswith(b"__pld_")):
            raise EmitError(f"global name {k!r} not emittable as identifier")
        return k.decode("ascii")

    # ---- 函数级发射 -----------------------------------------------------
    def emit(self) -> str:
        p = self.proto
        params = [f"__pld_p{i}" for i in range(p.numparams)]
        if p.is_vararg & 2:
            params.append("...")
        L = self.lines
        L.append(f'__pld_F["{self.path}"] = function(__pld_U)')
        L.append(f'return function({", ".join(params)})')
        boxed_init = ", ".join(f"[{i}]=true" for i in sorted(self.boxed))
        L.append(f"local __pld_R, __pld_B, __pld_top = {{}}, {{{boxed_init}}}, 0")
        for i in range(p.numparams):
            L.append(f"__pld_R[{i}] = {{v = __pld_p{i}}}" if i in self.boxed
                     else f"__pld_R[{i}] = __pld_p{i}")
        for i in sorted(self.boxed):
            if i >= p.numparams:
                L.append(f"__pld_R[{i}] = {{}}")
        L.append("local __pld_pc = 1")
        L.append("while true do")
        kw = "if"
        for start in sorted(self.cfg.blocks):
            L.append(f"{kw} __pld_pc == {start} then")
            kw = "elseif"
            self._emit_block(self.cfg.blocks[start])
        L.append('else __pld_error("pyluadec fallback: invalid pc") end')
        L.append("end")     # while
        L.append("end")     # inner function
        L.append("end")     # factory
        return "\n".join(L) + "\n"

    def _emit_block(self, blk) -> None:
        for li in blk.instrs[:-1]:
            self._emit_simple(li)
        last = blk.instrs[-1]
        if not self._emit_terminator(last):
            self._emit_simple(last)
            self.lines.append(f"__pld_pc = {blk.succs[0]}")

    # ---- 直线指令（本 Task 的子集；Task 7/8 扩展本方法与 _emit_terminator）
    def _emit_simple(self, li: LirInstr) -> None:
        ri = li.ri
        op, a, b, c, bx = ri.op, ri.a, ri.b, ri.c, ri.bx
        L, rd, wr, rk = self.lines, self.rd, self.wr, self.rk
        if op is Op.MOVE:
            L.append(wr(a, rd(b)))
        elif op is Op.LOADK:
            L.append(wr(a, const_lit(self.proto.constants[bx])))
        elif op is Op.LOADBOOL:
            L.append(wr(a, "true" if b else "false"))   # C≠0 时块尾由 terminator 跳 pc+2
        elif op is Op.LOADNIL:
            for i in range(a, b + 1):
                L.append(wr(i, "nil"))
        elif op is Op.GETGLOBAL:
            L.append(wr(a, self.global_name(bx)))
        elif op is Op.SETGLOBAL:
            L.append(f"{self.global_name(bx)} = {rd(a)}")
        elif op is Op.GETTABLE:
            L.append(wr(a, f"{rd(b)}[{rk(c)}]"))
        elif op is Op.SETTABLE:
            L.append(f"{rd(a)}[{rk(b)}] = {rk(c)}")
        elif op is Op.NEWTABLE:
            L.append(wr(a, "{}"))
        elif op is Op.SELF:
            # R(A+1) := R(B); R(A) := R(B)[RK(C)] —— 用临时变量抵御 A+1 == B 重叠
            L.append(f"do local __pld_t = {rd(b)} "
                     f"{wr(a + 1, '__pld_t')} {wr(a, f'__pld_t[{rk(c)}]')} end")
        elif op in _ARITH:
            L.append(wr(a, f"{rk(b)} {_ARITH[op]} {rk(c)}"))
        elif op is Op.UNM:
            L.append(wr(a, f"-({rd(b)})"))
        elif op is Op.NOT:
            L.append(wr(a, f"not ({rd(b)})"))
        elif op is Op.LEN:
            L.append(wr(a, f"#({rd(b)})"))
        elif op is Op.CONCAT:
            L.append(wr(a, " .. ".join(rd(i) for i in range(b, c + 1))))
        elif op is Op.CALL:
            self._emit_call(ri)
        else:
            raise EmitError(f"pc {ri.pc}: opcode {op.name} not yet supported by fallback")

    def _call_expr(self, ri) -> tuple[str, list[str]]:
        """返回 (调用表达式, 前置语句)。B==0（open args）在 Task 7 落地。"""
        a, b = ri.a, ri.b
        if b >= 1:
            args = ", ".join(self.rd(a + 1 + i) for i in range(b - 1))
            return f"{self.rd(a)}({args})", []
        raise EmitError(f"pc {ri.pc}: open-arg CALL not yet supported")

    def _emit_call(self, ri) -> None:
        a, c = ri.a, ri.c
        expr, pre = self._call_expr(ri)
        L = self.lines
        if c == 1 and not pre:
            L.append(expr)
        elif c >= 2 and not pre:
            targets = ", ".join(self.rd(a + i) for i in range(c - 1))
            L.append(f"{targets} = {expr}")
        elif c >= 1:
            body = [expr] if c == 1 else \
                [", ".join(self.rd(a + i) for i in range(c - 1)) + f" = {expr}"]
            L.append("do " + " ".join(pre + body) + " end")
        else:
            raise EmitError(f"pc {ri.pc}: open-result CALL not yet supported")

    # ---- 终结指令（本 Task 仅 RETURN 定长 + LOADBOOL 跳变体）
    def _emit_terminator(self, li: LirInstr) -> bool:
        ri = li.ri
        op, a, b = ri.op, ri.a, ri.b
        L, rd = self.lines, self.rd
        if op is Op.RETURN:
            if b == 1:
                L.append("return")
            elif b >= 2:
                L.append("return " + ", ".join(rd(a + i) for i in range(b - 1)))
            else:
                raise EmitError(f"pc {ri.pc}: open RETURN not yet supported")
            return True
        if op is Op.LOADBOOL and ri.c:
            L.append(self.wr(a, "true" if b else "false"))
            L.append(f"__pld_pc = {ri.pc + 2}")
            return True
        return False


def emit_chunk(root: Proto) -> bytes:
    parts: list[str] = [PRELUDE]

    def walk(path: str, p: Proto) -> None:
        for i, s in enumerate(p.subprotos):
            walk(f"{path}_{i}", s)
        parts.append(_FnEmitter(path, p).emit())

    walk("main", root)
    parts.append('return __pld_F["main"]({})(...)\n')
    return "".join(parts).encode()
