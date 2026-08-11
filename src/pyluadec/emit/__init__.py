"""Structured Lua printer.

**These entry points are unverified.** `print_chunk` and friends return
whatever the region/expression trees fold to; nothing here checks that the
result recompiles to the proto it came from. Printed source must not be
shipped, written to `build/decompiled/`, or recorded in the ledger until it
has passed the L3 certification gate -- go through
`pyluadec.structure.structured.emit_certified_chunk`, which ships structured
source **iff** the root proto certified and the semantically exact fallback
chunk otherwise. Import `print_chunk` directly only for tests, debugging, and
the certification path itself.
"""
from .lua import Printer, print_chunk, print_expr, print_function, print_region

__all__ = ["Printer", "print_chunk", "print_expr", "print_function", "print_region"]
