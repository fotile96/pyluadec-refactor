def _proto(src: str):
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    return load_bytes(oracle.compile_source(src.encode(), strip=True))


def test_identical_source_certifies_l3_at_rung1():
    from pyluadec.verify.certify import certify_l3
    src = b"local a = 1 local b = 2 return a + b"
    r = certify_l3(_proto(src.decode()), src)
    # BRIEF DEFECT (documented in task-0-report.md): oracle.compile_source embeds a
    # stable filename ("@in.lua") regardless of tempdir, so compiling byte-identical
    # source text twice with the same strip flag yields byte-identical protos --
    # source/lineinfo/locvars/linedefined all already match at rung 0 (a *stronger*
    # result than rung 1, not a failure of the gate). Verified empirically before
    # changing the expected rung.
    assert r.level == "L3" and r.rung == 0 and r.mismatches == ()


def test_line_only_difference_still_certifies_l3():
    from pyluadec.verify.certify import certify_l3
    # BRIEF DEFECT (documented in task-0-report.md): a top-level-only "print(1)"
    # example does not exercise rung 1 under strip=True compilation. A main chunk's
    # linedefined/lastlinedefined are always 0/0 regardless of leading blank lines,
    # and strip=True already collapses source/lineinfo/locvars identically on both
    # sides -- so orig and recompiled are already byte-identical at rung 0 (verified
    # empirically). A nested function is needed so linedefined/lastlinedefined
    # (which strip=True does NOT erase -- see CLAUDE.md's "但 linedefined/
    # lastlinedefined 幸存") genuinely shifts with the leading blank lines, giving a
    # real rung-0 mismatch that only rung 1's _strip_lineinfo normalization resolves.
    orig = _proto("local function f() return 1 end f()")
    r = certify_l3(orig, b"\n\n\nlocal function f() return 1 end f()")
    assert r.level == "L3" and r.rung == 1


def test_semantic_difference_is_l1():
    from pyluadec.verify.certify import certify_l3
    r = certify_l3(_proto("return 1"), b"return 2")
    assert r.level == "L1" and r.rung is None and r.mismatches != ()


def test_uncompilable_structured_source_is_l1():
    from pyluadec.verify.certify import certify_l3
    r = certify_l3(_proto("return 1"), b"this is not ) valid lua (")
    assert r.level == "L1" and r.rung is None


def test_reconstructed_shape_certifies_l3():
    # the M3 hypothesis: register-as-local reconstruction round-trips
    from pyluadec.verify.certify import certify_l3
    orig = _proto("local a = 1 a = a + 1 print(a)")
    recon = b"local l0_0 = 1\nl0_0 = l0_0 + 1\nprint(l0_0)\n"
    r = certify_l3(orig, recon)
    assert r.level == "L3", r.mismatches
