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
class Repeat:
    """`repeat <body> until <cond>`. Declared here so Tasks 2-4 can rely on
    the name and the printer can dispatch on it; recognition is Task 3, so
    `build_sir` never constructs one yet."""
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
class Return:
    instr: LirInstr
    claimed_pcs: frozenset[int]


@dataclass(frozen=True)
class Fallback:
    instrs: tuple[LirInstr, ...]
    claimed_pcs: frozenset[int]


Region = (Straight | Seq | If | NumericFor | GenericFor | WhileTrue | Repeat
          | EndIter | Break | Return | Fallback)

_CHILDREN = {
    Seq: lambda r: r.body,
    If: lambda r: (r.then_body,) + ((r.else_body,) if r.else_body is not None else ()),
    NumericFor: lambda r: (r.body,),
    GenericFor: lambda r: (r.body,),
    WhileTrue: lambda r: (r.body,),
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
