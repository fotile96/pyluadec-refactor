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
class Return:
    instr: LirInstr
    claimed_pcs: frozenset[int]


@dataclass(frozen=True)
class Fallback:
    instrs: tuple[LirInstr, ...]
    claimed_pcs: frozenset[int]


Region = Straight | Seq | If | NumericFor | GenericFor | Break | Return | Fallback

_CHILDREN = {
    Seq: lambda r: r.body,
    If: lambda r: (r.then_body,) + ((r.else_body,) if r.else_body is not None else ()),
    NumericFor: lambda r: (r.body,),
    GenericFor: lambda r: (r.body,),
}


def all_claimed(r: Region) -> frozenset[int]:
    acc = set(r.claimed_pcs)
    for child in _CHILDREN.get(type(r), lambda _: ())(r):
        cc = all_claimed(child)
        if acc & cc:
            raise RegionOverlap(f"pcs {sorted(acc & cc)} claimed by more than one region")
        acc |= cc
    return frozenset(acc)
