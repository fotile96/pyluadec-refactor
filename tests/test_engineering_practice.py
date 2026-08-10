"""Architectural guards against text-post-processing creeping back into this project.

The predecessor project (pyluadec) sank under a 3712-line emitter that regex-rewrote
its own emitted Lua source in two layers, plus a fixed-point cleanup loop with a
hardcoded 3x3 iteration count -- it even had to re-parse the text it had just emitted
to find block boundaries (count do/then/end, count indentation). That is precisely the
failure mode this rewrite exists to avoid: the analysis and emission layers here operate
on structured data (typed IR, frozen dataclasses), never on text.

These checks are static (AST-parse only, never import/exec the scanned files) and cheap
by design -- they read source, they do not compile to bytecode or run anything.
"""
from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src" / "pyluadec"
TESTS_DIR = Path(__file__).resolve().parent

# structure/ is deliberately excluded: its one regex (an identifier-validation
# pattern in structure/fallback.py) predates this rule and is a legitimate,
# narrowly-scoped exception, not text post-processing of emitted source.
GUARDED_PACKAGES = ["ingest", "lift", "cfg", "sir", "express", "emit", "verify"]


def _iter_guarded_files() -> list[Path]:
    files: list[Path] = []
    for pkg in GUARDED_PACKAGES:
        pkg_dir = SRC / pkg
        if pkg_dir.is_dir():
            files.extend(sorted(pkg_dir.rglob("*.py")))
    return files


def _re_usages(path: Path) -> list[str]:
    """Return 'path:line: detail' strings for any `import re` or `re.*` in path."""
    tree = ast.parse(path.read_text(), filename=str(path))
    re_aliases = {"re"}
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "re":
                    bound = alias.asname or alias.name
                    re_aliases.add(bound)
                    hits.append(f"{path}:{node.lineno}: import re")
        elif isinstance(node, ast.ImportFrom) and node.module == "re":
            names = ", ".join(a.name for a in node.names)
            hits.append(f"{path}:{node.lineno}: from re import {names}")
    for node in ast.walk(tree):
        if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                and node.value.id in re_aliases):
            hits.append(f"{path}:{node.lineno}: {node.value.id}.{node.attr}")
    return hits


def test_no_regex_in_analysis_or_emission_layers():
    """No module under ingest/lift/cfg/sir/express/emit/verify imports `re` or calls `re.*`.

    Checked by parsing each file's AST (never importing/executing it), so a
    lazily-imported `re` hidden inside a function body is caught too, not just
    module-level imports.
    """
    offenders: list[str] = []
    for path in _iter_guarded_files():
        offenders.extend(_re_usages(path))
    assert not offenders, (
        "regex found in a structured analysis/emission package:\n"
        + "\n".join(offenders) + "\n\n"
        "This project's analysis and emission layers (ingest/lift/cfg/sir/express/"
        "emit/verify) operate on structured data -- typed IR and frozen dataclasses "
        "-- never text. Regex creeping in here is the specific failure mode that "
        "sank the predecessor project: a 3712-line emitter that regex-rewrote its "
        "own emitted output in two layers plus a fixed-point loop with a hardcoded "
        "3x3 iteration count, re-parsing the text it had just emitted to find block "
        "boundaries. If you need text post-processing here, stop and redesign as "
        "structured data instead. (structure/ is intentionally excluded: its "
        "identifier-validation regex predates this rule and is a narrow, legitimate "
        "exception.)"
    )


def _time_sleep_usages(path: Path) -> list[str]:
    """Return 'path:line' strings for any time.sleep(...) call in path (incl. aliased)."""
    tree = ast.parse(path.read_text(), filename=str(path))
    sleep_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "time":
            for alias in node.names:
                if alias.name == "sleep":
                    sleep_names.add(alias.asname or alias.name)
    hits: list[str] = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Attribute) and node.attr == "sleep"
                and isinstance(node.value, ast.Name) and node.value.id == "time"):
            hits.append(f"{path}:{node.lineno}")
        elif isinstance(node, ast.Name) and node.id in sleep_names:
            hits.append(f"{path}:{node.lineno}")
    return hits


def test_no_time_sleep_in_test_suite():
    """No *.py file under tests/ calls time.sleep (directly or via `from time import sleep`).

    time.sleep is a common source of a silently slow suite; a test that needs to
    wait for something should poll with a bound or use a fake clock instead.
    """
    offenders: list[str] = []
    for path in sorted(TESTS_DIR.rglob("*.py")):
        offenders.extend(_time_sleep_usages(path))
    assert not offenders, (
        "time.sleep found in the test suite (silently slows the whole run):\n"
        + "\n".join(offenders)
    )
