"""Propose-and-certify channel: the proposal registry and its inliner
(M8 wiring, partner-approved 2026-08-18; see
``docs/reports/m8-strategy-survey-fable5.md`` §4.4/§9 and the handoff
``docs/reports/m8-handoff-proposal-channel.md``).

A *proposal* is a hand-written source file for one proto that refused
reconstruction, stored in wrapper form -- exactly what ``certify_proto``
compiles for a non-root proto::

    local u0, u1, ...            # when the proto has upvalues
    return function(<params>)
    <body>
    end

Proposals are DATA, not code: this module never certifies anything, it
only prepares text for the printer to inline at a CLOSURE site. The
certification is the caller's whole-tree round (``structured.py``'s
proposal tier): the chunk is reprinted with proposal bodies at the
covered sites, compiled by the real oracle, and compared by the
UNTOUCHED ladder with zero excluded paths -- so any splicing or renaming
error here is caught by the gate, never shipped (property P1).

**Upvalue renaming (the no-``re`` constraint).** The wrapper's body
references its upvalues as ``u0..u<n>``; inlined at a site inside the
parent they must read the ENCLOSING scope's own identifiers for those
captures -- the same ``names`` list ``emit.lua.Printer.closure_parts``
derives from the CLOSURE pseudo-instructions. The renamer is a
hand-written boundary-aware scanner (identifier-boundary checks and
string/comment state tracking), NOT a regex: the engineering-practice
gate statically forbids ``re`` in this package. Proposal files are read
``bytes``-only (property P5); diagnostic text never carries their
content.

Renaming soundness argument (H2 in the handoff): the proposals' bodies
descend from printer output whose ``code`` field compared equal to the
original's, so ``u<i>`` first-use order is monotonic in the original
GETUPVAL index order; renaming in ascending index order is therefore
exact. The whole-tree compare re-proves it on every regeneration.

**Enumeration is pinned (property P4).** ``MANIFEST`` is the complete,
explicit list of proposals the pipeline will ever consult -- adding or
removing one is a deliberate edit here, held by
``tests/test_proposal_channel.py``'s enumeration pin. A proto that the
reconstructor certified ``L3`` never consults a proposal: the protection
lives in the CALLER's refusers filter (``structured._proposal_round``
narrows the dict to refusing sites before the printer ever sees it --
controller review IMP-1, 2026-08-18; an earlier revision claimed the
protection came from the arm's position in ``closure_parts``, which was
wrong twice over: the arm returns early, so without the filter a
proposal would ALWAYS displace the reconstructor's text, certified or
not).
"""
from __future__ import annotations

import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_ROOT = _REPO_ROOT / "corpus" / "proposals"

#: The pinned enumeration (property P4): (corpus file, proto path).
#: The controller's demonstration campaign certified 8 leaves (survey
#: §9); the channel wiring added the 9th (`main_25`, its own K1 fold --
#: controller review §1.2 confirmed the diagnosis the wiring measured).
#: Each entry is certified through the unmodified ladder by
#: ``corpus/proposals/verify_proposals.py`` (9/9 at the wiring tree).
MANIFEST: tuple[tuple[str, str], ...] = (
    ("snr_common.lua", "main_24"),
    ("snr_common.lua", "main_25"),
    ("snr_common.lua", "main_25_4"),
    ("snr_common.lua", "main_71"),
    ("snr_common.lua", "main_74_18"),
    ("snr_common.lua", "main_76_2"),
    ("snr_graphic.lua", "main_4"),
    ("snr_mainmenu.lua", "main_7"),
    ("snr_story_main.lua", "main_3"),
)


def proposals_root() -> Path:
    """Where proposal files live. ``PYLUADEC_PROPOSALS_DIR`` overrides the
    repo-relative default (used by the enumeration/neuter tests to prove
    the loader actually reads this directory)."""
    env = os.environ.get("PYLUADEC_PROPOSALS_DIR")
    return Path(env) if env else _DEFAULT_ROOT


def for_file(corpus_name: str) -> dict[str, bytes]:
    """``proto_path -> raw proposal bytes`` for one corpus file. Empty dict
    for files with no proposals (the 221 uncovered files pay one dict
    allocation). Missing FILES (manifest names a file whose proposal is
    absent) raise -- the manifest is pinned, so an absent file is a
    broken tree, not a silent skip."""
    out: dict[str, bytes] = {}
    for fname, proto_path in MANIFEST:
        if fname != corpus_name:
            continue
        path = proposals_root() / fname.removesuffix(".lua") / f"{proto_path}.lua"
        if not path.is_file():
            raise FileNotFoundError(
                f"proposal manifest names {fname}:{proto_path} but "
                f"{path} does not exist")
        out[proto_path] = path.read_bytes()
    return out


def parse_wrapper(raw: bytes, proto_path: str) -> tuple[str, bytes]:
    """``(params, body)`` from a proposal's wrapper form.

    Parses the skeleton only -- the ``local u...`` declaration lines are
    skipped, the ``return function(...)`` line supplies the param list
    verbatim (param names are the body's own; they do not affect the
    recompiled bytecode), and the body runs to the final ``end`` line.
    Raises ``ValueError`` when the skeleton does not hold; the caller
    treats that as "no proposal" (the chunk then falls to the tiers it
    would have shipped anyway -- a refusal, never wrong text).
    """
    lines = raw.split(b"\n")
    i = 0
    # Skip blank lines and the `local u0, ...` declarations.
    while i < len(lines) and (
            not lines[i].strip() or lines[i].lstrip().startswith(b"local ")):
        i += 1
    if i >= len(lines) or not lines[i].startswith(b"return function("):
        raise ValueError(f"{proto_path}: wrapper has no `return function(` line")
    header = lines[i]
    close = header.rfind(b")")
    if close < 0:
        raise ValueError(f"{proto_path}: unterminated wrapper header")
    params = header[header.index(b"(") + 1:close].decode("ascii").strip()
    body_lines = lines[i + 1:]
    # Strip the trailing `end` (the wrapper's closer). It is the last
    # non-blank line; anything else means the skeleton changed shape.
    while body_lines and not body_lines[-1].strip():
        body_lines.pop()
    if not body_lines or body_lines[-1].strip() != b"end":
        raise ValueError(f"{proto_path}: wrapper does not end in `end`")
    body_lines.pop()
    return params, b"\n".join(body_lines) + b"\n" if body_lines else b""


_IDENT_CHARS = frozenset(
    b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")


def rename_upvalues(body: bytes, names: list[str],
                    shift: int = 0) -> bytes:
    """Replace every standalone ``u<digits>`` identifier with
    ``names[<digits>]`` and shift every ``l<k>_<digits>`` identifier's
    ``k`` up by ``shift``, leaving string literals and comments untouched.

    The ``u`` rename rebinds the wrapper's upvalue references to the
    enclosing scope's own identifiers. The ``l`` shift solves the
    SHADOW-CAPTURE collision: the wrapper spells its locals at depth 1
    (``l1_0``); spliced at a site whose enclosing scopes already hold
    ``l1_*..l<shift>_*`` locals, an unshifted body local of the same
    spelling would shadow the very name a renamed upvalue points at,
    silently turning a capture into a self-reference (the measured
    ``nups`` mismatch of the first wiring round -- `main_25_4`,
    `main_74_18`, `main_76_2`, all depth-2 sites with ``MOVE 0``
    captures). Shifting by the parent depth makes the body's names start
    at ``l<shift+1>_*``, disjoint from every enclosing local, which is
    the same naming the reconstructor arm would have used
    (``name_for(reg, depth + 1)``).

    A hand-written scanner (no ``re`` -- the package ban): it walks the
    bytes tracking quote state (single/double, backslash escapes), line
    comments, and long-bracket strings/comments (``[[ .. ]]`` and
    ``--[==[ .. ]==]``), and rewrites only in the normal state. An
    identifier qualifies iff it is ``u``/``U`` or ``l``/``L`` followed by
    the pattern above, bounded on both sides by non-identifier bytes. A
    ``u`` index beyond ``names`` is left as-is -- the whole-tree compare
    then refuses the chunk (an extra ``u7`` the wrapper never declared is
    a broken proposal, and the gate is the backstop, not this scanner).
    """
    out = bytearray()
    i, n = 0, len(body)

    def long_bracket_level(at: int) -> int:
        """If ``body[at:]`` opens a long bracket (``[`` or ``[=*[``),
        return its level, else -1. ``at`` must point at ``[``."""
        if at >= n or body[at] != 0x5B:
            return -1
        j = at + 1
        while j < n and body[j] == 0x3D:
            j += 1
        return j if j < n and body[j] == 0x5B else -1

    while i < n:
        b = body[i]
        # Line comment: `--` to end of line (long-bracket comments are
        # handled by the long-bracket arm below, which `--[` enters).
        if b == 0x2D and i + 1 < n and body[i + 1] == 0x2D:
            lvl = long_bracket_level(i + 2)
            if lvl < 0:
                j = body.find(b"\n", i)
                j = n if j < 0 else j
                out += body[i:j]
                i = j
                continue
        if b in (0x22, 0x27):                      # quoted string
            quote = b
            j = i + 1
            while j < n:
                if body[j] == 0x5C:                # backslash escape
                    j += 2
                    continue
                if body[j] == quote or body[j] == 0x0A:
                    break
                j += 1
            j = min(j + 1, n)
            out += body[i:j]
            i = j
            continue
        lvl = long_bracket_level(i)
        if lvl >= 0:                               # long string/comment
            closer = b"]" + b"=" * (lvl - i - 2) + b"]"
            j = body.find(closer, lvl + 1)
            j = n if j < 0 else j + len(closer)
            out += body[i:j]
            i = j
            continue
        if b in (0x75, 0x55):                      # 'u' / 'U'
            prev_ok = i == 0 or body[i - 1] not in _IDENT_CHARS
            j = i + 1
            while j < n and 0x30 <= body[j] <= 0x39:
                j += 1
            ident_ok = j > i + 1 and (j == n or body[j] not in _IDENT_CHARS)
            if prev_ok and ident_ok:
                idx = int(body[i + 1:j])
                if idx < len(names):
                    out += names[idx].encode("ascii")
                    i = j
                    continue
        elif b in (0x6C, 0x4C) and shift:           # 'l' / 'L' with a shift
            prev_ok = i == 0 or body[i - 1] not in _IDENT_CHARS
            j = i + 1
            while j < n and 0x30 <= body[j] <= 0x39:
                j += 1
            # l<digits>_<digits> -- the wrapper's local spelling; the
            # underscore must be there (a bare `l1` is not one of ours).
            if prev_ok and j > i + 1 and j < n and body[j] == 0x5F:
                k = i + 1
                while k < j and 0x30 <= body[k] <= 0x39:
                    k += 1
                depth = int(body[i + 1:j])
                out += b"l" + str(depth + shift).encode("ascii") + body[j:j + 1]
                i = j + 1
                continue
        out.append(b)
        i += 1
    return bytes(out)


def inline_parts(raw: bytes, names: list[str],
                 proto_path: str, shift: int = 0) -> tuple[str, str]:
    """``(params, body)`` ready for a CLOSURE site: the wrapper parsed,
    its upvalue references rebound to ``names`` (the enclosing scope's
    own identifiers, in upvalue-index order).

    The body is decoded UTF-8 HERE and only here -- the scanner and the
    rename run on bytes, and the decode is the printer's own convention
    (its whole output is ``str`` re-encoded at the end; a proposal is
    source text in the same class as ``corpus/final/`` itself, not a
    bytecode-derived diagnostic)."""
    params, body = parse_wrapper(raw, proto_path)
    return (rename_upvalues(params.encode("ascii"), [], shift).decode("ascii"),
            rename_upvalues(body, names, shift).decode("utf-8"))
