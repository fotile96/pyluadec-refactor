"""Expression AST (spec §4). Frozen; literals keep raw payload/bytes."""
from __future__ import annotations

from dataclasses import dataclass

from pyluadec.ingest.proto import LuaNumber


@dataclass(frozen=True)
class ConstExpr:
    value: object            # None | bool | LuaNumber | bytes


@dataclass(frozen=True)
class LocalExpr:
    reg: int


@dataclass(frozen=True)
class GlobalExpr:
    name: bytes


@dataclass(frozen=True)
class UpvalExpr:
    idx: int


@dataclass(frozen=True)
class IndexExpr:
    table: "Expr"
    key: "Expr"


@dataclass(frozen=True)
class BinExpr:
    op: str
    lhs: "Expr"
    rhs: "Expr"


@dataclass(frozen=True)
class UnExpr:
    op: str
    operand: "Expr"


@dataclass(frozen=True)
class CallExpr:
    fn: "Expr"
    args: tuple["Expr", ...]
    is_method: bool = False
    method: bytes | None = None


@dataclass(frozen=True)
class VarargExpr:
    pass


@dataclass(frozen=True)
class ClosureExpr:
    proto_idx: int           # index into the enclosing Proto.subprotos


@dataclass(frozen=True)
class TableExpr:
    array: tuple["Expr", ...]
    hash: tuple[tuple["Expr", "Expr"], ...]


@dataclass(frozen=True)
class MultiSpill:
    """The 2nd..nth register of a multi-value producer whose whole result was
    staged as ONE expression in the register at `base`.

    Lua has no expression for "the second value of `f()`", so this node is
    deliberately UNPRINTABLE: `emit.lua._expr`'s fallback raises
    `ReconstructError` on it. It exists so a consumer that takes the whole
    group at once (today: `emit.lua`'s `GenericFor` arm, via
    `Reconstructor.take_expr`) can recognise and drop the spill slots, while
    any other read of one refuses cleanly instead of printing something wrong.
    See `Reconstructor._emit_multi`.
    """
    base: int


Expr = (ConstExpr | LocalExpr | GlobalExpr | UpvalExpr | IndexExpr | BinExpr
        | UnExpr | CallExpr | VarargExpr | ClosureExpr | TableExpr | MultiSpill)
