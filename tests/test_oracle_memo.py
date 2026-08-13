"""The memo is process-level, keyed on content, and invisible in results."""
import time

from pyluadec import oracle


def test_recompiling_identical_bytes_hits_the_memo():
    src = b"local x = 1\nreturn x\n"
    a = oracle.compile_source(src)
    t0 = time.perf_counter()
    for _ in range(50):
        b = oracle.compile_source(src)
    dt = time.perf_counter() - t0
    assert b == a
    assert dt < 0.05, f"50 memo hits took {dt:.3f}s -- not memoized"


def test_strip_variants_do_not_collide():
    src = b"local y = 2\nreturn y\n"
    assert oracle.compile_source(src) != oracle.compile_source(src, strip=True)
