"""Calibration for the ported quality metric (`verify.semantic_score`).

The metric is an *evaluation* instrument, never a gate: it can only ever
report a number, and nothing in the tree lets it pass something
certification refuses. What these tests buy is the right to believe the
number. Two properties, and they pull in opposite directions:

1. **No false alarms.** A proto scored against itself must come out at 1.0
   on every one of the nine components -- otherwise the corpus average is
   depressed by the instrument rather than by the decompiler, and every
   later re-measurement is comparing against a floor nobody can find.
2. **Not blind.** The M2 fallback of a chunk that certifies `L3` must score
   strictly below 1.0. The fallback is semantically exact but structurally a
   `__pld_pc` dispatch state machine, so it is the sharpest available
   example of "recompiles to something certification would reject". If the
   metric could not see it, the corpus average would be measuring almost
   nothing -- 17 of 229 files ship exactly this -- and that would be a
   finding about the metric, not a licence to tune it until it fires.

The third test is the committed corpus smoke test; the full 229-file sweep
is a CLI run (`scripts/quality_score.py`), not part of this suite.
"""
import pytest


# One sample for both calibration tests, so the second one's verdict cannot
# be blamed on a different subject. Constrained from two sides: it must
# certify `L3` today (test 2's precondition asserts it, so the constraint is
# checked, not assumed), and it must make every counter in the signature
# non-empty somewhere in the tree (test 1 checks that too -- "all components
# 1.0" is free for a pair of empty Counters, so a sample that exercised
# nothing would pass test 1 vacuously). Between them that means: a global
# write (`Total =`), global reads (`print`, `string`), a table field read
# (`string.format`), calls in both arities, a subproto, a numeric `for` (the
# only back edge), an early `return` with two values, and constants of every
# kind including a multi-byte one (D2's char-vs-byte length divergence).
#
# EXPIRY: if a future change makes this stop certifying, do not delete the
# precondition -- find another chunk that certifies and still lights up
# every counter. Losing either half silently turns a calibration into
# decoration.
_RICH = b"""
local function f(a, b)
  local acc = 0
  for i = 1, a do acc = acc + i * b end
  if acc > 10 then return acc, "big" end
  return acc
end
Total = f(3, 4)
print(Total, string.format("%d", 3), 2.5, -7, "\xe3\x81\x82\xe3\x81\x84")
"""


def _load(src: bytes):
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    return load_bytes(oracle.compile_source(src, strip=True))


def test_identical_protos_score_one_on_every_component():
    from pyluadec.verify.semantic_score import score_protos
    p = _load(_RICH)
    fs = score_protos(p, p)
    assert fs.hard_issues == ()
    assert fs.status == "pass"
    for ps in fs.proto_scores:
        for name, value in ps.components.items():
            assert value == 1.0, f"component {name} at path {ps.path} = {value}"
        assert ps.score == pytest.approx(1.0)
    assert fs.score == pytest.approx(1.0)
    # The sample must actually exercise the counters, or "all 1.0" is
    # vacuous: an all-zero Counter pair scores 1.0 by definition.
    from pyluadec.verify.semantic_score import collect_proto_signatures
    sigs = collect_proto_signatures(p)
    for field in ("global_reads", "global_writes", "call_targets",
                  "call_shapes", "return_arity", "constant_fingerprint",
                  "opcode_family_counts"):
        assert any(getattr(s, field) for s in sigs.values()), field
    assert any(s.cfg_reachable[2] > 0 for s in sigs.values()), "no back edge"


def test_m2_fallback_of_an_l3_chunk_scores_below_one():
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.structure.fallback import emit_chunk
    from pyluadec.structure.structured import emit_certified_chunk
    from pyluadec.verify.semantic_score import score_protos

    original = _load(_RICH)
    # Precondition: this chunk is one certification ACCEPTS, so any drift the
    # metric reports below is the fallback's structure and not the sample's.
    assert emit_certified_chunk(original).certs["main"].level == "L3"

    fallback_src = emit_chunk(original)
    candidate = load_bytes(oracle.compile_source(fallback_src))
    fs = score_protos(original, candidate)
    # Measured 2026-08-12: 0.276364. Asserted as a band, not a constant --
    # the point is that the metric SEES the fallback, not that it scores it
    # to six decimals, and pinning the exact value would make every future
    # fallback-emitter change look like a metric regression. The upper bound
    # is the real assertion; the lower one only says the score stayed a
    # number in range.
    #
    # 0.5 is chosen from both sides, measured, not picked round: the true
    # score is 0.276364 (0.22 of headroom below), and blinding the metric by
    # making `_counter_similarity` return a constant 1.0 -- the neuter proof
    # for this test -- lifts it only to 0.904545, because the two CFG
    # components are not counters and keep firing. A bound of 0.9 would have
    # left that proof passing by 0.0045.
    assert 0.0 < fs.score < 0.5, fs.score
    # ... and it must not merely be the wrapper: the two protos that exist on
    # both sides must themselves score below 1.0, so a future fallback that
    # kept the proto tree shape could not sneak past this.
    shared = {ps.path: ps for ps in fs.proto_scores if ps.components}
    assert () in shared and shared[()].score < 1.0
    assert any(c < 1.0 for c in shared[()].components.values())


def test_corpus_smoke_three_small_files(corpus_dir, decompiled):
    """Committed corpus arm: 3 smallest files, end to end.

    Deliberately tiny -- the whole-corpus sweep is `scripts/quality_score.py`,
    a CLI run, because 229 decompiles plus 229 `luac` subprocesses do not
    belong in a suite with a 45s ceiling. This only pins that the CLI's path
    (decompile -> compile -> score) works on real corpus bytecode and that
    real files score in a sane range, so the sweep cannot silently start
    returning 0.0 or crashing.
    """
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes, load_file
    from pyluadec.verify.semantic_score import score_protos

    files = sorted(corpus_dir.glob("*.lua"), key=lambda p: p.stat().st_size)[:3]
    assert len(files) == 3
    for f in files:
        res = decompiled(f)
        cand = load_bytes(oracle.compile_source(res.source))
        fs = score_protos(load_file(f), cand, file_size=f.stat().st_size)
        assert 0.0 <= fs.score <= 1.0
        assert fs.score > 0.5, f"{f.name}: {fs.score}"
