"""M6 task 7: enumerated differential driving of ONE proto (the instrument).

The Lua side is `scripts/probe_enum.lua`; that file is the source of truth for
the stub environment, the spec-file grammar, the trace format and the frozen
budget constants. This module measures the enumeration space, encodes each
assignment, runs both sides, and adjudicates.

## What this instrument is and is not for

**Not defect hunting.** M6 measured that: six defects were confirmed in the
predecessor's shipped output and all six were found by the *static* arm, five
of them invisible to both dynamic arms; and the cheapest static instrument in
the tree (`scripts/loss_sweep.py`, 3.31s over all 1944 pairs) found everything
the graded fingerprint found plus two the fingerprint and an aggregate count
had each hidden. Task 7 was re-scoped on that evidence.

**For proving semantic equivalence where bytes differ.** When Tasks 9-12
change how a proto is reconstructed, the L3 certification gate answers "does
the recompiled proto match field-for-field". When it does not -- because the
change is a *representation* change -- there is currently no instrument that
says "and yet the two behave the same on every path this proto's own branches
can select". This is that instrument.

## What the ENUMERATION bought on this population: measured, and it is little

Two parts of this instrument are easy to conflate, and round 1 of this task's
review conflated them in four places. They are separable and they are worth
very different amounts here:

  * **The targeted named entry** (`discover` + `E`) is what found new
    behaviour. The L1.75 gate invokes every function-valued global a chunk
    defines, in one process, under one 3000-event budget; on
    `snr_common.lua` that budget is spent inside the FIRST of 79
    (`PROBE1|CAP|3001`, one `I|autoSystemSave`), so 78 of its functions are
    never called at all -- the `truncated:1/79` already on record from task 6.
    Driving `keyWait` by name reaches it in 116 events.

  * **The enumerated product** bought, on these 13 protos, **nothing that a
    single default-stub drive would not also have got**. Both pinned
    divergences reproduce under a no-assignment drive (measured directly, both
    of them). And 4 of the 10 driven rows produce exactly ONE distinct
    original-side trace across their whole product, so their "identical over
    the whole space" says no more than one point would.

  The quantitative case the enumeration DID establish is about sampling rather
  than about finding: on `snr_mainmenu.lua:main_7` only **16 of 128**
  assignments diverge (112 agree byte-for-byte), so a driver that sampled one
  point had a ~12% chance of seeing it -- it is luck, not design, that the
  default point is one of the 16. That is the measured argument for
  `budget-exceeded` being a refusal rather than a sample.

  **No row on this population makes the enumeration load-bearing.** Stated
  plainly because M7 has to decide whether to extend this instrument
  corpus-wide, and that decision should rest on what it actually bought. The
  case for keeping it is prospective, not demonstrated: Tasks 9-12 change
  reconstruction, and a representation change that is wrong on one arm of one
  branch is exactly the shape a single stub-policy drive cannot see and
  `snr_mainmenu.lua:main_7`'s 16/128 shows is easy to miss by sampling.

## The three verdicts the brief demands, and a fourth the corpus demands

`identical` / `divergent(assignment, first-diff)` / `budget-exceeded(size)` are
the brief's. **No silent sampling**: over budget is a refusal that states the
size, never a sample. If sampling is ever added it must be its own verdict
value, because "we tried a few thousand of 2^30" and "we tried all 12" are not the same
claim and a reader cannot tell them apart from a single `identical`.

`never-reached` is the fourth. It exists because of a measurement, not a
preference: this milestone repeatedly found probe arms that agreed because
they never fired -- `probe_keyseq.py` and `tests/test_keyseq_checkpoints.py`
stub the very gates that select two of the six confirmed defects, and five
authored key sequences gave byte-identical traces across three versions of one
file. **An arm that never fired is not evidence of agreement.** So a run whose
target proto was never entered reports that, and never reports `identical`.

## How "the target was entered" is established on BOTH sides

The naive reach test -- a `debug` call hook keyed on the target's
`(linedefined, lastlinedefined)` -- works only on the original: our artifact's
line numbers are the emitter's, and for every proto in this task's population
the artifact is fallback output, whose proto tree is deliberately reshaped
into `__pld_F` factories, so there is no line- or path-keyed correspondence to
compare against.

What both sides do share is the NAME the function is published under. So
`discover_entry` runs the probe in `discover` mode against the ORIGINAL
bytecode (where `linedefined`/`lastlinedefined` survive stripping and do name
the ledger's proto tree -- CLAUDE.md records 1715 of 1944 protos with nonzero
`linedefined`), walks the globals the chunk defined, and reports the ACCESS
PATHS at which a function with the target's line span is published. Both sides
are then driven with that path, and each side records its own `I|<path>` event
when the call actually happens. Reach is thus proven by an event both sides
emit, and a side that fails to publish the name at all reports `ENTRYFAIL`,
which is not a comparable value.

The residual assumption, stated rather than hidden: the two sides' functions
at the same access path are assumed to correspond. Nothing here proves it --
that is what the certification gate proves for `L3` protos and what this
instrument exists to substitute for where it cannot.

## Assignments carry values, reports carry indices

A branch constant may be a string out of the constant pool, i.e. Japanese game
text. The enumeration needs the real value (that is the whole point: `x ==
"foo"` has a true arm only if something supplies `"foo"`), so `Channel.values`
holds `bytes` and the spec file passes them as hex. Every ASCII surface --
`Assignment.name`, the CLI, the report -- names a value by its INDEX in the
channel's domain (`v0`, `v1`, ...), never by the value. `Channel.text` is the
access path, which `scripts/observation_classes.py` already measured to be
identifier-only corpus-wide (`non_identifier_names == 0`) and hex-escapes
otherwise.
"""
from __future__ import annotations

import hashlib
import itertools
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.observation_classes import (  # noqa: E402
    BUDGET, channels, domain_size, path_text,
)
from scripts.probe_common import adjudicate_pins  # noqa: E402

PROBE = ROOT / "scripts" / "probe_enum.lua"

# Markers a probe result may start with and still be COMPARED. `ENTRYFAIL|`
# and `SPECFAIL|` are deliberately absent for the L1.5 probe's reason: they
# produce the same string on both sides, so treating one as a value would
# report agreement for a run that never happened.
_MARKERS = (b"ENUM1|", b"LOADFAIL|")
_DISCOVER_MARKER = b"ENUMD1|"

VERDICTS = ("identical", "divergent", "budget-exceeded", "never-reached")


class ProbeError(RuntimeError):
    """The probe did not produce a usable result. Never silently turned into a
    comparable value."""


# --------------------------------------------------------------------------
# Channels and their value domains
# --------------------------------------------------------------------------

# Candidate "some other value" for a channel, tried in order; the first that
# is not one of the channel's own compared constants is used. It is what makes
# the domain `|constants| + 1` rather than `|constants|`: the arm where NONE of
# the equality tests hold. `False` leads because it is also falsy, so for a
# channel that is only truth-tested the two-element domain is exactly
# {falsy, truthy}.
_OTHER_CANDIDATES: tuple[object, ...] = (False, True, b"__pld_other", 0.0)


@dataclass(frozen=True)
class Channel:
    """One access path a proto's branches read, with the ordered value domain
    the enumeration walks.

    `path` is `observation_classes.channels`' segment tuple; `text` its ASCII
    rendering; `values` the real Lua values (bytes / float / bool / None).
    """
    path: tuple
    text: str
    values: tuple

    def value_name(self, i: int) -> str:
        """`v0`, `v1`, ... -- the only way a value is ever named in ASCII."""
        return f"v{i}"


@dataclass(frozen=True)
class Assignment:
    """One point of the enumerated product: an index into each channel's
    domain, in channel order."""
    indices: tuple[int, ...]
    channels: tuple[Channel, ...]

    @property
    def name(self) -> str:
        """`pressButton()=v0,systemSave.libFlag=v1` -- indices, never values.
        This is what a `divergent` verdict names, so it has to be both stable
        and free of corpus text."""
        return ",".join(f"{c.text}={c.value_name(i)}"
                        for c, i in zip(self.channels, self.indices))

    def values(self) -> tuple:
        return tuple(c.values[i] for c, i in zip(self.channels, self.indices))


def _canon_value(canon) -> object:
    """`observation_classes.channels`' `canon` tuple back to a Lua value."""
    kind = canon[0]
    if kind == "nil":
        return None
    if kind == "b":
        return canon[1]
    if kind == "n":
        return float(canon[1])
    return canon[1]           # ("s", bytes)


def _sort_key(canon) -> tuple:
    """Deterministic order over a channel's raw constants. Kind first so the
    ordering never depends on comparing a `bytes` with a `float`."""
    kind = canon[0]
    if kind == "nil":
        return (0, 0.0, b"")
    if kind == "b":
        return (1, float(canon[1]), b"")
    if kind == "n":
        return (2, float(canon[1]), b"")
    return (3, 0.0, canon[1])


def channels_of(proto) -> tuple[Channel, ...]:
    """The proto's branch channels, in `path_text` order, each with its
    enumerated domain. `channels_and_floors(proto)[0]`."""
    return channels_and_floors(proto)[0]


def channels_and_floors(proto) -> tuple[tuple[Channel, ...], int]:
    """`(channels, register_comparisons)`.

    The second element is `observation_classes.channels`' `n_unresolved`: the
    number of comparisons whose other side is a REGISTER, not a constant, so
    the channel's domain is not the compared set but the two-element
    `{falsy, truthy}` FLOOR. `classes.json` publishes it per record as
    `register_comparisons` precisely so a floor-based space is visible to a
    reader; this instrument used to discard it (`ch, _unresolved = ...`), so
    an `identical` verdict resting entirely on floors was indistinguishable
    from one over a fully enumerated domain. It is carried onto `EnumVerdict`
    instead -- see that class's `identical` bullet.

    **Where this can disagree with `classes.json`'s `input_space`, and why.**
    That file's `domain` is `len(rec["cmp"]) + 1`, and `cmp` holds
    `const_lit` renderings, which collapse every string to `"str"` and every
    non-integer number to `"num"`. Two distinct string constants compared
    against one channel are one element there and two here. The enumeration
    has to use the finer set -- a run that supplies `"a"` does not take the
    `== "b"` arm -- so this function's product is `>=` the published
    `input_space`, and `exhaust` compares ITS OWN size against the budget.
    """
    ch, unresolved = channels(proto)
    out = []
    for path in sorted(ch, key=path_text):
        rec = ch[path]
        raw = sorted(rec["raw"], key=_sort_key)
        vals = [_canon_value(c) for c in raw]
        if vals:
            for cand in _OTHER_CANDIDATES:
                if not any(_same(cand, v) for v in vals):
                    vals.append(cand)
                    break
            else:                                      # pragma: no cover
                raise AssertionError(
                    f"no distinct 'other' value for channel {path_text(path)}")
        else:
            # No constant comparison: a plain truth test (or a comparison
            # against another register, whose domain is unknown). Two
            # elements, falsy and truthy -- the same floor `domain_size`
            # publishes, and `register_comparisons` is where that floor is
            # visible as a floor.
            vals = [False, True]
        out.append(Channel(path=path, text=path_text(path),
                           values=tuple(vals)))
    return tuple(out), unresolved


def _same(a, b) -> bool:
    return type(a) is type(b) and a == b


def space_size(chans) -> int:
    n = 1
    for c in chans:
        n *= len(c.values)
    return n


def published_space(proto) -> int:
    """`classes.json`'s `input_space` for the same proto, recomputed. Only
    used to report where the two disagree."""
    ch, _ = channels(proto)
    n = 1
    for rec in ch.values():
        n *= domain_size(rec)
    return n


def enumerate_assignments(chans):
    """Every point of the product, in a fixed order: channel order is
    `path_text`, value order is `_sort_key` then the `other` value last, and
    `itertools.product` varies the LAST channel fastest. Deterministic so a
    `divergent` verdict names a reproducible assignment."""
    for idx in itertools.product(*[range(len(c.values)) for c in chans]):
        yield Assignment(indices=idx, channels=tuple(chans))


# --------------------------------------------------------------------------
# Spec-file encoding
# --------------------------------------------------------------------------

def encode_path(path) -> str:
    out = []
    for kind, val in path:
        if kind == "k":
            out.append("k" + val.hex())
        elif kind == "i":
            out.append(f"i{val}")
        elif kind == "d":
            out.append("d")
        else:
            out.append("c")
    return "/".join(out)


def encode_value(v) -> str:
    if v is None:
        return "x"
    if v is True or v is False:
        return "b1" if v else "b0"
    if isinstance(v, bytes):
        return "s" + v.hex()
    f = float(v)
    # `%.17g` renders a non-finite as `inf`/`nan`, and the probe's
    # `parse_value` calls `tonumber`, which returns nil for both -- a silently
    # WRONG assignment rather than a refused one. Unreachable on this corpus
    # (a `luac` constant pool can hold an infinity, but no comparison constant
    # in these 229 files is non-finite), so this is covered synthetically.
    if f != f or f in (float("inf"), float("-inf")):
        raise ProbeError(f"non-finite comparison constant {f!r} cannot be "
                         f"encoded: the probe's tonumber would read it as nil")
    return "n%.17g" % f


def spec_lines(mode: str, *, entry: str | None = None,
               assignment: Assignment | None = None,
               lines: tuple[int, int] | None = None) -> bytes:
    out = [f"M {mode}"]
    if lines is not None:
        out.append(f"D {lines[0]} {lines[1]}")
    if entry:
        out.append(f"E {entry}")
    if assignment is not None:
        for c, i in zip(assignment.channels, assignment.indices):
            out.append(f"A {encode_path(c.path)} {encode_value(c.values[i])}")
    return ("\n".join(out) + "\n").encode("ascii")


# --------------------------------------------------------------------------
# Running one side
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Trace:
    """One side's observation of one assignment.

    `raw` is the whole stdout, bytes -- the trace embeds string constants
    straight from the corpus and nothing here decodes them. `body` is what the
    comparison uses; today it is `raw`, and it is a separate field so a future
    footer (a coverage badge, say) can be excluded from the comparison without
    the comparison silently changing meaning.
    """
    raw: bytes
    status: str
    n_events: int
    entered: bool

    @property
    def body(self) -> bytes:
        return self.raw


def _header(raw: bytes) -> tuple[str, int]:
    line = raw.split(b"\n", 1)[0]
    parts = line.split(b"|")
    if parts[0] == b"LOADFAIL":
        return "LOADFAIL", -1
    return parts[1].decode("ascii"), int(parts[2])


@lru_cache(maxsize=None)
def _decompiled(path_str: str) -> bytes:
    from pyluadec.pipeline import decompile_file
    return decompile_file(Path(path_str)).source


def _payload(file: Path, side: str) -> tuple[bytes, bool]:
    if side == "original":
        return file.read_bytes(), False
    if side == "decompiled":
        return _decompiled(str(file)), True
    raise ValueError(f"unknown side {side!r}")


def _run(payload: bytes, is_source: bool, spec: bytes, *,
         timeout: float = 180.0) -> bytes:
    from pyluadec import oracle
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / ("t.lua" if is_source else "t.luac")
        f.write_bytes(payload)
        sp = Path(td) / "spec"
        sp.write_bytes(spec)
        # stdin=DEVNULL: a chunk that calls io.read() would otherwise block on
        # whatever the caller's stdin happens to be, and a probe that hangs is
        # an instrument that never reports.
        r = subprocess.run([str(oracle.lua_sz4()), str(PROBE), str(f), str(sp)],
                           capture_output=True, stdin=subprocess.DEVNULL,
                           timeout=timeout, cwd=td)
    if r.returncode != 0:
        raise ProbeError(
            f"probe exited {r.returncode}; "
            f"stderr={r.stderr.decode('utf-8', 'replace')!r}; "
            f"stdout={r.stdout[:400].decode('utf-8', 'replace')!r}")
    return r.stdout


def drive(file, proto_path: str, assignments, *, side: str = "original",
          entry: str | None = None) -> Trace:
    """Run ONE side of ONE assignment and return its trace.

    `assignments` is an `Assignment` (the enumerated point) or `None` for the
    unassigned run. `entry` is the encoded access path to call; `None` means
    the chunk body alone is the observation, which is what `proto_path ==
    "main"` needs.

    `proto_path` is carried for the caller's bookkeeping and to resolve the
    default entry; the probe itself is told a NAME, never a path.
    """
    file = Path(file)
    if entry is None and proto_path != "main":
        entry = _entry_for(file, proto_path)
    payload, is_source = _payload(file, side)
    raw = _run(payload, is_source, spec_lines("drive", entry=entry,
                                              assignment=assignments))
    if not raw.startswith(_MARKERS):
        raise ProbeError(
            f"probe produced an unrecognisable result for {file.name}:"
            f"{proto_path} on the {side} side; "
            f"stdout={raw[:400].decode('utf-8', 'replace')!r}")
    status, nev = _header(raw)
    # Reach is the `R|<name>|` COMPLETION event, never the `I|<name>` intent
    # event. `probe_enum.lua` appends `I|` and then checks the budget before
    # calling: an assignment whose chunk body emits exactly MAX_EVENTS-1
    # events makes the `I|` itself the event that trips the cap, so the call
    # is skipped and the target executes NOTHING -- and an `I|`-keyed test
    # calls that "entered". Constructed and confirmed at 2997 / 2998 / 2999
    # chunk-body events -> identical / identical(vacuous) / never-reached;
    # with this check the middle case is `never-reached` too. No instance
    # among the 13 shipped protos (all 182 driven assignments carry an `R|`),
    # so no committed verdict changes -- but this is the silent-arm failure
    # mode this milestone keeps paying for.
    entered = True
    if entry is not None:
        marker = b"R|" + path_text_of(entry).encode("ascii") + b"|"
        entered = any(line.startswith(marker) for line in raw.split(b"\n"))
    return Trace(raw=raw, status=status, n_events=nev, entered=entered)


def path_text_of(encoded: str) -> str:
    """The `I|`/`R|` event's rendering of an encoded access path -- the same
    function `probe_enum.lua::path_text` implements, so the driver can
    recognise its own entry events.

    `.` `/` `\\` `|` and every non-printable byte render as hex. The last two
    are there for correctness, not looks: the trace line goes through the
    probe's `esc`, which rewrites exactly `\\` and `|`, so a key containing
    either would never match this rendering and `entered` would be
    permanently false -- a spurious `never-reached`. Escaping them makes `esc`
    a no-op on the result. Unreachable on this corpus
    (`non_identifier_names == 0`), so it is covered synthetically."""
    out = []
    for i, tok in enumerate(encoded.split("/")):
        kind = tok[0]
        if kind == "k":
            v = bytes.fromhex(tok[1:])
            ok = all(0x20 <= b <= 0x7e and b not in (0x2e, 0x2f, 0x5c, 0x7c)
                     for b in v)
            out.append(("." if i else "")
                       + (v.decode("ascii") if ok else "0x" + v.hex()))
        elif kind == "i":
            out.append(f"[{tok[1:]}]")
        elif kind == "d":
            out.append("[*]")
        else:
            out.append("()")
    return "".join(out)


# --------------------------------------------------------------------------
# Entry discovery
# --------------------------------------------------------------------------

def _proto_at(file: Path, proto_path: str):
    from pyluadec.ingest import load_file
    from pyluadec.pipeline import walk_proto_paths
    protos: dict = {}
    walk_proto_paths("main", load_file(file), protos)
    return protos, protos[proto_path]


@lru_cache(maxsize=None)
def discover_entries(file_str: str, proto_path: str) -> tuple[str, ...]:
    """Encoded access paths at which the ORIGINAL chunk publishes a function
    whose line span is the target proto's, sorted.

    Empty when the proto is not published under any name the walk reaches --
    a nested helper closure, or one only stored in a table deeper than
    `DISCOVER_DEPTH`. That is a `never-reached` verdict, not a failure.

    Raises when the line span is not unique within the file: two protos with
    the same `(linedefined, lastlinedefined)` would make the discovered name
    ambiguous, and an ambiguous reach claim is worse than none.
    """
    file = Path(file_str)
    protos, target = _proto_at(file, proto_path)
    span = (target.linedefined, target.lastlinedefined)
    twins = [p for p, q in protos.items()
             if (q.linedefined, q.lastlinedefined) == span]
    if len(twins) != 1:
        raise ProbeError(
            f"{file.name}:{proto_path} has line span {span} shared with "
            f"{len(twins) - 1} other proto(s) ({sorted(twins)}); entry "
            f"discovery would be ambiguous")
    raw = _run(file.read_bytes(), False, spec_lines("discover", lines=span))
    if not raw.startswith(_DISCOVER_MARKER):
        raise ProbeError(
            f"discovery produced an unrecognisable result for {file.name}:"
            f"{proto_path}; stdout={raw[:400].decode('utf-8', 'replace')!r}")
    out = []
    for line in raw.split(b"\n")[1:]:
        if line.startswith(b"E|"):
            out.append(line[2:].split(b"|")[1].decode("ascii"))
    return tuple(sorted(out))


def _entry_for(file: Path, proto_path: str) -> str | None:
    hits = discover_entries(str(file), proto_path)
    return hits[0] if hits else None


# --------------------------------------------------------------------------
# The verdict
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class EnumVerdict:
    """`kind` is one of `VERDICTS`.

    * `identical`       -- every assignment in the FULL product produced
                           byte-equal traces on both sides, and the target was
                           entered on every one of them. `n_assignments`
                           equals `space_size` here; the two fields are
                           separate so that a future sampling verdict cannot
                           be mistaken for this one by a reader who only looks
                           at one of them.

    **What the product does NOT range over, stated here because this is where
    "the FULL product" is asserted.** The enumeration's channels come from
    `observation_classes.channels`, which only sees branch inputs reachable as
    a named access path off the stub environment. Three classes of branch
    contribute NO channel at all, so an `identical` verdict is silent about
    them (the limitation is also recorded at `observation_classes.py`'s
    `channels` and in `probe_enum.lua`'s SCOPE block):

      1. **Branches on a PARAMETER.** `drive` calls the discovered entry with
         no arguments, so a parameter is always nil and the arm selected by
         any other value is never taken. Constructed witness, measured
         2026-08-14: `function f(x) if x == 1 then engine.A() else
         engine.B() end end` against a copy differing ONLY on the `x == 1`
         arm returns `identical` over `space_size == 1`.
      2. **Access paths deeper than `observation_classes.MAX_PATH_DEPTH`**
         (8): the walk stops, so the read is not a channel.
      3. **Register-vs-register comparisons**: neither side is a constant, so
         there is no domain to enumerate. These become the two-element
         `{falsy, truthy}` FLOOR and are counted in
         `n_register_comparisons` -- a nonzero value there means part of this
         verdict's product is a floor, not the compared set.

    `n_assignments` is the number of assignments whose comparison was
    ADJUDICATED, which on the `divergent` path is the 1-based index of the
    first differing one and NOT `len(todo)`: `exhaust` returns as soon as it
    sees a difference. It is deliberately not "subprocesses launched", which
    is larger and nondeterministic -- `ThreadPoolExecutor.map` keeps up to
    `jobs` comparisons in flight and cancels the rest when the generator is
    abandoned, so a `divergent` run over this population launches ~230 drive
    processes across three measured runs where the adjudicated counts sum to
    115. `distinct_traces` is likewise over the adjudicated prefix.
    * `divergent`       -- `assignment` is the first (in enumeration order)
                           whose traces differ; `first_diff` is
                           `(line number, original line, decompiled line)` as
                           raw bytes.
    * `budget-exceeded` -- `space_size` exceeds `BUDGET`; NOTHING was run.
    * `never-reached`   -- the target proto could not be entered; `detail`
                           says why. Never conflated with `identical`.
    """
    kind: str
    file: str
    proto_path: str
    space_size: int
    n_assignments: int = 0
    n_channels: int = 0
    n_register_comparisons: int = 0
    entry: str | None = None
    entries: tuple[str, ...] = ()
    distinct_traces: int = 0
    assignment: Assignment | None = None
    first_diff: tuple[int, bytes, bytes] | None = None
    detail: str = ""
    statuses: tuple[str, ...] = ()

    def __post_init__(self):
        assert self.kind in VERDICTS, self.kind


def first_difference(a: bytes, b: bytes) -> tuple[int, bytes, bytes]:
    """`(line number, original line, decompiled line)`, raw bytes -- the same
    type the trace is in, for the reason `probe_behaviour.first_difference`
    records: decoding first would make an evidence pin blind to two different
    undecodable byte runs that decode to the same replacement text."""
    la, lb = a.split(b"\n"), b.split(b"\n")
    for i in range(max(len(la), len(lb))):
        x = la[i] if i < len(la) else b"<end of trace>"
        y = lb[i] if i < len(lb) else b"<end of trace>"
        if x != y:
            return (i + 1, x, y)
    return (0, b"", b"")


def exhaust(file, proto_path: str, *, jobs: int = 8,
            budget: int = BUDGET) -> EnumVerdict:
    """Drive both sides over the WHOLE enumerated product and adjudicate.

    `budget` is a parameter only so a test can prove the refusal path with a
    small space instead of constructing a 4097-point one; every production
    caller takes the default, which is
    `scripts/observation_classes.py::BUDGET` -- the single place the figure
    lives.
    """
    file = Path(file)
    _protos, proto = _proto_at(file, proto_path)
    chans, floors = channels_and_floors(proto)
    size = space_size(chans)
    common = dict(file=file.name, proto_path=proto_path, space_size=size,
                  n_channels=len(chans), n_register_comparisons=floors)
    if size > budget:
        return EnumVerdict(kind="budget-exceeded", **common)

    entry = None
    hits: tuple[str, ...] = ()
    if proto_path != "main":
        hits = discover_entries(str(file), proto_path)
        if not hits:
            return EnumVerdict(
                kind="never-reached", detail="no published name reaches the "
                "proto's line span", **common)
        # A proto CAN be published under several names (`Alpha = f; Beta = f`).
        # The first in sorted order is driven and the rest are carried on the
        # verdict rather than silently dropped: they are the same function, so
        # driving one is driving the proto, but a reader comparing two runs
        # needs to see that a choice was made. No corpus row has more than one
        # (measured over all 13, 2026-08-14).
        entry = hits[0]
    common["entry"] = entry
    common["entries"] = hits

    todo = list(enumerate_assignments(chans))

    def one(a: Assignment):
        return (a,
                drive(file, proto_path, a, side="original", entry=entry),
                drive(file, proto_path, a, side="decompiled", entry=entry))

    statuses: set[str] = set()
    n_entered = 0
    n_adjudicated = 0
    seen: set[bytes] = set()
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        for a, t0, t1 in ex.map(one, todo):
            statuses.add(t0.status)
            statuses.add(t1.status)
            n_adjudicated += 1
            seen.add(hashlib.sha256(t0.body).digest())
            if t0.body != t1.body:
                return EnumVerdict(kind="divergent", assignment=a,
                                   first_diff=first_difference(t0.body, t1.body),
                                   n_assignments=n_adjudicated,
                                   distinct_traces=len(seen),
                                   statuses=tuple(sorted(statuses)), **common)
            if t0.entered and t1.entered:
                n_entered += 1
    common["distinct_traces"] = len(seen)
    if n_entered == 0:
        return EnumVerdict(
            kind="never-reached", n_assignments=n_adjudicated,
            statuses=tuple(sorted(statuses)),
            detail="the entry was named but never called on any assignment",
            **common)
    if n_entered != n_adjudicated:
        return EnumVerdict(
            kind="never-reached", n_assignments=n_adjudicated,
            statuses=tuple(sorted(statuses)),
            detail=f"the target was entered on {n_entered} of {n_adjudicated} "
                   f"assignments; agreement on the rest is not evidence "
                   f"about this proto",
            **common)
    return EnumVerdict(kind="identical", n_assignments=n_adjudicated,
                       statuses=tuple(sorted(statuses)), **common)


# --------------------------------------------------------------------------
# Pinned divergences
# --------------------------------------------------------------------------

# The compound-`if` leaf protos whose two sides do NOT agree, pinned as
# `(assignment, original line, decompiled line)` so that a changed message, a
# different assignment, a converged pair or a vanished proto all fail
# adjudication. Same vocabulary and same `adjudicate_pins` rule as the L1.5 and
# L1.75 gates -- one function, so the CLI and the gate cannot drift apart on
# what "pass" means.
#
# BOTH pins are the SAME already-documented class: the `getobjname` naming
# artifact of the fallback's `__pld_R` box model, pinned for `snr_mainmenu.lua`
# in `probe_global_state.py` and `probe_behaviour.py` since M3. `ldebug.c`'s
# `kname()` names an operand only when the instruction that produced it is a
# `GETTABLE`/`GETGLOBAL` with a STRING constant key; the fallback state machine
# routes every register through `__pld_R[<number>]`, so the key is a NUMBER
# constant and `kname` says `field '?'`. Only the noun in an error MESSAGE
# differs; the two sides fail at the same instruction with the same error kind.
# Both should CONVERGE when the code on the failing path stops going through
# the box model -- at which point adjudication reports `gone` and the pin must
# be deleted, not left to pass silently. That happened to
# `snr_mainmenu.lua:main_7` in M6 task 12: all 128 of its assignments are now
# byte-identical and its entry was deleted below, exactly as this comment
# prescribes.
#
# **Not because it certifies.** Round-1 correction: this comment first said
# task 12 "lifted that chunk's `main` to `L3`", which is false twice over --
# `snr_mainmenu.lua:main` is `L1` (`mismatch: code at root/7`) and `main_7`
# itself is `L1` with `shipped: "fallback"`, i.e. the pinned proto is STILL
# emitted by the state machine. What changed is that the file went from
# whole-file fallback to HYBRID, so the enclosing frames on the failing path
# ship structured text and the `GETTABLE` that composes the message now
# carries its string key on both sides. The file still emits `__pld_R` on 1974
# of 3325 lines (3220 of 4782 before), 18 of them the `["library"]` lines this
# pin was about.
#
# The attribution is also joint, not single: measured by a source-level 4-way
# ablation over all 229 files, neither the constructor-read fix nor the
# closure-capture fix changes one byte of shipped output on its own; only both
# together do. The same convergence removed the file's pins in
# `probe_global_state.py` and `probe_behaviour.py`. `snr_common.lua:main_81`
# remains: `snr_common.lua` still ships whole-file fallback.
#
# `snr_common.lua:main_81` (`keyWait`) is a NEW instance of that class. It is
# new because of the TARGETED NAMED ENTRY, not because of the enumeration --
# an earlier version of this comment claimed the latter and it is measured
# FALSE (round 1). What actually happens, all re-measured 2026-08-14:
#
#   * Driving `keyWait` with NO ASSIGNMENT AT ALL -- i.e. exactly the L1.75
#     stub policy -- already produces this divergence.
#   * BOTH assignments reach the `DIV` and produce byte-identical 116-event
#     traces on the original side. `pressButton() == false` does NOT return
#     early: pc 12's `EQ 0 R3 K(true)` fails, so pc 13's `JMP -> 16` is taken
#     straight to the `DIV`; `pressButton() == true` skips pc 13, falls
#     through pc 14's `EQ 1 R2 K(0)` (R2 is 1 from pc 2's `LOADK`) and skips
#     pc 15's `JMP -> 26`, arriving at pc 16 as well.
#   * What the L1.75 gate actually misses it by is TRUNCATION:
#     `probe_raw(snr_common.lua)` returns `PROBE1|CAP|3001` having invoked
#     exactly ONE of the file's 79 function-valued globals (`I|autoSystemSave`
#     -> `R|autoSystemSave|CAP`). This is the `truncated:1/79` already on
#     record from task 6. `keyWait` is never invoked at all.
#
# Instruction-level evidence, original bytecode, 1-based pcs (as
# `pyluadec.lift` and `luac -l -l` both number them):
#   pc 2     `LOADK R2 K(1)`
#   pc 3-5   `GETGLOBAL R3 "pressButton"; LOADK R4 "CIRCLE"; CALL R3 2 2`
#   pc 12-13 `EQ 0 R3 K(true); JMP -> 16`
#   pc 14-15 `EQ 1 R2 K(0); JMP -> 26`
#   pc 16    `DIV R3 R0 K(<number>)` -- R0 is the parameter, and the probe
#            calls every function with no arguments, so R0 is nil.
# The original's `DIV` operand is a bare register with no `locvars` (the corpus
# is stripped), so `kname` finds nothing and Lua says "arithmetic on a nil
# value"; the fallback's operand came from `__pld_R[0]`, so `kname` says
# "field '?'". The pinned assignment is `pressButton()=v0` only because it is
# the FIRST in enumeration order; `v1` diverges identically.
EXPECTED_DIVERGENCE: dict[str, tuple[str, bytes, bytes]] = {
    "snr_common.lua:main_81": (
        # Evidence moved 2026-08-15, M7 task 6: snr_common flipped whole-file
        # fallback -> HYBRID (dynamic-key constructor fix), so the divergent
        # side's error names the re-emitted local instead of the fallback box
        # operand. Same divergence class (nil arithmetic in keyWait under
        # stub-driven assignments), same assignment, byte-precise per the
        # instrument's contract.
        "pressButton()=v0",
        b"R|keyWait|attempt to perform arithmetic on a nil value",
        b"R|keyWait|attempt to perform arithmetic on local 'l1_0' (a nil value)"),
}


def evidence(v: EnumVerdict) -> tuple[str, bytes, bytes]:
    """The pinned form of a `divergent` verdict."""
    assert v.kind == "divergent", v.kind
    return (v.assignment.name, v.first_diff[1], v.first_diff[2])


# --------------------------------------------------------------------------
# Pinned REFUSALS
# --------------------------------------------------------------------------

#: The two verdicts that are refusals: the instrument declines to make a claim
#: about the proto. `budget-exceeded` ran nothing; `never-reached` ran nothing
#: that entered the target. Neither is evidence of agreement.
REFUSALS = ("budget-exceeded", "never-reached")

# The population rows the instrument REFUSES, adjudicated exactly like the
# divergences above and with the same `adjudicate_pins` rule, so a row that
# starts refusing, stops refusing, or refuses for a different reason all fail.
#
# This exists because the exit contract used to be
# `return 1 if (unexpected or moved or gone) else 0` over the divergences
# ALONE, so a silently-growing refused set sat behind a green exit code. The
# full-population run printed `budget-exceeded 1, never-reached 2` and exited
# 0 -- one proto never driven, two never entered, green. CLAUDE.md's
# out-of-suite criterion points at this instrument as the exemplar of "自带上
# 界并在越界时拒绝 ... 非零退出", and until this table existed that property
# was true of the report and false of the exit code. M7 agenda 8 is the
# corpus-wide extension of this instrument, which is exactly where a growing
# refused set would hide.
#
# Re-derived from the instrument 2026-08-14 (`uv run python
# scripts/probe_enum.py`), never by hand. `space`/`channels` come from
# `channels_of`, NOT from `classes.json`'s `input_space`: for
# `snr_s4_10_s.lua:main_58` the published figure is 1152 and the enumerable
# space is 23616, a 20x difference, because `classes.json` collapses every
# string constant to `"str"` (see `channels_and_floors`).
EXPECTED_REFUSALS: dict[str, tuple[str, str]] = {
    "snr_fragment_main.lua:main_1": (
        "never-reached", "no published name reaches the proto's line span"),
    "snr_s4_10_s.lua:main_58": (
        "budget-exceeded", "space=23616 channels=7"),
    "snr_story_main.lua:main_1": (
        "never-reached", "no published name reaches the proto's line span"),
}


def refusal_evidence(v: EnumVerdict) -> tuple[str, str]:
    """The pinned form of a refusal verdict: `(kind, why)`.

    `why` is the instrument's own `detail` for `never-reached` (a fixed
    English sentence, or the `entered on N of M` count) and the measured space
    for `budget-exceeded`. Both are free of corpus text, like every other
    ASCII surface in this module.
    """
    assert v.kind in REFUSALS, v.kind
    if v.kind == "budget-exceeded":
        return (v.kind, f"space={v.space_size} channels={v.n_channels}")
    return (v.kind, v.detail)


def pins_for(table: dict, population) -> dict:
    """`table` restricted to the rows `population` actually drove.

    Single-proto CLI mode used to adjudicate a one-row population against the
    WHOLE pin table, so every per-proto debugging run except
    `snr_common.lua main_81` reported the other pins as `gone` and exited 1 --
    the documented per-proto command was unusable in a script. A pin says
    nothing about a run that did not include its proto.
    """
    keys = {f"{f}:{p}" for f, p in population}
    return {k: v for k, v in table.items() if k in keys}


# --------------------------------------------------------------------------
# The population, and the CLI
# --------------------------------------------------------------------------

def compound_if_leaves(ledger_rows) -> list[tuple[str, str]]:
    """The protos this task's demonstration runs over: the `structure:`
    refusals whose refusal is their OWN, not inherited from a descendant.

    Measured at task 7 (2026-08-14) over `corpus/ledger.jsonl`: the
    `structure:` family was **21 shapes**, of which **13 were leaves** and 8
    ancestors carrying a descendant's reason verbatim (the ledger copies the
    reason up, so `snr_story_main.lua:main`, 10 instructions, was recorded as
    refusing at "pc 131"). The leaf/ancestor split is decided here the same
    way `observation_classes.refusal_origin` decides it -- by re-running
    `build_sir` on the proto alone -- and the two agreed on all 21.

    **Re-measured after task 11 (2026-08-14): 1 shape, 1 leaf**
    (`snr_common.lua:main_71`). The condition-tree recognizer closed the other
    20; 7 of them reached `L3` and 13 moved to the `mismatch:` family, which
    this function does not select. The task-7 population is preserved verbatim
    as `M6_TASK11_POPULATION` and that -- not this derivation -- is what the
    CLI and the standing gate now drive, for the reason given there.
    """
    from pyluadec.ingest import load_file
    from pyluadec.lift.lift import lift_proto
    from pyluadec.pipeline import walk_proto_paths
    from pyluadec.sir.build import build_sir, StructureError

    corpus = Path(os.environ["PYLUADEC_CORPUS_DIR"])
    trees: dict[str, dict] = {}
    out = []
    for row in ledger_rows:
        reason = row.get("refusal_reason") or ""
        if not reason.startswith("structure:"):
            continue
        for occ in row["occurrences"]:
            f, path = occ["file"], occ["proto_path"]
            if f not in trees:
                protos: dict = {}
                walk_proto_paths("main", load_file(corpus / f), protos)
                trees[f] = protos
            try:
                build_sir(lift_proto(trees[f][path]))
            except StructureError:
                out.append((f, path))
    return sorted(set(out))


#: The population `compound_if_leaves` returned when this instrument was
#: built (task 7, 2026-08-14), frozen as a literal because task 11 then CLOSED
#: most of it: the derivation above now returns one row
#: (`snr_common.lua:main_71`), so a ledger-derived population would silently
#: stop exercising the twelve protos whose region trees task 11 changed --
#: which is exactly when running them matters most.
#:
#: This list is therefore a PROSPECTIVE population, not a defect census and
#: not evidence about task 11. Six of the eight files holding these protos
#: ship byte-identical artifacts across task 11 (measured 2026-08-14: still
#: whole-file fallback or an unchanged hybrid), and the two that changed hold
#: exactly the two rows `exhaust` reports as `never-reached` -- so the
#: verdicts here could not have moved, and their not moving proves nothing.
#: What it buys is the future: when one of these files stops shipping
#: fallback, this is the instrument that starts driving its new artifact, and
#: a ledger-derived population (now one row) would not include it.
#:
#: It is correct for this list to go stale relative to `compound_if_leaves`;
#: what it must not do is shrink. `tests/test_probe_enum.py` asserts both
#: halves: that every member is still adjudicated with the verdict task 7
#: measured, and that the live derivation has moved to 1.
M6_TASK11_POPULATION: tuple[tuple[str, str], ...] = (
    ("snr_common.lua", "main_71"),
    ("snr_common.lua", "main_74_13"),
    ("snr_common.lua", "main_76_2"),
    ("snr_common.lua", "main_76_8"),
    ("snr_common.lua", "main_81"),
    ("snr_fragment_main.lua", "main_1"),
    ("snr_graphic.lua", "main"),
    ("snr_graphic.lua", "main_4"),
    ("snr_mainmenu.lua", "main_7"),
    ("snr_memory.lua", "main_4"),
    ("snr_music.lua", "main_3"),
    ("snr_s4_10_s.lua", "main_58"),
    ("snr_story_main.lua", "main_1"),
)


def _read_ledger() -> list[dict]:
    import json
    with open(ROOT / "corpus" / "ledger.jsonl", "rb") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) == 2:
        population = [(argv[0], argv[1])]
    else:
        population = list(M6_TASK11_POPULATION)
    corpus = Path(os.environ["PYLUADEC_CORPUS_DIR"])
    counts: dict[str, int] = {k: 0 for k in VERDICTS}
    divergent: dict[str, tuple] = {}
    refused: dict[str, tuple] = {}
    for f, path in population:
        v = exhaust(corpus / f, path)
        counts[v.kind] += 1
        extra = ""
        if v.kind == "divergent":
            divergent[f"{f}:{path}"] = evidence(v)
            extra = f"  assignment={v.assignment.name}  line {v.first_diff[0]}"
        elif v.kind == "never-reached":
            refused[f"{f}:{path}"] = refusal_evidence(v)
            extra = f"  ({v.detail})"
        elif v.kind == "budget-exceeded":
            refused[f"{f}:{path}"] = refusal_evidence(v)
            extra = "  (nothing run)"
        print(f"{f}:{path:12} {v.kind:16} channels={v.n_channels} "
              f"floors={v.n_register_comparisons} "
              f"space={v.space_size} run={v.n_assignments} "
              f"distinct={v.distinct_traces} "
              f"statuses={','.join(v.statuses) or '-'}{extra}")
    # Both tables are restricted to the rows this run actually drove, so
    # single-proto mode adjudicates only its own pins (item 24).
    unexpected, moved, gone = adjudicate_pins(
        divergent, pins_for(EXPECTED_DIVERGENCE, population))
    r_new, r_moved, r_gone = adjudicate_pins(
        refused, pins_for(EXPECTED_REFUSALS, population))
    print("enum: " + ", ".join(f"{k} {counts[k]}" for k in VERDICTS)
          + f"; {len(divergent) - len(unexpected)} pinned divergence(s)"
          + f"; {len(refused) - len(r_new)} pinned refusal(s)"
          + f"; budget={BUDGET}")
    if unexpected:
        print(f"UNEXPECTED divergence(s): {unexpected}")
    if moved:
        print(f"pinned evidence moved: {moved}")
    if gone:
        print(f"pinned divergence(s) converged or vanished: {gone}")
    # A refusal is the instrument declining to make a claim, so the refused
    # set is part of the exit contract, not commentary: a NEW refusal means a
    # proto stopped being driven, a MOVED one means it refuses for a different
    # reason, and a GONE one means a pin can no longer fail.
    if r_new:
        print(f"UNEXPECTED refusal(s) -- proto(s) no longer driven: {r_new}")
    if r_moved:
        print(f"pinned refusal(s) changed reason: {r_moved}")
    if r_gone:
        print(f"pinned refusal(s) no longer refused -- delete the pin: {r_gone}")
    return 1 if (unexpected or moved or gone
                 or r_new or r_moved or r_gone) else 0


if __name__ == "__main__":
    sys.exit(main())
