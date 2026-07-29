"""C4(a) — `year_label` is for rendering and nothing else.

⭐ THE POINT OF A REDUNDANT FIELD IS THAT IT MUST STAY REDUNDANT. The ruling
allows `year_label` beside `year` on statement rows because Recharts reads its
axis key off each datum. That is a two-owners shape by construction, and the
thing that makes it safe is that exactly one of the two owners is ever computed
on. The moment something sorts, joins, compares or parses `year_label`, the raw
`year` stops being the single source of truth and the two can disagree.

Written while zero instances exist. Once one exists it is no longer a guard, it
is a migration.
"""
import ast
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND = os.path.join(ROOT, "axiom", "services") if os.path.isdir(
    os.path.join(ROOT, "axiom", "services")) else os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "services")


def _py_files():
    base = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "..", "..", "services"))
    for dp, dn, fn in os.walk(base):
        dn[:] = [d for d in dn if d != "__pycache__"]
        for f in fn:
            if f.endswith(".py"):
                yield os.path.join(dp, f)


COMPUTE_CONTEXTS = (ast.Compare, ast.BinOp, ast.BoolOp)


def test_year_label_is_never_computed_on():
    """It may be WRITTEN (assigned into a payload). It may not be read into a
    comparison, arithmetic, sort key, or dict lookup."""
    offenders = []
    for path in _py_files():
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except Exception:
            continue
        for node in ast.walk(tree):
            # a read of the STRING key in a computing context
            if isinstance(node, COMPUTE_CONTEXTS):
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Constant) and sub.value == "year_label":
                        offenders.append((path, node.lineno, "compared/combined"))
            if isinstance(node, ast.Call):
                fname = getattr(node.func, "attr", getattr(node.func, "id", ""))
                if fname in ("sorted", "sort", "max", "min", "int", "float"):
                    for sub in ast.walk(node):
                        if isinstance(sub, ast.Constant) and sub.value == "year_label":
                            offenders.append((path, node.lineno, f"passed to {fname}()"))
    assert not offenders, (
        "year_label is being computed on; raw `year` must stay the only field "
        f"anything derives from: {offenders}")


def test_year_label_is_actually_present_so_this_guard_is_not_vacuous():
    """⭐ A GUARD OVER A FIELD THAT DOES NOT EXIST PASSES TRIVIALLY. If the
    payload stopped carrying year_label, the test above would go green for the
    wrong reason — the ALWAYS-PASSING sibling of the taxonomy's entry 5."""
    found = 0
    for path in _py_files():
        try:
            src = open(path, encoding="utf-8").read()
        except Exception:
            continue
        found += src.count('"year_label"')
    assert found >= 3, f"year_label appears {found} times — the guard has nothing to guard"
