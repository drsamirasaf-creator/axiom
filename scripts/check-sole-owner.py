#!/usr/bin/env python3
"""Sole ownership of net debt, ROIC, WACC and EVA — enforced by SHAPE.

⭐ WRITTEN BEFORE THE CONSOLIDATION, AND ITS CORRECT INITIAL STATE IS RED.
A guard authored after the fix has never been observed to catch anything: it is
calibrated against a codebase that already passes, so it proves only that it can
print a tick. This one is expected to find FOUR net-debt sites on the day it is
written. If it finds three, the detector is wrong, not the codebase.

⭐ IT KEYS ON ARITHMETIC SHAPE, NOT ON IDENTIFIERS. Every one of the four sites
computes the same quantity and only two of them spell it the same way:

    financials:328    _n(lambda a, b: a - b, debt, cash)          <- inside a lambda,
                                                                     operands are the
                                                                     CALL ARGUMENTS
    intelligence:1569 BS["short_term_debt"][ys] + BS["long_term_debt"][ys]
                        - BS["cash"][ys]                          <- three-operand
    valuation:135     company["_debt_book"] - bs["cash"][ys]      <- TWO-operand
    valuation:542     bs["short_term_debt"][ys] + bs["long_term_debt"][ys]
                        - bs["cash"][ys]                          <- three-operand

A detector that only knows the three-operand form misses valuation:135 — the
site that matters most, because it is the one reading a caller-injected private
key. Grepping for "net_debt" misses it too: the variable is named net_debt at
every site, but so is a DIFFERENT quantity (see the collision exclusion below).

⭐ THE ALLOWLIST ASSERTS ITS OWN COVERAGE, IN BOTH DIRECTIONS.
  · a file that matches a shape and is NOT allowlisted -> fail (a new copy)
  · an allowlist entry that no longer matches          -> fail (stale drift)
One-directional coverage checks report clean on a surface they can no longer
see, which is the failure this whole family of guards exists to prevent.
"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ⭐ EXCLUDED BY PATH, AND THE REASON IS NOT OPTIONAL.
# valuation/engines.py's `deterministic["net_debt"]` is NOT the ratios net debt.
# It is a key on the DCF result dict that happens to share a name; on 30 Jul it
# produced five false positives in check-none-arithmetic until holder-awareness
# told the two apart. It must never be repointed at the ratio library: doing so
# would make the valuation bridge read a ratio computed for a different period
# basis. That would be the defect wearing the fix's clothes, and it is exactly
# the "cleanup" a future reader will reach for on seeing two things named alike.
# ⭐ AND IT IS A POSITIVE ASSERTION, NOT AN EXCLUSION, BECAUSE THE EXCLUSION WAS
# INERT. Written first as a path-based skip, it changed nothing: verified by
# deleting it and re-running — 4 sites either way. `deterministic["net_debt"]`
# is a dict KEY, not an arithmetic shape, so a shape detector never matched it
# and never needed to skip it. A guard clause that guards nothing is the
# declared-but-unbound class this codebase keeps finding, and shipping one
# inside a guard would have been the joke writing itself.
#
# So it asserts the opposite direction: the collision site MUST still be
# present, and MUST NOT be wired to the ratio library. That is a live check —
# it fires the day someone "tidies up" the two same-named things.
COLLISION_SITE = ("services/api/modules/valuation/engines.py",
                  '"net_debt": _r(net_debt)')
COLLISION_MUST_NOT_CONTAIN = ("ratios.net_debt", "ratios.NET_DEBT",
                              "library.net_debt")
COLLISION_EXCLUSIONS = set()   # kept empty: shape matching needs no path skips

# ⭐ THE ALLOWLIST ENCODES THE TARGET, NOT TODAY. One file, one site, per
# quantity. That is why this guard is RED the day it is written: net debt has
# four sites in three files and must have one. A guard whose expected values
# describe the current state is a description, not a guard — it goes green
# immediately and can never fail on the thing it was built for.
#
# LIBRARY is where the sole owner will live. It does not exist yet, so the
# stale-entry check fires too — correctly. Both directions stay honest.
LIBRARY = "services/api/modules/financials/ratios.py"
ALLOWLIST = {"net_debt": [LIBRARY], "roic": [LIBRARY],
             "eva": [LIBRARY], "wacc": [LIBRARY]}
EXPECTED = {"net_debt": 1, "roic": 1, "eva": 1, "wacc": 1}

SCAN_DIRS = ["services/api"]
SKIP = {"__pycache__"}


# ── operand recognisers: what does this expression MEAN, not what is it called ─
def _key_of(node):
    """The last constant string subscript, or the bare name: bs["cash"][ys] -> cash."""
    while isinstance(node, ast.Subscript):
        k = node.slice
        if isinstance(k, ast.Constant) and isinstance(k.value, str):
            return k.value
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _is_cash(n):
    k = _key_of(n)
    return bool(k) and k == "cash"


def _is_debt_component(n):
    k = _key_of(n)
    return k in ("short_term_debt", "long_term_debt")


def _is_debt_aggregate(n):
    """A single operand that already stands for total debt."""
    k = _key_of(n)
    return bool(k) and ("debt" in k) and k not in ("net_debt",) \
        and not _is_debt_component(n)


def _net_debt_shape(node):
    """<debt> - <cash>, in either the three-operand or two-operand form."""
    if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub)):
        return False
    if not _is_cash(node.right):
        return False
    left = node.left
    # three-operand: (short_term_debt + long_term_debt) - cash
    if isinstance(left, ast.BinOp) and isinstance(left.op, ast.Add):
        if _is_debt_component(left.left) and _is_debt_component(left.right):
            return True
    # two-operand: <debt aggregate> - cash   (valuation:135)
    return _is_debt_aggregate(left)


def _n_call_shape(node):
    """⭐ _n(lambda a, b: a - b, debt, cash) — the operands are the CALL ARGS.

    financials:328 writes it this way, so the BinOp inside the lambda carries
    only placeholder names. The meaning lives one level out, in what is passed."""
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == "_n" and len(node.args) == 3):
        return False
    fn = node.args[0]
    if not isinstance(fn, ast.Lambda):
        return False
    body = fn.body
    if not (isinstance(body, ast.BinOp) and isinstance(body.op, ast.Sub)):
        return False
    a, b = node.args[1], node.args[2]
    return (_is_debt_aggregate(a) or _is_debt_component(a)) and _is_cash(b)


def _roic_shape(node):
    """<nopat> / <invested capital>."""
    if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)):
        return False
    return _key_of(node.left) == "nopat" and _key_of(node.right) in ("ic", "invested_capital")


def _roic_n_shape(node):
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == "_n" and len(node.args) == 3):
        return False
    fn = node.args[0]
    if not (isinstance(fn, ast.Lambda) and isinstance(fn.body, ast.BinOp)
            and isinstance(fn.body.op, ast.Div)):
        return False
    return (_key_of(node.args[1]) == "nopat"
            and _key_of(node.args[2]) in ("ic", "invested_capital"))


def _eva_shape(node):
    """<nopat> - <wacc> * <invested capital>, direct or through _n."""
    def _sub_mult(b):
        if not (isinstance(b, ast.BinOp) and isinstance(b.op, ast.Sub)):
            return False
        r = b.right
        return (isinstance(r, ast.BinOp) and isinstance(r.op, ast.Mult)
                and _key_of(b.left) in ("nopat", "n_")
                and _key_of(r.left) in ("wacc", "w") or False)
    if _sub_mult(node):
        return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
            and node.func.id == "_n" and node.args:
        fn = node.args[0]
        if isinstance(fn, ast.Lambda) and _sub_mult(fn.body):
            return True
    return False


def _wacc_shape(node):
    """The cost-of-capital blend: ke * we + kd * (1 - T) * wd, in any spelling."""
    if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)):
        return False
    txt = ast.unparse(node)
    return ("ke" in txt and "kd" in txt and "*" in txt and
            ("1 - " in txt or "1.0 - " in txt))


SHAPES = {"net_debt": (_net_debt_shape, _n_call_shape),
          "roic": (_roic_shape, _roic_n_shape),
          "eva": (_eva_shape,),
          "wacc": (_wacc_shape,)}


class Finder(ast.NodeVisitor):
    def __init__(self, rel, src):
        self.rel, self.src = rel, src
        self.hits = {k: [] for k in SHAPES}

    def generic_visit(self, node):
        for kind, fns in SHAPES.items():
            if any(f(node) for f in fns):
                txt = ast.unparse(node)[:70]
                if not any(self.rel == p and frag in self.src
                           and frag in txt for p, frag in COLLISION_EXCLUSIONS):
                    self.hits[kind].append((node.lineno, txt))
                # ⭐ DO NOT DESCEND INTO A MATCHED NODE. `_n(lambda n_, i_:
                # n_ - w["wacc"] * i_, ...)` matches, and so does the BinOp in
                # its own lambda body — one expression counted twice. A guard
                # whose count is inflated by its own recursion cannot be
                # compared against an expected count, which is the whole
                # mechanism here.
                return
        super().generic_visit(node)


def main():
    found = {k: [] for k in SHAPES}
    for d in SCAN_DIRS:
        for base, dirs, files in os.walk(os.path.join(ROOT, d)):
            dirs[:] = [x for x in dirs if x not in SKIP]
            for f in sorted(files):
                if not f.endswith(".py"):
                    continue
                path = os.path.join(base, f)
                rel = os.path.relpath(path, ROOT)
                try:
                    src = open(path, encoding="utf-8").read()
                    tree = ast.parse(src)
                except Exception:
                    continue
                fi = Finder(rel, src)
                fi.visit(tree)
                for k, hits in fi.hits.items():
                    for ln, txt in hits:
                        found[k].append((rel, ln, txt))

    rc = 0

    # ── the name collision, asserted rather than skipped ────────────────────
    cpath, cfrag = COLLISION_SITE
    csrc = ""
    try:
        csrc = open(os.path.join(ROOT, cpath), encoding="utf-8").read()
    except OSError:
        pass
    if cfrag not in csrc:
        print(f"  ✗ COLLISION SITE GONE: {cpath} no longer contains {cfrag!r}.\n"
              f"    deterministic[\"net_debt\"] is the DCF bridge's own figure, not\n"
              f"    the ratios net debt. If it was repointed at the library, the\n"
              f"    bridge now reads a ratio computed on a different period basis —\n"
              f"    the defect wearing the fix's clothes. If it was renamed on\n"
              f"    purpose, update COLLISION_SITE deliberately.\n")
        rc = 1
    else:
        bad = [m for m in COLLISION_MUST_NOT_CONTAIN if m in csrc]
        if bad:
            print(f"  ✗ COLLISION SITE REPOINTED AT THE LIBRARY: {bad}\n")
            rc = 1
        else:
            print(f"  ✓ name collision intact and unwired: "
                  f"{cpath} keeps its own net_debt\n")

    for kind in ("net_debt", "roic", "eva", "wacc"):
        hits = found[kind]
        files = sorted({r for r, _l, _t in hits})
        allowed = ALLOWLIST[kind]
        print(f"  {kind.upper():<9} {len(hits)} site(s) in {len(files)} file(s) "
              f"· expected {EXPECTED[kind]}")
        for r, ln, t in hits:
            print(f"      {r}:{ln}  {t}")

        # direction 1: a shape in a file nobody allowlisted
        strays = [f for f in files if f not in allowed]
        if strays:
            print(f"      ✗ NOT ALLOWLISTED: {strays}")
            rc = 1
        # direction 2: an allowlist entry that no longer matches
        stale = [f for f in allowed if f not in files]
        if stale:
            print(f"      ✗ STALE ALLOWLIST ENTRY (no longer matches): {stale}")
            rc = 1
        if len(hits) != EXPECTED[kind]:
            print(f"      ✗ COUNT {len(hits)} != expected {EXPECTED[kind]}")
            rc = 1
        print()

    print("  ✓ sole ownership holds." if rc == 0 else
          "  ✗ sole ownership VIOLATED — see above.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
