#!/usr/bin/env python3
"""Arithmetic on a statement-block value reached by PLAIN SUBSCRIPT.

    BS["cash"][ys] - BS["short_term_debt"][ys]      <- raises when either is None
    BS["cash"].get(ys) - ...                        <- absence-safe, not a finding

Statement-block values are None BY DESIGN on any dataset that does not cover
every line item in every period. A plain subscript hands that None straight to
the arithmetic, which raises.

⭐ THIS IS WHY FOUR OF FIVE SINGLE-OWNER QUANTITIES CANNOT DEMONSTRATE THEIR OWN
ABSENCE BEHAVIOUR. net_debt, invested_capital, ROIC and WACC all propagate
absence correctly inside ratios.py — and the entry points still raise before
reaching them:

    valuation.run        raises in auto_forecast, before net_debt
    valuation.multiples  raises after net_debt, at the bridge
    intelligence brief   raises upstream of net_debt
    dp_optimize          raises before invested_capital

Only financials.derive_series -> the dashboard KPI gets a None all the way to a
rendered em dash. The libraries are correct and unobservable.

⭐ THE RATCHET IS 36, MEASURED — AND THE ~195 IT REPLACES WAS MINE, UNCALIBRATED.
That figure came from a loose experimental rule on 30 Jul which counted `.get()`
forms (absence-SAFE) and each operand of an expression separately. It sat in the
ledger for two days and the disposition drawn from it — "larger than any segment
so far, it gets its own era" — was wrong. 36 sites in 7 modules, 25 of them
upstream of a rendered surface, is a segment.

An expected count is meaningless until the counter is calibrated against a known
population. This one is calibrated below, in both directions, on every run.
"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOCKS = {"income_statement", "balance_sheet", "cash_flow"}
ARITH = (ast.Add, ast.Sub, ast.Mult, ast.Div)

# Measured 2026-08-01. Downward-only: this number may fall as modules are
# converted, and may not rise without the evidence a rise demands.
# ⭐⭐ 69, AND THE FOURTH CORRECTION TO THIS NUMBER — THIS ONE UPWARD.
#
#   ~195  uncalibrated: counted .get() forms (absence-SAFE) and every operand
#     36  calibrated shape
#     29  validator idiom modelled (7 sites provably guarded by `if not errors:`)
#     20  after converting auto_forecast's 9
#     69  ⭐ tuple-unpacked block bindings made visible
#
# `IS, BS, CF = data["income_statement"], data["balance_sheet"], data["cash_flow"]`
# appears at engines.py:266, :486 and :991 and is the COMMON binding form. Only
# the single-target form was handled, so BS/IS/CF were never registered and every
# site using them was invisible — including two entire modules
# (financials/proforma.py at 17, and 19 more in intelligence/engines.py).
#
# RAISING A RATCHET IS NORMALLY FORBIDDEN. Permitted here under the
# counter-corrected category: measured on the SAME tree both ways, the
# pre-conversion codebase reads 78 and the post-conversion 69. The nine
# conversions are real and reduced it; the rest was always there and unseen.
#
# ⭐ FOUND BY TRACING A RAISE THE GUARD SAID COULD NOT EXIST — engines.py:502
# still raised after the module was reported converted. A guard is only as good
# as the last thing that contradicted it.
EXPECTED_TOTAL = 86
# LOWERED 97 -> 86 ON 30 Jul: financials/engines.py converted, 11 -> 0 under the
# current model. Downward only; the 97 above was itself a counter correction.
# ⭐ RAISED 69 -> 97 ON 30 Jul, AND THE RAISE IS A COUNTER CORRECTION WITH THE
# CODEBASE UNCHANGED — the permitted category, not a new defect. Modelling the
# LOCAL-BINDING HOP (`pref = bs["preferred_equity"][ys]` then `ev - pref - mino`,
# valuation:146) revealed 28 sites the counter could not see. No application code
# was touched between the two measurements.
#
# ⭐ THE FIFTH TIME THIS COUNTER WAS WRONG, AND THE FIFTH TIME IT WAS WRONG IN
# THE DIRECTION THAT HIDES WORK: ~195 -> 36 -> 29 -> 69 -> 97. Every advance made
# without first widening the counter measured the scanner instead of the code.
#
# Per-module effect of the widening:
#     intelligence/engines.py   24 -> 33      valuation/engines.py    3 -> 12
#     financials/proforma.py    17 -> 24      sentinel.py             1 ->  3
#     financials/engines.py     11 -> 11      prescience_decision.py  1 ->  2
# financials/engines.py is UNCHANGED, so the mid-module segment's remaining
# figure of 11 survives the recalibration.

# Modules whose output reaches a surface a customer sees. A delta here is
# customer-visible; elsewhere it is internal or batch.
RENDERED = {
    "services/api/modules/financials/engines.py",
    "services/api/modules/financials/router.py",
    "services/api/modules/valuation/engines.py",
    "services/api/modules/intelligence/engines.py",
    "services/api/modules/twin/engines.py",
    "services/api/modules/benchmarks/engines.py",
    "services/api/reporting.py",
    "services/api/report_pdf.py",
    "services/api/forecast_studio.py",
}


def _subscript_depth(node):
    d = 0
    while isinstance(node, ast.Subscript):
        d += 1
        node = node.value
    return d, node


def _block_rooted(node, blocks):
    """A plain subscript chain rooted at a statement-block name.

    `.get(...)` breaks the chain deliberately — an absence-safe accessor is not
    this defect, and counting it would make the guard fire on its own remedy."""
    depth = 0
    while isinstance(node, ast.Subscript):
        depth += 1
        node = node.value
    if depth < 1:
        return False
    return isinstance(node, ast.Name) and node.id in blocks


class Scan(ast.NodeVisitor):
    """⭐ MODELS THE VALIDATOR IDIOM, because 7 of the first 16 sites were not
    defects.

    financials.validate_dataset does its balance-sheet arithmetic inside

        if not errors:
            assets = bs["cash"][str(y)] + bs["other_current_assets"][str(y)] + ...

    where `errors` is the list the validation loop appends every missing or
    non-numeric value to. Reaching that arithmetic PROVES every operand is
    present and numeric. Verified empirically rather than assumed — removing
    cash, total_equity, preferred_equity or noncurrent_assets each produces an
    error naming it and never reaches the arithmetic.

    Counting them would have meant converting seven safe sites and reporting a
    class 24% larger than it is. The guard that is actually there has to be
    modelled, or the count is about the scanner."""

    def __init__(self):
        self.blocks = set(BLOCKS)
        self.hits = []
        self.fn = "<module>"
        self._err_lists = set()   # names built by .append() in this function
        self._guarded = 0         # depth inside `if not <err_list>:`
        self._tainted = set()     # locals holding a plain-subscript VALUE

    def visit_FunctionDef(self, n):
        p, self.fn = self.fn, n.name
        prev_lists, prev_g = set(self._err_lists), self._guarded
        prev_taint = set(self._tainted)
        self._tainted = set()
        self._guarded = 0
        # names this function appends to — the validator's error accumulator
        self._err_lists = {
            c.func.value.id
            for c in ast.walk(n)
            if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
            and c.func.attr == "append" and isinstance(c.func.value, ast.Name)}
        self.generic_visit(n)
        self.fn, self._err_lists, self._guarded = p, prev_lists, prev_g
        self._tainted = prev_taint

    def visit_If(self, n):
        t = n.test
        is_clear = (isinstance(t, ast.UnaryOp) and isinstance(t.op, ast.Not)
                    and isinstance(t.operand, ast.Name)
                    and t.operand.id in self._err_lists)
        if is_clear:
            self._guarded += 1
            for b in n.body:
                self.visit(b)
            self._guarded -= 1
            for b in n.orelse:
                self.visit(b)
        else:
            self.generic_visit(n)

    def visit_Assign(self, n):
        """locals bound to a block, in BOTH binding forms.

        ⭐ THE TUPLE UNPACK WAS INVISIBLE, AND IT IS THE COMMON FORM.

            IS, BS, CF = (data["income_statement"], data["balance_sheet"],
                          data["cash_flow"])

        appears at engines.py:266, :486 and :991. Only the single-target form was
        handled, so BS/IS/CF were never registered as block names and every
        plain-subscript site using them was uncounted — including
        engines.py:502, which still raised after this module was reported
        converted. Found by tracing a raise the guard said could not exist."""
        vals = (n.value.elts if isinstance(n.value, (ast.Tuple, ast.List))
                else [n.value])
        for t in n.targets:
            tgts = (t.elts if isinstance(t, (ast.Tuple, ast.List)) else [t])
            pairs = zip(tgts, vals) if len(tgts) == len(vals) else \
                [(x, n.value) for x in tgts]
            for name, val in pairs:
                if not isinstance(name, ast.Name) or not isinstance(val, ast.Subscript):
                    continue
                k = val.slice
                if isinstance(k, ast.Constant) and k.value in BLOCKS:
                    self.blocks.add(name.id)

        # ⭐ THE LOCAL-BINDING HOP, AND ITS ABSENCE MADE 69 A FLOOR.
        #     pref = bs["preferred_equity"][ys]
        #     mino = bs["minority_interest"][ys]
        #     equity = ev - net_debt - pref - mino          valuation:146
        # Every operand is a plain subscript and the arithmetic is identical to
        # the modelled form; only the BINDING differs. Matching the inline shape
        # and not this one counts the way a defect is SPELLED rather than what it
        # is — the same error as counting by identifier.
        #
        # Depth >= 2 so a BLOCK binding (`bs = data["balance_sheet"]`) is never
        # mistaken for a VALUE, and `.get()` still breaks the chain, so an
        # absence-safe local is not tainted.
        for t in n.targets:
            tgts = (t.elts if isinstance(t, (ast.Tuple, ast.List)) else [t])
            vs = (n.value.elts if isinstance(n.value, (ast.Tuple, ast.List))
                  and len(n.value.elts) == len(tgts) else [n.value] * len(tgts))
            for name, val in zip(tgts, vs):
                if not isinstance(name, ast.Name):
                    continue
                depth, _root = _subscript_depth(val)
                if depth >= 2 and _block_rooted(val, self.blocks) and not self._guarded:
                    self._tainted.add(name.id)
        self.generic_visit(n)

    def visit_BinOp(self, n):
        if isinstance(n.op, ARITH) and not self._guarded:
            for side in (n.left, n.right):
                if (_block_rooted(side, self.blocks)
                        or (isinstance(side, ast.Name) and side.id in self._tainted)):
                    self.hits.append((n.lineno, self.fn, ast.unparse(n)[:58]))
                    break
        self.generic_visit(n)


# ── calibration, run before any count is believed ───────────────────────────
POSITIVE = [
    ("arithmetic OUTSIDE a cleared-errors guard still counts",
     'def f(data, ys):\n'
     '    errors = []\n'
     '    errors.append("x")\n'
     '    bs = data["balance_sheet"]\n'
     '    return bs["cash"][ys] + bs["short_term_debt"][ys]'),
    ("auto_forecast site that masks valuation.run",
     'BS = data["balance_sheet"]\n'
     'x = BS["other_current_assets"][str(y)] - BS["current_liabilities_ex_debt"][str(y)]'),
    ("dp_optimize debt0 that masks the IC site",
     'bs = data["balance_sheet"]\n'
     'debt0 = bs["short_term_debt"][ys] + bs["long_term_debt"][ys]'),
    ("income statement, aliased block",
     'IS = data["income_statement"]\nx = IS["revenue"][ys] - IS["cogs"][ys]'),
    ("⭐ TUPLE-UNPACKED blocks — the common binding form",
     'IS, BS, CF = data["income_statement"], data["balance_sheet"], data["cash_flow"]\n'
     'x = BS["other_current_assets"][str(y)] - BS["current_liabilities_ex_debt"][str(y)]'),
    ("⭐ LOCAL-BINDING HOP — valuation:146, the fifth correction",
     'bs = data["balance_sheet"]\n'
     'pref = bs["preferred_equity"][ys]\n'
     'mino = bs["minority_interest"][ys]\n'
     'equity = ev - pref - mino'),
]
NEGATIVE = [
    ("a local bound from .get() is absence-safe, not tainted",
     'bs = data["balance_sheet"]\n'
     'pref = bs["preferred_equity"].get(ys)\n'
     'x = ev - pref'),
    ("a BLOCK binding is not a tainted VALUE",
     'bs = data["balance_sheet"]\nx = ev - 1'),
    ("a tainted local inside `if not errors:` is proven present",
     'def f(data, ys, ev):\n'
     '    errors = []\n'
     '    errors.append("x")\n'
     '    if not errors:\n'
     '        bs = data["balance_sheet"]\n'
     '        pref = bs["preferred_equity"][ys]\n'
     '        return ev - pref'),
    ("arithmetic inside `if not errors:` — operands proven present",
     'def f(data, years):\n'
     '    errors = []\n'
     '    errors.append("x")\n'
     '    if not errors:\n'
     '        bs = data["balance_sheet"]\n'
     '        for y in years:\n'
     '            a = bs["cash"][str(y)] + bs["other_current_assets"][str(y)]'),
    ("the SAME expression written with .get()",
     'BS = data["balance_sheet"]\nx = BS["cash"].get(ys) - BS["short_term_debt"].get(ys)'),
    ("an absence-safe accessor helper",
     'x = _bs(data, "cash", ys) - _bs(data, "short_term_debt", ys)'),
    ("_n() over .get() operands",
     'BS = data["balance_sheet"]\n'
     'x = _n(lambda a, b: a - b, BS["cash"].get(ys), BS["long_term_debt"].get(ys))'),
    ("subscript with no arithmetic",
     'bs = data["balance_sheet"]\nx = bs["cash"][ys]'),
]


def calibrate():
    bad = []
    for label, src in POSITIVE:
        sc = Scan()
        sc.visit(ast.parse(src))
        if not sc.hits:
            bad.append(("MISSED", label))
    for label, src in NEGATIVE:
        sc = Scan()
        sc.visit(ast.parse(src))
        if sc.hits:
            bad.append(("FALSE POSITIVE", label))
    return bad


def main():
    bad = calibrate()
    if bad:
        print("  ✗ CALIBRATION FAILED — the count below is not to be believed:")
        for kind, label in bad:
            print(f"      {kind}: {label}")
        return 2
    print(f"  ✓ calibration: {len(POSITIVE)} positive, {len(NEGATIVE)} negative "
          f"(absence-safe forms rejected)\n")

    per_file, total, rendered = [], 0, 0
    for base, dirs, files in os.walk(os.path.join(ROOT, "services/api")):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in sorted(files):
            if not f.endswith(".py"):
                continue
            rel = os.path.relpath(os.path.join(base, f), ROOT)
            try:
                tree = ast.parse(open(os.path.join(base, f),
                                     encoding="utf-8").read())
            except Exception:
                continue
            sc = Scan()
            sc.visit(tree)
            if sc.hits:
                per_file.append((rel, sc.hits))
                total += len(sc.hits)
                if rel in RENDERED:
                    rendered += len(sc.hits)

    per_file.sort(key=lambda r: -len(r[1]))
    print(f"  {'module':<50} {'sites':>6}  rendered?")
    for rel, hits in per_file:
        print(f"  {rel:<50} {len(hits):>6}  "
              f"{'YES' if rel in RENDERED else '-'}")
    print(f"\n  {total} site(s) in {len(per_file)} module(s) · expected "
          f"{EXPECTED_TOTAL}")
    print(f"  upstream of a rendered surface: {rendered}")

    if total > EXPECTED_TOTAL:
        print(f"\n  ✗ RATCHET BROKEN: {total} > {EXPECTED_TOTAL}. A new site of "
              f"this class was added.")
        return 1
    if total < EXPECTED_TOTAL:
        print(f"\n  ✓ {EXPECTED_TOTAL - total} site(s) converted since the "
              f"ratchet was set. Lower EXPECTED_TOTAL to {total} to lock it in.")
        return 1
    print("\n  ✓ at the ratchet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
