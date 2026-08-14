"""The memo is process-level, keyed on content, and invisible in results."""
import subprocess
import uuid

from pyluadec import oracle


class _CountingSubprocess:
    """A pass-through view of the `subprocess` module that counts `run`.

    Deliberately NOT a fake: `run` delegates to the real one, so every value
    the memo stores under this monkeypatch is genuine `luac_sz4` output. That
    matters here -- `oracle.py`'s `_COMPILE_MEMO` comment warns that a test
    which *fakes* `subprocess.run` while keeping the real key inputs would
    write a synthetic result into a process-wide cache under an ordinary key.
    Counting a real call cannot do that. Scoped to `pyluadec.oracle`'s own
    namespace rather than to the `subprocess` module, so nothing else in the
    process sees it.
    """

    def __init__(self, real):
        self._real = real
        self.n = 0

    def __getattr__(self, name):
        return getattr(self._real, name)

    def run(self, *a, **kw):
        self.n += 1
        return self._real.run(*a, **kw)


def test_recompiling_identical_bytes_hits_the_memo(monkeypatch):
    """Asserts the memo's EFFECT -- `luac` subprocesses NOT spawned -- rather
    than a wall clock.

    This was `dt < 0.05` for 50 compiles, which had ~2x margin against the
    real unmemoized cost on the review host (0.09-0.11s for 50 spawns): it
    fires under a neuter today and retires itself silently on a faster
    machine. A spawn count has no margin to erode.

    The source is unique per run, so the cold compile is a guaranteed MISS and
    the `== 1` below is a real measurement rather than a coincidence of test
    ordering. Proven to fail under a real neuter (2026-08-14): commenting out
    `_COMPILE_MEMO[key] = result` in `src/pyluadec/oracle.py` and running this
    test alone gives `AssertionError: 51 luac spawn(s) for 1 cold compile +
    50 repeats -- not memoized`.
    """
    counting = _CountingSubprocess(subprocess)
    monkeypatch.setattr(oracle, "subprocess", counting)
    src = f"local x = 1 -- {uuid.uuid4()}\nreturn x\n".encode()
    a = oracle.compile_source(src)
    assert counting.n == 1, f"a cold compile spawned {counting.n} luac(s)"
    for _ in range(50):
        b = oracle.compile_source(src)
    assert b == a
    assert counting.n == 1, (
        f"{counting.n} luac spawn(s) for 1 cold compile + 50 repeats -- "
        "not memoized")


def test_strip_variants_do_not_collide():
    src = b"local y = 2\nreturn y\n"
    assert oracle.compile_source(src) != oracle.compile_source(src, strip=True)
