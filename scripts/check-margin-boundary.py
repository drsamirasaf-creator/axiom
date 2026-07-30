#!/usr/bin/env python3
"""Class A: margins are prevented by BOUNDARY, not detected by shape.

⭐ WHY THIS EXISTS AND THE SHAPE SCAN CANNOT DO IT. Thirteen registry ratios are
`@0/@1*100`. `gross_profit / revenue` and `ebit / revenue` are the SAME
arithmetic; no scan, however sharp, can tell them apart, because there is nothing
to tell apart. The question a shape scan asks — "does this arithmetic appear
twice?" — has no useful answer here. The question this asks is different and
answerable: **WHERE may this arithmetic live at all?**

That is an import/boundary rule. It is falsifiable in a way a shape count is not:
plant a margin in a new module and it fails.

⭐ A RATCHET, NOT A CLEAN-SLATE RULE. Five modules compute margins today across
20 sites. Declaring "only ratios.py" would fail on the first run and be
suppressed within a week. The declared set below is downward-only: a NEW module
computing a margin fails, and a module whose count FALLS must be recorded here,
so the number can only shrink.

⭐ WHAT COUNTS AS A MARGIN, and why the first detector was thrown away. It read
the denominator node's own name and missed the two dominant idioms here —
`_n(lambda a, b: a / b, ebit[i], rev[i])`, where the denominator is a lambda
PARAMETER, and `IS['revenue'][str(y)]`, a nested subscript with a non-literal
key. Both are margins in financials/engines.py and both were reported absent.
Denominators are read as SOURCE TEXT with `_n` lambdas resolved param->argument.

A growth rate is NOT a margin: `rev[i] / rev[i-1]` divides by revenue and is a
different quantity. Excluded when numerator and denominator name the same scale.
"""
import ast
import collections
import os
import re
import sys

SCALE = re.compile(r'(revenue|\brev\b|sales|turnover|total_assets|'
                   r'total_equity|\bequity\b|ebitda|invested_capital)', re.I)
ROOTS = ["services"]
OWNER = os.path.join("services", "api", "modules", "financials", "ratios.py")

# ── THE DECLARED BOUNDARY. Downward-only. ───────────────────────────────────
# Measured 2026-07-30. Lower a number when sites move to the owner; never raise
# one. A module absent from this dict may not compute a margin at all.
ALLOWED = {
    # ⭐ 7 -> 8 ON 30 Jul, AND IT IS A COUNTER CORRECTION, NOT A NEW MARGIN.
    # The EBIT-margin driver fit was being excluded as a GROWTH RATE: the
    # numerator (revenue - cogs - opex - d&a) shares the word "revenue" with the
    # denominator, and the growth-exclusion heuristic keys on exactly that
    # overlap. Wrapping the fit in _n() moved the numerator to lambda parameters,
    # the overlap vanished, and the site was counted for the first time.
    #
    # THE HEURISTIC HAS A FALSE-NEGATIVE MODE, recorded here rather than fixed:
    # any margin whose numerator mentions its own denominator's line item reads
    # as a growth rate. rev[i]/rev[i-1] must stay excluded, so the fix is not to
    # drop the rule — it is to compare the RESOLVED operands rather than their
    # source text. Queued, not done.
    os.path.join("services", "api", "modules", "financials", "engines.py"): 8,
    os.path.join("services", "api", "modules", "benchmarks", "engines.py"): 7,
    os.path.join("services", "api", "modules", "intelligence", "engines.py"): 4,
    os.path.join("services", "api", "accounts.py"): 1,
    os.path.join("services", "api", "core", "refcompanies.py"): 1,
    OWNER: 99,          # the intended destination; no ceiling
}


def _src(n):
    try:
        return ast.unparse(n)
    except Exception:
        return ""


def divisions(tree):
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
            if nm == "_n" and n.args and isinstance(n.args[0], ast.Lambda):
                lam = n.args[0]
                bind = {p.arg: _src(a) for p, a in zip(lam.args.args, n.args[1:])}
                for d in ast.walk(lam.body):
                    if isinstance(d, ast.BinOp) and isinstance(d.op, ast.Div):
                        yield (n.lineno,
                               bind.get(_src(d.left), _src(d.left)),
                               bind.get(_src(d.right), _src(d.right)))
                continue
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div):
            yield (n.lineno, _src(n.left), _src(n.right))


def margins_in(text):
    """(lineno, denominator) for every margin-shaped division."""
    out = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return out
    for ln, num, den in divisions(tree):
        if not SCALE.search(den):
            continue
        nb = set(re.findall(r'[A-Za-z_]\w*', num))
        db = set(re.findall(r'[A-Za-z_]\w*', den))
        if {w for w in nb & db if SCALE.search(w)}:
            continue                       # growth rate, not a margin
        out.append((ln, den))
    return out


def survey():
    found = collections.defaultdict(list)
    for root in ROOTS:
        for dp, _, fs in os.walk(root):
            if "__pycache__" in dp:
                continue
            for fn in fs:
                if not fn.endswith(".py"):
                    continue
                p = os.path.join(dp, fn)
                m = margins_in(open(p, encoding="utf-8").read())
                if m:
                    found[p] = m
    return found


def control():
    """⭐ KNOWN-POSITIVE: the check must fire on a margin planted outside the
    boundary. Run every invocation, because a boundary rule that has never
    rejected anything is indistinguishable from one that cannot."""
    cases = [
        ("plain",   "def f(gp, revenue):\n    return gp / revenue * 100\n"),
        ("wrapped", "def f(a, b):\n    return _n(lambda x, y: x / y, ebit, revenue)\n"),
        ("subscript", "def f(IS, y):\n    return (IS['ebit'][y]) / IS['revenue'][str(y)]\n"),
    ]
    bad = [name for name, src in cases if not margins_in(src)]
    neg = margins_in("def f(rev, i):\n    return rev[i] / rev[i - 1] - 1\n")
    return bad, neg


def main():
    bad, neg = control()
    print("KNOWN-POSITIVE CONTROL")
    if bad:
        print(f"  ✗ did NOT fire on: {bad} — the boundary check is inert, nothing below is meaningful")
        return 2
    print("  ✓ fires on a planted margin in all 3 idioms (plain, _n-wrapped, nested subscript)")
    if neg:
        print(f"  ✗ negative control FAILED: a growth rate was counted as a margin")
        return 2
    print("  ✓ negative control: a growth rate (rev[i]/rev[i-1]) is not counted")
    print()

    found = survey()
    print("MARGIN SITES BY MODULE")
    total = 0
    for p, m in sorted(found.items(), key=lambda kv: -len(kv[1])):
        total += len(m)
        cap = ALLOWED.get(p)
        state = "declared" if cap is not None else "⭐ NOT DECLARED"
        print(f"  {len(m):>3}  {p}   [{state}{'' if cap is None else f', cap {cap}'}]")
    print(f"\n  {total} sites across {len(found)} modules")
    print()

    fail = 0
    for p, m in sorted(found.items()):
        cap = ALLOWED.get(p)
        if cap is None:
            print(f"✗ NEW MODULE COMPUTING A MARGIN: {p}")
            for ln, den in m[:5]:
                print(f"    line {ln}: / {den[:50]}")
            print("  Margins belong in services/api/modules/financials/ratios.py.")
            print("  This is Class A: it cannot be caught by shape, only by place.")
            fail = 1
        elif len(m) > cap:
            print(f"✗ RATCHET RAISED: {p} has {len(m)} margin sites, declared {cap}")
            fail = 1
        elif len(m) < cap:
            print(f"⚠ RATCHET SHOULD FALL: {p} has {len(m)}, declared {cap} — lower it here")
            fail = 1
    if not fail:
        print("✓ every margin site sits in a declared module, none above its cap")
    return fail


if __name__ == "__main__":
    sys.exit(main())
