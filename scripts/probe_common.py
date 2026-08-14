"""Shared adjudication for the probe gates (L1.5 global-state, L1.75
behaviour).

Both probes compare an original corpus file against our decompiled output and
both carry a small list of *pinned* divergences: pairs that are known not to
agree, recorded with instruction-level evidence, and asserted two-directionally
so that a changed message, a converged pair or a vanished file all fail.

The rule is one function so the standing gate (pytest) and the documented CLI
cannot drift apart on what "pass" means -- they did: probe_global_state.py's
main() knew nothing about the pins and printed "225/229" with a non-zero exit
while the suite was green.
"""
from __future__ import annotations


def adjudicate_pins(
    divergent: dict[str, tuple],
    pinned: dict[str, tuple],
) -> tuple[list[str], list[str], list[str]]:
    """`(unexpected, moved, gone)` -- each a sorted list of keys.

    `divergent` is the set of subjects that actually differ, keyed by name,
    with the evidence tuple; `pinned` is the expectation.

    The evidence tuple is deliberately UNTYPED beyond `tuple`. Only `==` is
    ever applied to it, and the three callers already disagree on its shape:
    `probe_global_state.py` pins `(str, str)`, `probe_behaviour.py` pins
    `(bytes, bytes)` -- bytes on purpose, see its `first_difference` -- and
    `probe_enum.py` pins `(str, bytes, bytes)`, adding the assignment that
    exposes the divergence, and keys on `file:proto_path` rather than on a
    file name. The annotation said `tuple[str, str]` through all of that and
    was simply false; widening it is not a loosening.

    * `unexpected` -- diverges and is not pinned: a new defect, or an old one
      that moved to a different file.
    * `moved` -- pinned, still diverges, but the evidence pair changed: the
      recorded explanation no longer describes what happens.
    * `gone` -- pinned but no longer divergent (converged, or the file is not
      in the corpus any more): the pin is stale and must be deleted, not left
      to pass silently.

    A clean gate is all three empty.
    """
    unexpected = sorted(n for n in divergent if n not in pinned)
    moved = sorted(n for n in divergent if n in pinned and divergent[n] != pinned[n])
    gone = sorted(n for n in pinned if n not in divergent)
    return unexpected, moved, gone
