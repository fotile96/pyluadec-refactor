"""SIR region tree (spec §3 layer ③). Frozen; claimed_pcs are a disjoint partition of the function's pcs."""
from __future__ import annotations

from dataclasses import dataclass

from pyluadec.lift.lift import LirInstr


class RegionOverlap(Exception):
    pass


@dataclass(frozen=True)
class Straight:
    instrs: tuple[LirInstr, ...]
    claimed_pcs: frozenset[int]


@dataclass(frozen=True)
class Seq:
    body: tuple["Region", ...]
    claimed_pcs: frozenset[int]      # always empty; claiming delegated to body


@dataclass(frozen=True)
class If:
    cond: LirInstr
    negated: bool
    then_body: "Region"
    else_body: "Region | None"
    join_pc: int
    claimed_pcs: frozenset[int]


@dataclass(frozen=True)
class NumericFor:
    prep: LirInstr
    loop: LirInstr
    body: "Region"
    claimed_pcs: frozenset[int]


@dataclass(frozen=True)
class GenericFor:
    call: LirInstr                   # TFORLOOP
    loop: LirInstr                   # trailing JMP
    body: "Region"
    claimed_pcs: frozenset[int]


@dataclass(frozen=True)
class Break:
    claimed_pcs: frozenset[int]


@dataclass(frozen=True)
class WhileTrue:
    """`while true do <body> end`: an unconditional backward JMP closing a
    range whose head dominates it. Claims ONLY the closing JMP -- the body
    claims everything in [header, closing)."""
    body: "Region"
    closing: LirInstr                # the backward JMP closing the loop
    claimed_pcs: frozenset[int]      # exactly {closing pc}


@dataclass(frozen=True)
class While:
    """`while <cond> do <body> end` -- a loop with a real header condition.

    luac's layout (`lparser.c:whilestat`, lines 991-1007, plus `lcode.c`'s
    jump patching), with `L` the pc the closing back edge targets:

        L .. C-1:   header instructions   -- the condition's operand code
        C:          <compare / TEST>      -- the condition test itself
        C+1:        JMP -> E              -- the false-exit, out of the loop
        C+2 .. S-1: body
        S:          JMP -> L              -- the closing back edge
        E == S+1                          -- the loop's fall-through exit

    Deliberately NOT desugared to `WhileTrue` + a leading `if not c then break
    end`: that is semantically identical but recompiles to THREE instructions
    (inverted compare, JMP past the break, JMP to the exit) where the original
    has two, so it can never certify L3. Measured, M4 task 1.

    `header` is claimed by this node rather than left to a preceding sibling
    `Straight`: it re-executes on every iteration, so it belongs inside the
    loop. It must reconstruct to ZERO statements (pure operand staging into
    the Reconstructor's env) -- a Lua `while` header has nowhere to put a
    statement. `emit.lua`'s arm enforces that; see its comment for why this is
    the guard that keeps this node from silently dropping work.

    `negated` follows the same convention as `If.negated`/`Repeat.negated`
    (`ri.a == 0`) and, like both of those, is informational only: the printer
    derives polarity from the instruction's own A/C field, the single source
    of truth. NOTE (carried over from the M4 task 2 review, and true of all
    three nodes): the *name* is inverted relative to the value -- `A == 0` is
    the case where the fall-through branch is the PLAIN, un-negated
    comparison. The name is left alone here rather than renamed across three
    node types, precisely because no consumer reads it; if one ever does, the
    rename must happen first.
    """
    header: tuple[LirInstr, ...]
    cond: LirInstr
    negated: bool
    body: "Region"
    closing: LirInstr
    claimed_pcs: frozenset[int]      # header pcs + {cond pc, exit-JMP pc, closing pc}


@dataclass(frozen=True)
class Repeat:
    """`repeat <body> until <cond>`.

    Recognized since M4 task 3 (`sir/build.py::_match_repeat`), so unlike the
    "declared but never constructed" state this docstring used to describe,
    `build_sir` does build these. **It never builds one from THIS corpus**,
    though: measured M4 task 12, the 229 decompiled files contain 0 `repeat`
    and 0 `until` lines, against 971 `while` and 1482 `for` lines. The
    recognizer's evidence is therefore entirely synthetic
    (`tests/test_emit_while.py`, `tests/test_sir_build_loops.py`) -- treat
    corpus green as saying nothing about this node, and see
    MEMORY.md's "the corpus is a weaker oracle than it looks".
    """
    body: "Region"
    cond: LirInstr                   # bottom comparison/TEST
    negated: bool
    closing: LirInstr                # the conditional backward JMP
    claimed_pcs: frozenset[int]      # {cond pc, closing pc}


@dataclass(frozen=True)
class EndIter:
    """A threaded end-of-iteration JMP: a backward JMP to the current loop's
    header from inside its body, in a position where control would fall out
    of the body anyway.

    luac produces these mechanically: `luaK_jump` concatenates the list of
    jumps pending at the loop's closing JMP into that jump's own list, and
    `whilestat` then patches the whole list to the loop header. So every
    JMP-to-header other than the closing one is a jump whose *source-level*
    destination was "the end of the loop body". Prints as nothing (Task 2);
    certification adjudicates that luac re-threads it identically."""
    claimed_pcs: frozenset[int]


@dataclass(frozen=True)
class VTail:
    """The last alternative of a short-circuit value chain: a straight run
    whose net effect is to write the chain's target register.

    May be EMPTY, and that is not a degenerate case to guard against -- it is
    `lcode.c:discharge2reg` emitting nothing because the final operand is
    already sitting in the destination register (`x = <cond> and 9 or x`,
    measured on `snr_graphic.lua:main_3` pc 39). The value on that path is
    then the target register's INCOMING value, which is exactly what an empty
    run reconstructs to."""
    instrs: tuple[LirInstr, ...]


@dataclass(frozen=True)
class VAlt:
    """One short-circuiting alternative of an `and`/`or` value chain.

    Layout, with `join` the chain's single exit and `A` its target register:

        staging...                    -- operand code for `gate` (may be empty)
        gate  ; JMP -> E              -- OPTIONAL; E == test_pc + 2
        inner_staging...              -- operand code for the tested value
        test  = TESTSET A B C
                JMP -> join
        <rest continues at test_pc + 2>

    Ungated, the alternative reads `R[B] or <rest>` when `C == 1` and
    `R[B] and <rest>` when `C == 0` -- directly from `lvm.c`'s
    `l_isfalse(rb) != C` (see tests/test_express_testset.py's module
    docstring).

    Gated, it reads `(<gate> and R[B]) or <rest>`, and ONLY that: the gate is
    `lcode.c:luaK_patchtohere` retargeting a pending jump list with `NO_REG`,
    which happens for the left operand of an `or` whose own left operand is an
    `and`. `luaK_goiftrue`'s inversion is already accounted for by reading the
    gate with FALL-THROUGH polarity (`Reconstructor.condition_expr`), the same
    single source of truth `If`/`While`/`Repeat` use. A gate whose alternative
    carries `C == 0` is a different shape (`(<gate> or R[B]) and <rest>`) and
    `sir.build` refuses it rather than guessing its source form."""
    staging: tuple[LirInstr, ...]
    gate: LirInstr | None
    gate_jmp_pc: int | None
    inner_staging: tuple[LirInstr, ...]
    test: LirInstr                   # TESTSET
    test_jmp_pc: int
    rest: "VNode"


VNode = VAlt | VTail


@dataclass(frozen=True)
class CondValue:
    """`R[target] = <short-circuit and/or expression>` -- luac's VALUE idiom.

    Deliberately NOT an `If`: a TESTSET *assigns* on the branch it takes, so
    there is no if-statement reading of it (which is why M3 refused it
    outright). It is also not a `Straight`: the alternatives are conditionally
    evaluated, so their operand code must reconstruct to expressions, never to
    statements -- see `Reconstructor._refuse_statements`, the guard that keeps
    this node from claiming pcs whose work it would then never print.

    `claimed_pcs` covers the WHOLE chain (every alternative's staging, gate,
    gate JMP, test, test JMP, and the tail run), so `_CHILDREN` deliberately
    has no entry for this node."""
    target: int
    node: VNode
    claimed_pcs: frozenset[int]


def value_claimed(node: VNode) -> frozenset[int]:
    """Every pc a VNode chain occupies. Kept next to the node definitions so a
    new field cannot be added without this function being the obvious place
    that has to learn about it."""
    if isinstance(node, VTail):
        return frozenset(li.ri.pc for li in node.instrs)
    acc = {node.test.ri.pc, node.test_jmp_pc}
    acc |= {li.ri.pc for li in node.staging}
    acc |= {li.ri.pc for li in node.inner_staging}
    if node.gate is not None:
        assert node.gate_jmp_pc is not None
        acc |= {node.gate.ri.pc, node.gate_jmp_pc}
    return frozenset(acc) | value_claimed(node.rest)


@dataclass(frozen=True)
class Return:
    instr: LirInstr
    claimed_pcs: frozenset[int]


# There is deliberately NO `Fallback` region node. The M3 plan sketched one
# ("whole-function downgrade marker, claims every pc"), it was defined here
# through M4, and it was never constructed by anything -- `build_sir` raises
# `StructureError` instead and the *caller* decides, which is the discipline
# CLAUDE.md states as "识别或 StructureError，绝不猜结构". A node that no
# recognizer builds and that `emit.lua` would raise on is exactly the kind of
# dead layer the predecessor accumulated; removed at the M4 whole-branch
# review. Degrading to the M2 state machine is `structure.fallback`'s job, at
# chunk granularity, and it does not go through the region tree at all.
Region = (Straight | Seq | If | NumericFor | GenericFor | WhileTrue | While
          | Repeat | EndIter | Break | Return | CondValue)

_CHILDREN = {
    Seq: lambda r: r.body,
    If: lambda r: (r.then_body,) + ((r.else_body,) if r.else_body is not None else ()),
    NumericFor: lambda r: (r.body,),
    GenericFor: lambda r: (r.body,),
    WhileTrue: lambda r: (r.body,),
    While: lambda r: (r.body,),
    Repeat: lambda r: (r.body,),
}


def all_claimed(r: Region) -> frozenset[int]:
    acc = set(r.claimed_pcs)
    for child in _CHILDREN.get(type(r), lambda _: ())(r):
        cc = all_claimed(child)
        if acc & cc:
            raise RegionOverlap(f"pcs {sorted(acc & cc)} claimed by more than one region")
        acc |= cc
    return frozenset(acc)


def _own_enditers(r: Region) -> frozenset[int]:
    """The EndIter pcs belonging to THIS loop level -- the walk stops at a
    nested loop, whose own EndIters were already validated when that loop was
    recognized."""
    if isinstance(r, EndIter):
        return r.claimed_pcs
    if isinstance(r, Seq):
        out: frozenset[int] = frozenset()
        for c in r.body:
            out |= _own_enditers(c)
        return out
    if isinstance(r, If):
        out = _own_enditers(r.then_body)
        if r.else_body is not None:
            out |= _own_enditers(r.else_body)
        return out
    return frozenset()


def _tail_enditers(r: Region) -> frozenset[int]:
    """The EndIter pcs that print LAST on some path through `r` -- i.e. those
    an emitter can legitimately print as nothing, because falling out of `r`
    at that point executes nothing else.

    `Seq` contributes only its last child (anything earlier has statements
    after it); an `If` contributes both arms (each arm's end IS the if's end).
    Every other node contributes nothing: a `Straight`/`Return`/`Break` is not
    an EndIter, and a nested loop's tail is its own iteration's end, not this
    body's."""
    if isinstance(r, EndIter):
        return r.claimed_pcs
    if isinstance(r, Seq):
        return _tail_enditers(r.body[-1]) if r.body else frozenset()
    if isinstance(r, If):
        out = _tail_enditers(r.then_body)
        if r.else_body is not None:
            out |= _tail_enditers(r.else_body)
        return out
    return frozenset()
