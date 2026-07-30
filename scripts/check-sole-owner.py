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
# ⭐ THE BRIEF EXPECTED 3. THE FIRST MEASUREMENT SAID 14. THE CALIBRATED COUNT
# IS 15 — and the difference is the INSTRUMENT, not the codebase.
#
# `_key_of` could not see through `.get(ys)`, so
# `_n(lambda a, b: a + b, BS["short_term_debt"].get(ys), BS["long_term_debt"].get(ys))`
# at financials:309 was invisible. The defect was found while calibrating the
# INVESTED-CAPITAL counter against a known population, and fixing it there
# raised this count too. A ratchet set from an uncalibrated counter is a number
# about the counter.
#
# ⭐ RAISING A RATCHET IS NORMALLY FORBIDDEN. It is permitted here, once, and
# only because nothing in the codebase changed — the detector started seeing a
# site that was always there. Lowering it to 14 to keep the guard quiet would
# have hidden a real site; leaving it at 14 would have failed forever on a
# number that was never right. Both are worse than saying so.
#
# THERE ARE 15, ACROSS 5 FILES — 10 IN ONE.
#     intelligence/engines.py   10
#     financials/engines.py      3   (:309 and :609 are both _n forms)
#     sentinel.py                1   (:145, inside the _debt_book function)
#     prescience_decision.py     1   (:240, the base term under the debt_scale shock)
#     valuation/engines.py       1   (:126)
# Recorded as a RATCHET at the measured truth, not at the expected 3: a guard
# pinned to a number the codebase never had is permanently red for a reason
# nobody can action, and gets muted. The number may only go DOWN.
#
# The finding this produces is not "16 is wrong" — total debt is a legitimate
# term to form. It is that intelligence/engines.py re-derives it TEN times by
# hand, and every one of those is a place net debt can be re-derived tomorrow
# without touching the library. That is a consolidation lane of its own.
# ⭐ MEASURED AT 2, NOT PREDICTED. Invested capital is ROIC's DENOMINATOR, so
# ROIC's "single owner" status was only ever true of its numerator: the ratio is
# one expression over another and only one of the two was guarded.
#
#     financials/engines.py:314    _n(lambda d,e,pe,mi,c: d+e+pe+mi-c, ...)
#     intelligence/engines.py:594  debt0 + total_equity + preferred + minority - cash
#
# ⭐ SO ROIC SOLE-OWNERSHIP IS A TARGET, NOT A STATE. Recorded as such. The
# ratchet may only go down; consolidating IC is its own segment.
#
# Calibration (standing law: an expected count is meaningless until the counter
# is calibrated against a known population) found TWO detector defects before
# this number was trusted — `_key_of` could not see through `.get(ys)`, and the
# equity operand is a local named `equity` at one site and BS["total_equity"] at
# the other. Uncalibrated, it would have reported 1.
IC_SITES = [
    "services/api/modules/financials/engines.py",
    "services/api/modules/intelligence/engines.py",
]
TOTAL_DEBT_SITES = [
    "services/api/sentinel.py",
    "services/api/modules/valuation/engines.py",
    "services/api/prescience_decision.py",
    "services/api/modules/financials/engines.py",
    "services/api/modules/intelligence/engines.py",
]
# net_debt is CONSOLIDATED — its allowlist is the library and nothing else.
# roic / eva / wacc are single-site but still live in engines.py; moving them is
# Segment D (wacc) and Segment E (roic, after invested capital). Their allowlist
# names the CURRENT home with the owning segment, so the guard is red only on
# real violations — a guard red on work that has not been scheduled yet is
# noise, and noise is how a red stops being read.
ENGINES = "services/api/modules/financials/engines.py"
ALLOWLIST = {"net_debt": [LIBRARY],
             "roic": [ENGINES],        # -> LIBRARY in Segment E (after IC)
             "eva": [ENGINES],         # -> LIBRARY in Segment E
             "wacc": [ENGINES],        # -> LIBRARY in Segment D
             # total_debt is COUNTED, not consolidated — see
             # _total_debt_shape. Its allowlist is the set of
             # callers legitimately forming the base term.
             "total_debt": TOTAL_DEBT_SITES,
             "invested_capital": IC_SITES}
EXPECTED = {"net_debt": 1, "roic": 1, "eva": 1, "wacc": 1,
            "total_debt": 15, "invested_capital": 2}

SCAN_DIRS = ["services/api"]
SKIP = {"__pycache__"}


# ── operand recognisers: what does this expression MEAN, not what is it called ─
def _key_of(node):
    """The last constant string subscript, or the bare name: bs["cash"][ys] -> cash.

    ⭐ IT MUST SEE THROUGH `.get(...)` TOO. Calibration against a known
    population caught this: the inline invested-capital site was detected and
    the `_n` one was not, because financials writes
    `BS["preferred_equity"].get(ys)` — a Call, not a Subscript — and the
    recogniser returned None for every such operand. The counter would have
    reported 1 where there are 2, and an expected count taken from an
    uncalibrated counter is a number about the counter, not the codebase."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
            and node.func.attr == "get":
        node = node.func.value
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
    if not (_is_n_call(node) and len(node.args) == 3):
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




def _is_n_call(node):
    """`_n(...)` OR `fin._n(...)`.

    ⭐ CAUGHT BY THE CONSOLIDATION ITSELF. valuation:126 became
    `fin._n(lambda a, b: a + b, ...)` and the total-debt count silently fell
    15 -> 14, because the recogniser matched only a bare Name `_n`. The site had
    not gone anywhere; the detector stopped seeing it the moment the call was
    written through the module alias — a counter that drops when code is
    IMPROVED reports a fix as a removal."""
    if not isinstance(node, ast.Call):
        return False
    f = node.func
    return ((isinstance(f, ast.Name) and f.id == "_n")
            or (isinstance(f, ast.Attribute) and f.attr == "_n"))


def _total_debt_shape(node):
    """<short_term_debt> + <long_term_debt> — the base term, direct or via _n.

    ⭐ A COUNT, NOT A CONSOLIDATION. Total debt is a legitimate quantity for
    several callers to form; what must not happen is a FOURTH appearing without
    anyone noticing, because each one is a place net debt can be re-derived by
    hand tomorrow."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _is_debt_component(node.left) and _is_debt_component(node.right)
    if _is_n_call(node) and len(node.args) == 3:
        fn = node.args[0]
        if (isinstance(fn, ast.Lambda) and isinstance(fn.body, ast.BinOp)
                and isinstance(fn.body.op, ast.Add)):
            return (_is_debt_component(node.args[1])
                    and _is_debt_component(node.args[2]))
    return False



# The equity operand is spelled `BS["total_equity"]` at one site and a local
# named `equity` at the other. Calibration surfaced the second; matching only
# the first would have counted 1 where there are 2.
_EQUITY_KEYS = {"total_equity", "equity"}


def _is_equity(n):
    return _key_of(n) == "total_equity"


def _ic_shape(node):
    """<debt> + <equity> + <preferred> + <minority> - <cash> — invested capital.

    ⭐ ROIC's DENOMINATOR. Sole ownership of ROIC is hollow while invested
    capital has copies: the ratio is one expression over another, and only one
    of the two was being guarded.

    Matched by composition, not by the variable name `ic`: the add-chain must
    carry total_equity and at least one of preferred_equity / minority_interest,
    and the whole thing must subtract cash. That distinguishes it from net debt
    (whose add-chain is two DEBT components) without relying on either site
    spelling the local the same way.
    """
    def _chain_keys(n, out):
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
            _chain_keys(n.left, out); _chain_keys(n.right, out)
        else:
            k = _key_of(n)
            if k:
                out.add(k)
        return out

    def _match(sub):
        if not (isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.Sub)):
            return False
        if not _is_cash(sub.right):
            return False
        keys = _chain_keys(sub.left, set())
        return (bool(keys & _EQUITY_KEYS)
                and bool(keys & {"preferred_equity", "minority_interest"}))

    if _match(node):
        return True
    # the _n form: _n(lambda d, e, pe, mi, c: d + e + pe + mi - c, ...args)
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == "_n" and len(node.args) >= 4):
        fn = node.args[0]
        if isinstance(fn, ast.Lambda) and isinstance(fn.body, ast.BinOp) \
                and isinstance(fn.body.op, ast.Sub):
            argkeys = {_key_of(a) for a in node.args[1:]}
            return (bool(argkeys & _EQUITY_KEYS)
                    and bool(argkeys & {"preferred_equity", "minority_interest"})
                    and "cash" in argkeys)
    return False


SHAPES = {"net_debt": (_net_debt_shape, _n_call_shape),
          "invested_capital": (_ic_shape,),
          "total_debt": (_total_debt_shape,),
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
        # ⭐ SCOPED TO THE ASSIGNMENT, NOT THE FILE. After consolidation
        # valuation/engines.py legitimately contains "ratios.net_debt" — the
        # line above the bridge calls it. Searching the whole file fired on the
        # fix. The question is only ever whether the COLLIDING KEY was
        # repointed, so look at that statement.
        keyline = next((l for l in csrc.split("\n") if cfrag in l), "")
        bad = [m for m in COLLISION_MUST_NOT_CONTAIN if m in keyline]
        if bad:
            print(f"  ✗ COLLISION SITE REPOINTED AT THE LIBRARY: {bad}\n")
            rc = 1
        else:
            print(f"  ✓ name collision intact and unwired: "
                  f"{cpath} keeps its own net_debt\n")

    for kind in ("net_debt", "total_debt", "invested_capital",
                 "roic", "eva", "wacc"):
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
        if EXPECTED[kind] is not None and len(hits) != EXPECTED[kind]:
            print(f"      ✗ COUNT {len(hits)} != expected {EXPECTED[kind]}")
            rc = 1
        print()

    print("  ✓ sole ownership holds." if rc == 0 else
          "  ✗ sole ownership VIOLATED — see above.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
