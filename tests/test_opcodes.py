import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
LISTING_DIR = ROOT / "corpus" / "golden" / "listing"

# luac listing 指令行：\t<pc>\t[<line>]\t<OPNAME 左对齐补空格>\t<operands>[\t; comment]
INSTR_LINE_RE = re.compile(r"^\t(\d+)\t\[[^\]]*\]\t(\w+) *\t([-0-9 ]+?)(?:\t;.*)?$")


def test_decode_known_words():
    from pyluadec.lift.opcodes import Op, decode
    # word = op | A<<6 | C<<14 | B<<23
    ri = decode(0x00000000, pc=1)                     # MOVE 0 0
    assert ri.op is Op.MOVE and ri.a == 0 and ri.b == 0
    ri = decode(1 | (2 << 6) | (5 << 14), pc=7)       # LOADK A=2 Bx=5
    assert ri.op is Op.LOADK and ri.a == 2 and ri.bx == 5 and ri.pc == 7
    ri = decode(22 | (0 << 6) | ((131071 - 3) << 14), pc=1)   # JMP sBx=-3
    assert ri.op is Op.JMP and ri.sbx == -3


def test_decode_rejects_bad_opcode():
    import pytest
    from pyluadec.lift.opcodes import DecodeError, decode
    with pytest.raises(DecodeError):
        decode(38, pc=1)          # opcode 38 不存在


def test_isk_indexk():
    from pyluadec.lift.opcodes import indexk, isk
    assert not isk(255) and isk(256) and isk(511)
    assert indexk(256) == 0 and indexk(300) == 44


def _check_against_listing(listing_text: str, protos_flat):
    """listing 的每条指令行 (opname, operand 列) 与我方 decode 结果逐条相等。"""
    from pyluadec.lift.opcodes import decode, luac_operand_str
    it = iter(protos_flat)
    cur = None; idx = 0; checked = 0
    for line in listing_text.splitlines():
        m = INSTR_LINE_RE.match(line)
        if not m:
            if line.startswith(("main <", "function <")):
                cur = next(it); idx = 0
            continue
        pc, opname, operands = int(m.group(1)), m.group(2), m.group(3).strip()
        assert pc == idx + 1
        ri = decode(cur.code[idx], pc=pc)
        assert ri.op.name == opname, f"pc {pc}: {ri.op.name} != {opname}"
        assert luac_operand_str(ri) == operands, f"pc {pc} {opname}: {luac_operand_str(ri)!r} != {operands!r}"
        idx += 1; checked += 1
    return checked


def test_decoder_matches_all_golden_listings(corpus_dir):
    from pyluadec.ingest import load_file
    total = 0
    for lst in sorted(LISTING_DIR.glob("*.txt")):
        name = lst.name[: -len(".txt")]
        root = load_file(corpus_dir / name)
        flat = []
        def walk(p):
            flat.append(p)
            for s in p.subprotos: walk(s)
        walk(root)
        total += _check_against_listing(lst.read_text(), flat)
    assert total > 200_000    # 语料约 21 万条指令，全部核对


def test_decoder_matches_fresh_listing_for_corpus_missing_ops(tmp_path):
    """SELF/POW/UNM/NOT/CLOSE 语料未用到，用现编译的源码补齐 oracle 覆盖。"""
    from pyluadec.ingest import load_file
    src = tmp_path / "t.lua"
    src.write_text(
        "local o = {}\n"
        "function o:m(x) return -x ^ 2, not x, #\"s\" end\n"   # SELF 在调用处
        "local function outer()\n"
        "  local cap = 1\n"
        "  do local inner = function() cap = cap + 1 end inner() end\n"  # CLOSE
        "  return o:m(cap)\n"
        "end\n"
        "return outer()\n")
    out = tmp_path / "t.out"
    subprocess.run([str(BUILD / "luac_sz4"), "-o", str(out), str(src)], check=True)
    listing = subprocess.run([str(BUILD / "luac_sz4"), "-l", "-l", str(out)],
                             capture_output=True, text=True, check=True).stdout
    for need in ("SELF", "POW", "UNM", "NOT"):
        assert need in listing        # 用例确实触发了这些 opcode
    root = load_file(out)
    flat = []
    def walk(p):
        flat.append(p)
        for s in p.subprotos: walk(s)
    walk(root)
    assert _check_against_listing(listing, flat) > 0
