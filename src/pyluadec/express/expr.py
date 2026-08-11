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


Expr = (ConstExpr | LocalExpr | GlobalExpr | UpvalExpr | IndexExpr | BinExpr
        | UnExpr | CallExpr | VarargExpr | ClosureExpr | TableExpr)
