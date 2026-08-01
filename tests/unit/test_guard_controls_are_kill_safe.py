"""No guard may write to the filesystem to test itself.

⭐⭐ THE CLASS THIS CLOSES. Guards planted a line into PRODUCTION SOURCE to
exercise their own control, then removed it in a `finally`. ⭐ A `finally` DOES
NOT SURVIVE A KILL. Four times a timeout landed between the write and the
restore, stranding a live NameError in production source and reddening unrelated
gates: `sentinel.py` twice, `benchmarks/router.py` twice, most recently
`_planted = allocation_sqrt()`.

⭐⭐ FOUR OCCURRENCES IS A MECHANISM, NOT FOUR ACCIDENTS. The remedy is not
"be careful with cleanup" — it is to never create the thing that needs cleaning.

⭐⭐ KEYED ON BEHAVIOUR VIA AN AST READ, NOT ON THE TOKEN (§III.9). Four times
this era a guard banned a WORD and struck correct writing — `credential` hit
client-facing reassurance, `comment` hit the docstring explaining the ruling,
`respondent` hit explanatory copy, and `open(` hit `urllib.request.urlopen(`.
⭐ THAT LAST ONE IS THIS EXACT BAN. So this test matches CALL NODES whose callee
mutates the filesystem, and reads `open()`'s MODE — a read is not a write, and
`urlopen` is a different attribute name entirely.
"""
import ast
import glob
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(ROOT, "scripts")

# ⭐ Callees that MUTATE the filesystem. Reading is fine — every guard reads
# source; that is how a static check works.
MUTATORS = {
    "write_text", "write_bytes", "mkdir", "makedirs", "touch",
    "copy", "copyfile", "copy2", "copytree", "move",
    "remove", "unlink", "rmtree", "rmdir",
    "mkdtemp", "mkstemp", "mktemp", "NamedTemporaryFile", "TemporaryDirectory",
}
# ⭐ `os.replace` moves a file; `str.replace` returns a string. Only a call on
# one of these receivers is the filesystem one — this is the false positive my
# own first enumeration produced, and it is why the receiver is checked.
FS_MODULES = {"os", "shutil", "pathlib", "Path", "tempfile"}


def fs_writes(tree):
    """-> [(lineno, what)] for every call that MUTATES the filesystem."""
    out = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        if isinstance(f, ast.Attribute):
            name, recv = f.attr, f.value
            recv_name = (recv.id if isinstance(recv, ast.Name)
                         else recv.func.id if isinstance(recv, ast.Call)
                         and isinstance(recv.func, ast.Name) else None)
        elif isinstance(f, ast.Name):
            name, recv_name = f.id, None
        else:
            continue

        if name == "open":
            mode = None
            if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                mode = n.args[1].value
            for kw in n.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = kw.value.value
            # ⭐ open() with no mode is a READ. Only a writing mode counts.
            if isinstance(mode, str) and any(c in mode for c in "wax+"):
                out.append((n.lineno, f"open(mode={mode!r})"))
        elif name == "replace":
            # ⭐ os.replace / Path(...).replace move a file; str.replace does not.
            if recv_name in FS_MODULES:
                out.append((n.lineno, f"{recv_name}.replace()"))
        elif name in MUTATORS:
            out.append((n.lineno, f"{name}()"))
    return out


def _guards():
    g = sorted(glob.glob(os.path.join(SCRIPTS, "check-*.py")))
    assert g, "no guards found — a broken selector, not a clean corpus"
    return g


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE KNOWN POSITIVE — a scanner that has never fired has not been tested
# ═══════════════════════════════════════════════════════════════════════════

_BAD_BACKUP = """
import shutil, tempfile
def control():
    bak = tempfile.mktemp(suffix=".bak")
    shutil.copy2(src, bak)
    with open(src, "w") as fh:
        fh.write(planted)
    try:
        return check()
    finally:
        shutil.copy2(bak, src)
"""
_BAD_TEMPDIR = """
import tempfile, shutil
def control():
    d = tempfile.mkdtemp(prefix="x-")
    open(d + "/planted.py", "w").write("X = 1")
"""
_OK_READS = """
def scan(rel):
    with open(rel, encoding="utf-8") as fh:
        return ast.parse(fh.read())
"""
_OK_URLOPEN = """
import urllib.request
def probe(u):
    with urllib.request.urlopen(u, timeout=25) as r:
        return r.status
"""
_OK_STR_REPLACE = """
def norm(url):
    return url.replace("postgresql+psycopg://", "postgresql://")
"""
_OK_IN_MEMORY = """
OVERRIDES = {}
def control():
    OVERRIDES[rel] = source.replace(marker, marker + "\\n    _planted = f()")
    try:
        return check()
    finally:
        OVERRIDES.pop(rel, None)
"""


def test_THE_CONTROL_the_detector_fires_and_does_not_overfire():
    """⭐⭐ Cases 3-5 are the §III.9 false positives this must not repeat: a
    READ open(), urlopen(), and str.replace()."""
    assert fs_writes(ast.parse(_BAD_BACKUP)), \
        "the exact four-occurrence shape was NOT detected"
    assert fs_writes(ast.parse(_BAD_TEMPDIR)), \
        "a temp-dir plant was NOT detected"
    assert not fs_writes(ast.parse(_OK_READS)), \
        "a READ open() was flagged — reading source is how a static check works"
    assert not fs_writes(ast.parse(_OK_URLOPEN)), \
        "urlopen() was flagged — the fourth substring false positive, repeated"
    assert not fs_writes(ast.parse(_OK_STR_REPLACE)), \
        "str.replace() was flagged as a file move"
    assert not fs_writes(ast.parse(_OK_IN_MEMORY)), \
        "the REQUIRED in-memory pattern was flagged"


@pytest.mark.parametrize("path", _guards(), ids=os.path.basename)
def test_NO_GUARD_WRITES_TO_THE_FILESYSTEM(path):
    """⭐ A guard that edits anything to test itself is one interruption from
    committing that edit."""
    hits = fs_writes(ast.parse(open(path, encoding="utf-8").read()))
    assert not hits, (
        f"{os.path.basename(path)} mutates the filesystem at "
        f"{[(l, w) for l, w in hits]}.\n"
        "Build the modified source as a STRING and parse it — see "
        "pack_input_scan.OVERRIDES. A `finally` does not survive a kill."
    )


def test_the_corpus_is_not_empty():
    """⭐ '0 writers in 0 guards' and '0 in 25' print the same tick (III.4)."""
    assert len(_guards()) >= 25


def test_NO_PLANTED_LINE_IS_SITTING_IN_PRODUCTION_SOURCE():
    """⭐⭐ THE ORPHAN SWEEP, RUN ON EVERY SUITE. A leak that happened four times
    may have left a fifth nobody noticed — and the previous four were each found
    by a failing unrelated test, not by looking."""
    orphans = []
    for dp, _, fs in os.walk(os.path.join(ROOT, "services")):
        if "__pycache__" in dp:
            continue
        for fn in fs:
            if not fn.endswith(".py"):
                continue
            p = os.path.join(dp, fn)
            for i, ln in enumerate(open(p, encoding="utf-8"), 1):
                if "_planted" in ln:
                    orphans.append(f"{os.path.relpath(p, ROOT)}:{i}: {ln.strip()}")
    assert not orphans, "planted control lines stranded in production source:\n" + \
        "\n".join(orphans)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE CONVERSION MUST NOT HAVE DISABLED THE CONTROL
# ═══════════════════════════════════════════════════════════════════════════
# ⭐ A conversion that silently turns the control off is WORSE than the leak it
# fixes: the leak was loud (it reddened the build), an inert control is silent.
# So each converted guard is driven BOTH ways — red with the plant, green
# without — rather than merely being run once and seen to exit 0.

def _load(name):
    import importlib.util
    import sys
    if SCRIPTS not in sys.path:
        sys.path.insert(0, SCRIPTS)
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), os.path.join(SCRIPTS, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ⭐⭐ EXPORT- AND PACK-COVERAGE ARE PROVEN BY RUNNING THE GUARD, NOT HERE.
# Both walk call graphs to depth 6 across services/; driving each one twice from
# a test costs more than ten minutes. ⭐ THE PROOF IS NOT LOST — each guard runs
# its own control on EVERY invocation and exits non-zero if the plant is not
# detected, so the gate loop makes the assertion every time it runs. Duplicating
# it here would buy nothing and would make the suite the slowest thing in the
# repo, which is how a gate stops being run.
#
# Verified this lane, both before and after conversion:
#   check-export-coverage  "+ a surface added to the app is detected as uncarried"
#   check-pack-coverage    "+ a read added to an entry point is detected"


def test_assumption_registry_control_is_RED_on_the_plant():
    g = _load("check-assumption-registry")
    assert g.control() is True, "the planted constant was not found"
    # ⭐ GREEN WITHOUT IT — the same predicate over a registered value must not
    # flag, or the control proves only that the function returns True.
    have = next(iter(g.registered_values().values()))
    val = have[0] if isinstance(have, (list, tuple)) else have
    assert not g._unregistered_in("<c>", f"KNOWN = {val!r}\n"), \
        "a REGISTERED value was flagged — the control cannot distinguish"


def test_ratio_shapes_control_scans_SOURCES_without_touching_disk():
    """⭐ The shape key is DERIVED from the scanner, not written by hand. My
    first version guessed the literal "a+b" and failed — the scanner
    canonicalises, so a hand-written key tests the guess, not the scanner."""
    g = _load("check-ratio-shapes")
    src = "def f(a, b):\n    return a + b\n"
    shape = next(g.shape_of_expr(n) for n, _ in g.iter_expressions("<c>", _src=src))
    hits = g.scan({shape: "R1"}, roots=[], sources={"<c>": src})
    assert any(r == "R1" for r, _, _ in hits), \
        "an in-memory source was not scanned — the control is inert"
    other = next(g.shape_of_expr(n) for n, _ in
                 g.iter_expressions("<c>", _src="def f(a, b):\n    return a * b\n"))
    assert other != shape
    assert not g.scan({other: "R2"}, roots=[], sources={"<c>": src}), \
        "a non-matching shape was reported — the scanner cannot distinguish"
