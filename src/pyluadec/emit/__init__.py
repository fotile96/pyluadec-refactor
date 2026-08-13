"""Structured Lua printer.

**These entry points are unverified.** `print_chunk` and friends return
whatever the region/expression trees fold to; nothing here checks that the
result recompiles to the proto it came from. Printed source must not be
shipped, written to `build/decompiled/`, or recorded in the ledger until it
has passed the L3 certification gate -- go through
`pyluadec.structure.structured.emit_certified_chunk`, which never returns
unverified structured code.

**It is not "structured iff the root certified".** That was true through M4 and
stopped being true at M5 task 6 (this docstring said it verbatim until task 12
found it). There are three tiers: the root's own certified bytes; else a
`certify_hybrid` artifact -- structured code with the fallback state machine
substituted at the CLOSURE sites that could not be certified, shipped while the
root itself does NOT certify; else the whole-chunk fallback. On the corpus,
216 / 6 / 7 files respectively. The invariant that survives is the weaker one:
every proto in a shipped artifact is either covered by the certification that
compiled those exact bytes, or emitted by the semantically-exact fallback and
confessed in the ledger.

Import `print_chunk` directly only for tests, debugging, and the certification
path itself.
"""
from .lua import (Printer, print_chunk, print_chunk_or_raise, print_expr,
                  print_function, print_region)

# `print_chunk_or_raise` is exported alongside `print_chunk` because it is a
# real entry point, not an internal helper: `structure.structured.certify_proto`
# calls it precisely to get the refusal MESSAGE that becomes a non-`L3` ledger
# row's `refusal_reason` (M4 task 6), which `print_chunk`'s `None` cannot carry.
# It was reachable only as `pyluadec.emit.lua.print_chunk_or_raise` while its
# `None`-returning sibling was a package export, which made the package surface
# claim the pair was one function.
__all__ = ["Printer", "print_chunk", "print_chunk_or_raise", "print_expr",
           "print_function", "print_region"]
