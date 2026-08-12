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

HELPERS = """\
local __pld_select, __pld_unpack, __pld_tonumber, __pld_error = select, unpack, tonumber, error
local __pld_pack = function(...) return {n = __pld_select('#', ...), ...} end
local __pld_get = function(R, B, i) local x = R[i] if B[i] then return x.v end return x end
local __pld_set = function(R, B, i, v) if B[i] then R[i].v = v else R[i] = v end end
"""

PRELUDE = HELPERS + "local __pld_F = {}\n"


_NEG_ZERO_PAYLOAD = struct.pack("<d", -0.0)


def num_lit(k: LuaNumber, *, parenthesize_negative: bool = True) -> str:
    """Render a number payload as a Lua numeral that recompiles to exactly
    these 8 bytes.

    `parenthesize_negative=False` returns the BARE numeral (`-1`, not
    `(-1)`) for the caller that has its own precedence model and will add
    parentheses only where the grammar needs them -- `emit.lua`, which treats
    a leading `-` as unary-minus precedence (M5 task 7 change 3). The default
    keeps the always-safe over-parenthesised form, which is what this module's
    own state-machine templates want: they splice numerals into
    `f"{x} {op} {y}"` slots with no precedence model at all.

    The three special forms below (`(0/0)`, `(1/0)`, `(-1/0)`,
    `(-1/(1/0))`) are unaffected by the flag on purpose: they are
    EXPRESSIONS, not numerals, and their precedence is `/`'s, not unary
    minus's, so `(-1/0) ^ 2` and `-1/0 ^ 2` are different programs.
    """
    v = struct.unpack("<d", k.payload)[0]
    if v != v:
        return "(0/0)"
    if v == float("inf"):
        return "(1/0)"
    if v == float("-inf"):
        return "(-1/0)"
    if k.payload == _NEG_ZERO_PAYLOAD:
        # luaH_get normalises integral number keys via lua_number2int when
        # interning constants (lvm.c), so a plain `-0.0` numeral collides
        # with `0.0` in luac's constant table -- whichever is added first
        # wins, and the preamble's `0` numeral (fallback.py's boxed-register
        # init) means +0.0 always wins that race. `lcode.c`'s constfolding
        # refuses to fold division by zero, so this expression survives as
        # a runtime computation and reliably evaluates to -0.0 instead of
        # going through the constant table at all.
        return "(-1/(1/0))"
    candidates = []
    if v == int(v) and abs(v) < 1e16:
        candidates.append("%d" % int(v))
    candidates += ["%.14g" % v, "%.17g" % v]
    for s in candidates:
        if struct.pack("<d", float(s)) == k.payload:
            if parenthesize_negative and s.startswith("-"):
                return f"({s})"
            return s
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


def const_lit(c, *, parenthesize_negative: bool = True) -> str:
    if c is None:
        return "nil"
    if c is True:
        return "true"
    if c is False:
        return "false"
    if isinstance(c, LuaNumber):
        return num_lit(c, parenthesize_negative=parenthesize_negative)
    if isinstance(c, bytes):
        return str_lit(c)
    raise EmitError(f"unexpected constant {c!r}")


_ARITH = {Op.ADD: "+", Op.SUB: "-", Op.MUL: "*", Op.DIV: "/", Op.MOD: "%", Op.POW: "^"}


#: How one upvalue slot of the function being emitted is reached, as a
#: `(kind, text)` pair. Two kinds, and the distinction is the whole hinge of
#: hybrid emission (M5 task 6):
#:
#: * ``("box", expr)`` -- the classic fallback protocol. `expr` names a box
#:   table ``{v = ...}``; the value is `expr.v` and writes go to `expr.v`. This
#:   is what `__pld_F` factories receive in `__pld_U`, and it is what makes
#:   `OP_CLOSE` expressible (closing a slot means installing a *new* box, which
#:   closures created earlier do not see).
#: * ``("name", ident)`` -- the value IS the enclosing Lua scope's variable
#:   `ident`, captured as a genuine Lua upvalue. No box, no `.v`. Only an
#:   *inline* emission can use this, and only for slots whose enclosing scope
#:   is real Lua code (the structured printer's locals at a hybrid boundary, or
#:   another inline emitter's inherited name slots).
#:
#: A single function can mix the two: a child of an inline emitter inherits
#: name slots for the upvalues its parent reached by name, and gets box slots
#: for everything the parent holds in `__pld_R`.
_BOX = "box"
_NAME = "name"


class _FnEmitter:
    """Emit one proto as a pc-dispatch state machine.

    Two shapes, selected by `inline`:

    * `inline=False` (the M2 form, `emit_chunk`'s): a top-level
      ``__pld_F["path"] = function(__pld_U) return function(...) ... end end``
      factory. Every upvalue is a box handed in through `__pld_U`, and every
      nested function is a *sibling* factory reached by name -- so the whole
      chunk is a flat list of closed factories.
    * `inline=True` (M5 task 6's, `inline_function_parts`'): the `function
      (...) ... end` literal itself, to be dropped into a hole the structured
      printer left at a CLOSURE site. Upvalues come from `upslots`, nested
      functions are emitted *in place* as immediately-invoked factories, and
      the `__pld_*` helpers are declared as locals of this function instead of
      the chunk.

    The inline shape exists because a hybrid chunk's structured part is
    compared field-by-field against the original: the substituted function must
    occupy exactly one subproto slot of its parent and capture exactly the
    parent variables the original CLOSURE's pseudo-instructions name, in the
    same order. A hoisted factory would satisfy neither.
    """

    def __init__(self, path: str, proto: Proto, *, inline: bool = False,
                 upslots: tuple[tuple[str, str], ...] | None = None):
        self.path = path
        self.proto = proto
        self.fn = lift_proto(proto)
        self.cfg = build_cfg(self.fn)
        self.boxed = self.fn.captured_regs
        self.lines: list[str] = []
        self.inline = inline
        self.upslots: tuple[tuple[str, str], ...] = (
            upslots if upslots is not None
            else tuple((_BOX, f"__pld_U[{i}]") for i in range(proto.nups)))

    # ---- 访问助手 -------------------------------------------------------
    def up_slot(self, b: int) -> tuple[str, str]:
        if not 0 <= b < len(self.upslots):
            raise EmitError(f"{self.path}: upvalue index {b} out of range "
                            f"(nups={len(self.upslots)})")
        return self.upslots[b]

    def up_read(self, b: int) -> str:
        kind, text = self.up_slot(b)
        return text if kind == _NAME else f"{text}.v"

    def up_write(self, b: int, expr: str) -> str:
        kind, text = self.up_slot(b)
        return (f"{text} = {expr}" if kind == _NAME else f"{text}.v = {expr}")

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
    def _params(self) -> str:
        p = self.proto
        if p.is_vararg & 4:
            raise EmitError(
                f"{self.path}: VARARG_NEEDSARG set (is_vararg={p.is_vararg}) — "
                "the Lua 5.0 compat 'arg' table that adjust_varargs materialises "
                "into R[numparams] is not modelled by the fallback emitter")
        params = [f"__pld_p{i}" for i in range(p.numparams)]
        if p.is_vararg & 2:
            params.append("...")
        return ", ".join(params)

    def _emit_body(self) -> None:
        """Register frame + pc-dispatch loop, the part both shapes share."""
        p, L = self.proto, self.lines
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

    def emit(self) -> str:
        params = self._params()
        L = self.lines
        L.append(f'__pld_F["{self.path}"] = function(__pld_U)')
        L.append(f"return function({params})")
        self._emit_body()
        L.append("end")     # inner function
        L.append("end")     # factory
        return "\n".join(L) + "\n"

    def emit_inline(self, *, order_prologue: bool) -> tuple[str, str]:
        """`(params, body)` for a bare `function(<params>)\\n<body>end` literal.

        `order_prologue` forces this function's upvalue INDICES to follow
        `upslots` order, by referencing every name slot, in slot order, in the
        first statement. `lparser.c`'s `indexupvalue` appends an upvalue the
        first time the name is mentioned while parsing, and `pushclosure` emits
        the enclosing function's pseudo-instruction sequence in exactly that
        order -- so without the prologue, a state machine that happens to touch
        upvalue 2 before upvalue 0 would make the ENCLOSING (structured,
        field-compared) function emit a different `MOVE`/`GETUPVAL` sequence
        after its `CLOSURE`, i.e. a different `code` tuple, and the hybrid
        certification would fail on the parent rather than on this function.
        The prologue is only needed at a hybrid boundary; nested emissions
        inside an already-substituted subtree are compared against nothing and
        pass `order_prologue=False`.
        """
        params = self._params()
        if order_prologue:
            if any(kind != _NAME for kind, _ in self.upslots):
                # A box slot between two name slots would make the prologue
                # register the names in the wrong INDEX order, which is the one
                # thing it exists to get right. Boundary emissions always get
                # all-name slots from the structured printer, so this is
                # unreachable today; it is a raise rather than an assert
                # because it guards what the enclosing certification compares.
                raise EmitError(
                    f"{self.path}: hybrid boundary function has non-name upvalue "
                    f"slots {self.upslots!r}; upvalue order cannot be pinned")
            names = [text for _kind, text in self.upslots]
            if names:
                self.lines.append("local __pld_ord = {" + ", ".join(names) + "}")
        self.lines.append(HELPERS.rstrip("\n"))
        self._emit_body()
        return params, "\n".join(self.lines) + "\n"

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
        elif op is Op.VARARG:
            if not (self.proto.is_vararg & 2):
                raise EmitError(f"pc {ri.pc}: VARARG in non-vararg function")
            if b == 1:
                pass                                    # 零目标 no-op
            elif b >= 2:
                targets = ", ".join(rd(a + i) for i in range(b - 1))
                L.append(f"{targets} = ...")
            else:
                L.append("do local __pld_rs = __pld_pack(...)")
                L.append(f"for __pld_i = 1, __pld_rs.n do "
                         f"__pld_set(__pld_R, __pld_B, {a} + __pld_i - 1, __pld_rs[__pld_i]) end")
                L.append(f"__pld_top = {a} + __pld_rs.n end")
        elif op is Op.SETLIST:
            eff_c = c if c != 0 else self.proto.code[li.consumed[0] - 1]
            base = (eff_c - 1) * 50                     # LFIELDS_PER_FLUSH
            if b >= 1:
                for i in range(1, b + 1):
                    L.append(f"{rd(a)}[{base + i}] = {rd(a + i)}")
            else:
                L.append(f"do local __pld_n = __pld_top - {a} - 1")
                L.append(f"for __pld_i = 1, __pld_n do {rd(a)}[{base} + __pld_i] = "
                         f"__pld_get(__pld_R, __pld_B, {a} + __pld_i) end end")
        elif op is Op.GETUPVAL:
            L.append(wr(a, self.up_read(b)))
        elif op is Op.SETUPVAL:
            L.append(self.up_write(b, rd(a)))
        elif op is Op.CLOSE:
            for i in sorted(self.boxed):
                if i >= a:
                    L.append(f"__pld_R[{i}] = {{v = __pld_R[{i}].v}}")
        elif op is Op.CLOSURE:
            caps: list[str] = []            # box arguments, `[idx]=<box expr>`
            slots: list[tuple[str, str]] = []   # the child's own upvalue slots
            for idx, ps in enumerate(self.fn.closure_pseudo[ri.pc]):
                if ps.op is Op.MOVE:
                    if ps.b not in self.boxed:
                        raise EmitError(
                            f"pc {ri.pc}: captured register {ps.b} not boxed (lift bug)")
                    caps.append(f"[{idx}]=__pld_R[{ps.b}]")      # 盒对象本身
                    slots.append((_BOX, f"__pld_U[{idx}]"))
                else:                                            # GETUPVAL 伪指令
                    kind, text = self.up_slot(ps.b)
                    if kind == _NAME:
                        # Inherited by lexical scope, not passed: the child sees
                        # the very same Lua variable the parent does, which is
                        # what makes a name slot alias correctly at all.
                        slots.append((_NAME, text))
                    else:
                        caps.append(f"[{idx}]={text}")
                        slots.append((_BOX, f"__pld_U[{idx}]"))
            # proto_path convention, hand-written here for the second of three
            # times -- see pipeline.walk_proto_paths' docstring. This key must
            # match the ledger's `proto_path` for the same proto or you lose
            # the ability to look a ledger row up in the emitted artifact.
            # `bx` is the subproto index, i.e. the same `i` that
            # walk_proto_paths and emit_chunk's walk get from enumerate().
            child = f"{self.path}_{bx}"
            if not self.inline:
                L.append(wr(a, f'__pld_F["{child}"]({{{", ".join(caps)}}})'))
            else:
                # Inline shape: the same factory, immediately invoked in place,
                # so the whole substituted subtree stays inside the one subproto
                # slot its parent's `CLOSURE` instruction points at. The box
                # arguments are evaluated in THIS function's scope, before the
                # factory's own `__pld_U` parameter shadows the name.
                sub = _FnEmitter(child, self.proto.subprotos[bx],
                                 inline=True, upslots=tuple(slots))
                cparams, cbody = sub.emit_inline(order_prologue=False)
                L.append(wr(a, f"(function(__pld_U) return function({cparams})\n"
                               f"{cbody}end end)({{{', '.join(caps)}}})"))
        else:
            raise EmitError(f"pc {ri.pc}: opcode {op.name} not yet supported by fallback")

    def _call_expr(self, ri) -> tuple[str, list[str]]:
        """返回 (调用表达式, 前置语句)。"""
        a, b = ri.a, ri.b
        if b >= 1:
            args = ", ".join(self.rd(a + 1 + i) for i in range(b - 1))
            return f"{self.rd(a)}({args})", []
        pre = [f"local __pld_t, __pld_n = {{}}, __pld_top - {a + 1}",
               f"for __pld_i = 1, __pld_n do "
               f"__pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, {a + 1} + __pld_i - 1) end"]
        return f"{self.rd(a)}(__pld_unpack(__pld_t, 1, __pld_n))", pre

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
        else:   # c == 0: open results
            L.append("do " + " ".join(pre))
            L.append(f"local __pld_rs = __pld_pack({expr})")
            L.append(f"for __pld_i = 1, __pld_rs.n do "
                     f"__pld_set(__pld_R, __pld_B, {a} + __pld_i - 1, __pld_rs[__pld_i]) end")
            L.append(f"__pld_top = {a} + __pld_rs.n end")

    # ---- 终结指令（控制流、调用全形态、open RETURN）
    def _emit_terminator(self, li: LirInstr) -> bool:
        ri = li.ri
        op, a, b = ri.op, ri.a, ri.b
        L, rd = self.lines, self.rd
        if op is Op.LOADBOOL and ri.c:
            L.append(self.wr(a, "true" if b else "false"))
            L.append(f"__pld_pc = {ri.pc + 2}")
            return True
        c = ri.c
        rk, wr = self.rk, self.wr
        if op is Op.JMP:
            L.append(f"__pld_pc = {ri.pc + 1 + ri.sbx}")
            return True
        if op in (Op.EQ, Op.LT, Op.LE):
            cmp = {Op.EQ: "==", Op.LT: "<", Op.LE: "<="}[op]
            cond = f"{rk(b)} {cmp} {rk(c)}"
            if a == 0:
                cond = f"not ({cond})"
            L.append(f"if {cond} then __pld_pc = {ri.pc + 1} "
                     f"else __pld_pc = {ri.pc + 2} end")
            return True
        if op is Op.TEST:
            t, f = (ri.pc + 1, ri.pc + 2) if c else (ri.pc + 2, ri.pc + 1)
            L.append(f"if {rd(a)} then __pld_pc = {t} else __pld_pc = {f} end")
            return True
        if op is Op.TESTSET:
            take = f"{wr(a, '__pld_t')} __pld_pc = {ri.pc + 1}"
            skip = f"__pld_pc = {ri.pc + 2}"
            branch = f"if __pld_t then {take} else {skip} end" if c else \
                     f"if __pld_t then {skip} else {take} end"
            L.append(f"do local __pld_t = {rd(b)} {branch} end")
            return True
        if op is Op.FORPREP:
            L.append("do")
            L.append(f"local __pld_i = __pld_tonumber({rd(a)}) "
                     f"if __pld_i == nil then __pld_error(\"'for' initial value must be a number\") end")
            L.append(f"local __pld_l = __pld_tonumber({rd(a + 1)}) "
                     f"if __pld_l == nil then __pld_error(\"'for' limit must be a number\") end")
            L.append(f"local __pld_s = __pld_tonumber({rd(a + 2)}) "
                     f"if __pld_s == nil then __pld_error(\"'for' step must be a number\") end")
            L.append(f"{wr(a, '__pld_i - __pld_s')} {wr(a + 1, '__pld_l')} {wr(a + 2, '__pld_s')}")
            L.append("end")
            L.append(f"__pld_pc = {ri.pc + 1 + ri.sbx}")
            return True
        if op is Op.FORLOOP:
            L.append(f"do local __pld_s = {rd(a + 2)} local __pld_i = {rd(a)} + __pld_s")
            L.append(f"if (__pld_s > 0 and __pld_i <= {rd(a + 1)}) or "
                     f"(__pld_s <= 0 and __pld_i >= {rd(a + 1)}) then")
            L.append(f"{wr(a, '__pld_i')} {wr(a + 3, '__pld_i')} "
                     f"__pld_pc = {ri.pc + 1 + ri.sbx}")
            L.append(f"else __pld_pc = {ri.pc + 1} end end")
            return True
        if op is Op.TFORLOOP:
            targets = ", ".join(rd(a + 3 + i) for i in range(c))
            L.append(f"{targets} = {rd(a)}({rd(a + 1)}, {rd(a + 2)})")
            L.append(f"if {rd(a + 3)} ~= nil then {wr(a + 2, rd(a + 3))} "
                     f"__pld_pc = {ri.pc + 1} else __pld_pc = {ri.pc + 2} end")
            return True
        if op is Op.TAILCALL:
            expr, pre = self._call_expr(ri)
            if pre:
                L.append("do " + " ".join(pre))
                L.append(f"return {expr} end")
            else:
                L.append(f"return {expr}")
            return True
        if op is Op.RETURN:            # 补齐 open 情形
            if b == 1:
                L.append("return")
            elif b >= 2:
                L.append("return " + ", ".join(rd(a + i) for i in range(b - 1)))
            else:
                L.append(f"do local __pld_t, __pld_n = {{}}, __pld_top - {a}")
                L.append(f"for __pld_i = 1, __pld_n do "
                         f"__pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, {a} + __pld_i - 1) end")
                L.append("return __pld_unpack(__pld_t, 1, __pld_n) end")
            return True
        return False


def inline_function_parts(proto: Proto, path: str,
                          upval_names: tuple[str, ...]) -> tuple[str, str]:
    """`(params, body)` for the fallback state machine of `proto`, shaped as a
    function literal the structured printer can drop straight into a hole it
    left at a CLOSURE site (M5 task 6's hybrid boundary).

    `upval_names` are the enclosing scope's OWN identifiers for this proto's
    upvalues, in upvalue-index order -- exactly the list
    `emit.lua.Printer.closure_parts` computes from the `CLOSURE`'s
    pseudo-instructions. They are referenced by name, so Lua's own upvalue
    mechanism provides the aliasing (a write on either side is seen by the
    other, and `OP_CLOSE` in the enclosing *structured* function does what the
    original did). No box protocol crosses this boundary; boxes reappear only
    strictly inside the substituted subtree, where nothing is compared.

    Two properties the enclosing function's certification depends on, both
    handled here:

    1. **One subproto slot.** The whole substituted subtree is emitted inside
       this single literal (nested functions become immediately-invoked
       factories), so the parent's `CLOSURE Bx` still points at subproto index
       `Bx` and the parent's `subprotos` tuple keeps its length.
    2. **The same captures, in the same order** -- see `emit_inline`'s
       `order_prologue`.

    Raises `EmitError` for a proto the fallback cannot express at all
    (`VARARG_NEEDSARG`); the caller then has no hybrid and ships the whole-file
    fallback.
    """
    em = _FnEmitter(path, proto, inline=True,
                    upslots=tuple((_NAME, n) for n in upval_names))
    return em.emit_inline(order_prologue=True)


def emit_chunk(root: Proto) -> bytes:
    parts: list[str] = [PRELUDE]

    def walk(path: str, p: Proto) -> None:
        # Third and last hand-written copy of the proto_path convention --
        # see pipeline.walk_proto_paths' docstring for why all three must
        # agree and what breaks silently if they drift.
        for i, s in enumerate(p.subprotos):
            walk(f"{path}_{i}", s)
        parts.append(_FnEmitter(path, p).emit())

    walk("main", root)
    parts.append('return __pld_F["main"]({})(...)\n')
    return "".join(parts).encode()
