#!/usr/bin/env python3
"""Arithmetic on a value that a `.get()` can make None.

⭐ THIS IS THE BACKEND INSTANCE OF THE NULL-SAFETY CLASS. The frontend spent a
pass on it today: 266 bare `.toFixed()` calls on payload values that are null by
design, fixed with lib/num.ts and a lint ratchet. The server has the same defect
in the other direction — it is where the None is MADE.

Production, Sentry PYTHON-2, event c4ac3b4f:

    e = rev[i] - cogs[i] - opex[i] - da[i]
    TypeError: unsupported operand type(s) for -: 'NoneType' and 'NoneType'

`_series` returns `vals.get(str(y))`; `_pvm_full` assembles historicals with a
forecast whose keys need not align. None is a NORMAL value on that path.

WHAT IT FLAGS
  A binary arithmetic expression (+ - * /) where an operand traces back to a
  `.get(...)` with no default, or to indexing a series built from one, inside the
  financials/valuation/intelligence engines.

⭐ ITS BLIND SPOTS, STATED — IT IS A FLOOR, NOT A PROOF:
  · It is syntactic. `a - b` where `a` came from a `.get()` three assignments ago
    is only caught because this tracks simple local aliases; anything passed
    through a function call is invisible.
  · It cannot know that a caller guarantees completeness. Some flagged sites are
    genuinely safe, which is why this reports rather than fails the build.
  · ⭐ CALIBRATED ONCE, AND EVERY FINDING IN THE FIRST RUN WAS A FALSE POSITIVE.
    All 7 were already guarded — a ternary `is not None`, an `if v is None:
    continue`, an `if top:`. A checker that is 7-for-7 wrong gets muted within a
    week, so it now models those three guard forms. That the real codebase
    guards this nearly everywhere is itself the finding: the derivation loop was
    the exception, not the rule.
  · `x / y if y else None` guards the DIVISOR only. A None numerator still
    raises, and that idiom is common here — so those are flagged deliberately.

  · ⭐⭐ IT DOES NOT MODEL THE DOMINANT SHAPE, AND "clean" MUST NOT BE READ AS
    "no defects of this class". This checker knows one source of None: a
    `.get()` with no default. But the dataset's OWN VALUES are None —
    `data["balance_sheet"]["cash"]["2024"]` is None for any period a line item
    does not cover — and those are reached by PLAIN SUBSCRIPT, which this treats
    as safe because a missing key would raise KeyError rather than yield None.

    On 2026-07-30 that blind spot cost three live production sites on
    GET /plan-vs-methods?extend_method=ensemble&horizon=10:
        modules/financials/router.py:284   d["nwc"][i] - d["nwc"][i-1]
        forecast_studio.py:105             BS[...][ys] - BS[...][ys]
        forecast_studio.py:184             (oca - cl) - (prev_oca - prev_cl)
    All three were found by a browser crawl and a unit test. This checker
    reported 0 findings across every run, including on the files that held them,
    and continues to report them clean when the defects are reintroduced —
    verified, not assumed.

    An experimental rule that treats subscript chains rooted at a statement
    block (income_statement / balance_sheet / cash_flow) as nullable surfaces
    ~195 candidate sites across these 8 modules — including auto_forecast:400,
    the same shape as the bug that started this. That is a triage lane, not a
    gate: shipping 195 unactionable findings is how a checker gets muted. The
    measurement is recorded here so the number is known rather than rediscovered.

  · ⭐ MEASURED COVERAGE OF THE `or 0` HALF, 30 Jul — 3 OF 5 KNOWN SITES.
    Controls, run both directions on the real code:
        baseline (all fixed)                    10 findings
        4x health_index + 1x benchmarks re-added 13 findings
        restored                                10 findings
    CAUGHT: health_index's `roic or 0.0`, `current_ratio or 0.0`,
            `debt_to_equity or 0.0` — parameters named after _n()-built keys.
    MISSED: `rev_cagr or 0.0`, because no dict key is named rev_cagr, so the
            name-matching that carries taint across the call boundary has
            nothing to match on.
    MISSED: benchmarks' `(kpis["roic"] or 0)`, because `kpis` is a local dict
            literal and holder-awareness — added to kill five false positives on
            valuation's `deterministic["net_debt"]` — correctly says that
            literal does not build roic with _n, while the values in it in fact
            came from the ratios dict. Precision bought at the cost of recall,
            stated rather than hidden.

  · ⭐ ADDING A MODULE ONCE REMOVED COVERAGE, SILENTLY. Ambiguous key names were
    first subtracted GLOBALLY, so putting benchmarks/engines.py in TARGETS —
    which builds roic/roa/invested_capital plainly — collapsed the key set from
    nine names to three and un-flagged the EVA expression entirely. The finding
    count did not move, so nothing announced it. Subtraction is per-file now and
    cross-module collisions are resolved by holder.

The remedy is `_n(fn, *vals)` in financials/engines.py: absence propagates, and
never `or 0`, because a missing revenue is not zero revenue.
"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = [
    # ⭐ forecast_studio.py WAS MISSING FROM THIS LIST UNTIL 2026-07-30, AND IT
    # HELD TWO LIVE INSTANCES OF THE EXACT CLASS THIS CHECKER EXISTS FOR — the
    # driver fit (`per()` guarded revenue and nothing else) and the balance-sheet
    # roll-forward (`(oca - cl) - (prev_oca - prev_cl)` from an absent opening
    # balance). The checker reported "0 unguarded sites" across 7 modules while
    # both were 500ing /plan-vs-methods.
    #
    # A hand-written target list is the coverage floor this codebase keeps
    # relearning: "0 problems in 0 files" and "0 problems in every file" print
    # the same tick. The list is still hand-written — that is a known weakness,
    # not a solved problem — but the module that fits every forecast driver is
    # now inside it.
    "services/api/forecast_studio.py",
    "services/api/modules/financials/engines.py",
    "services/api/modules/financials/proforma.py",
    "services/api/modules/financials/oci.py",
    "services/api/modules/financials/router.py",
    "services/api/modules/valuation/engines.py",
    # ⭐ ADDED 30 Jul. benchmarks was outside the target list while
    # `(kpis["roic"] or 0) * bases["invested_capital"]` asserted a company earns
    # zero NOPAT when ROIC is merely unknown — and that fabricated zero fed the
    # `excess` column, turning an absent input into a quantified shortfall
    # against the sector benchmark.
    "services/api/modules/benchmarks/engines.py",
    "services/api/modules/intelligence/engines.py",
    "services/api/modules/twin/engines.py",
]
ARITH = (ast.Sub, ast.Add, ast.Mult, ast.Div)


def absence_built_keys(tree):
    """Dict keys whose value is BUILT WITH `_n(...)` — nullable by construction.

    ⭐ THIS EXISTS BECAUSE THE SAME EXPRESSION 500'd FROM THREE DIFFERENT LINES.

        eva_cur  = cur["nopat"] - w["wacc"] * cur["invested_capital"]   # :524
        eva_prev = prev["nopat"] - w["wacc"] * prev["invested_capital"] # :525
        "expected": _r(cur["nopat"] - w["wacc"] * cur["invested_capital"])  # :559

    Fixing them one at a time is how a pair becomes a trio. The durable
    statement is not "line 524 is wrong" but "`nopat` and `invested_capital` are
    None by construction, so arithmetic on them is unguarded wherever it
    appears" — which is what this returns.

    ⭐ IT IS DERIVED, NOT HAND-LISTED. A literal set of key names in this file
    would be a second description of what engines.py builds, and would drift the
    moment a new `_n()`-built key is added — the two-owners defect, inside the
    checker. So the keys are read out of the dict literals that construct them:
    any key whose value expression calls `_n` is nullable, transitively through
    `_r(_n(...))`.

    Deliberately NOT included: keys built with `or 0`. Those never yield None —
    they yield a FABRICATED zero, which is the other half of this class and
    needs a different check, not this one.

    ⭐ THE FIRST VERSION FAILED ITS OWN NEGATIVE CONTROL. It matched only an
    inline `_n(...)` inside the dict value, so it found `"ebitda": _r(_n(...))`
    but not `"nopat": _r(nopat)` — where the `_n` call is one assignment earlier.
    Reintroducing all three EVA copies produced ZERO findings: the checker was
    decorative for precisely the expression it was extended to catch. So a local
    assigned from `_n(...)` carries the taint into the dict that returns it.

    The dataflow is deliberately restricted to `_n` and nothing else. A general
    taint pass was tried on 30 Jul and produced 195 findings while still missing
    the live bug; `_n` is narrow because its entire contract is "returns None
    when any operand is absent", so following it cannot be wrong.
    """
    keys, plain = set(), set()

    def _calls_n(node):
        return any(isinstance(s, ast.Call) and isinstance(s.func, ast.Name)
                   and s.func.id == "_n" for s in ast.walk(node))

    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef,
                               ast.Module)):
            continue
        # locals bound to an _n(...) result, anywhere in this scope
        n_locals = set()
        for a in ast.walk(fn):
            if isinstance(a, ast.Assign) and _calls_n(a.value):
                for t in a.targets:
                    if isinstance(t, ast.Name):
                        n_locals.add(t.id)
        for node in ast.walk(fn):
            if not isinstance(node, ast.Dict):
                continue
            for k, v in zip(node.keys, node.values):
                if not isinstance(k, ast.Constant) or not isinstance(k.value, str):
                    continue
                if _calls_n(v) or any(isinstance(s, ast.Name) and s.id in n_locals
                                      for s in ast.walk(v)):
                    keys.add(k.value)
                else:
                    plain.add(k.value)

    # ⭐ A KEY BUILT BOTH WAYS IS AMBIGUOUS, SO IT IS DROPPED. Matching on the
    # key NAME is what makes this holder-agnostic — the whole point, since the
    # EVA expression must be caught whoever holds the dict. The cost is
    # collisions on generic names: `expected` is absence-built in the EVA
    # checkpoint and plainly built in data_coverage, and flagging
    # `is_c["expected"] + bs_c["expected"]` is a false positive that would teach
    # people to ignore the checker within a week.
    #
    # `nopat` and `invested_capital` survive because nothing in these modules
    # builds them any other way. Dropping the ambiguous names loses coverage
    # rather than inventing precision — the honest trade, and it is stated
    # rather than hidden.
    #
    # ⭐ THE SUBTRACTION MUST BE GLOBAL, AND DOING IT PER FILE WAS A BUG. A key
    # absence-built in financials/engines.py and plainly built in
    # valuation/engines.py survived, because this file's own `plain` did not
    # contain it. That kept `net_debt` in the set and produced five false
    # positives in valuation, where net_debt is
    # `company["_debt_book"] - bs["cash"][ys]` — raw arithmetic, not _n. The
    # caller unions both sets and subtracts once, across every target.
    # Per-file: a key built both ways INSIDE ONE MODULE is ambiguous there
    # (`expected` is absence-built in the EVA checkpoint and plainly built in
    # data_coverage). Cross-module collisions are handled by holder, not by
    # deleting the name — see _nullable / local_dicts.
    return keys - plain, plain


def nullable_dict_keys(tree):
    """{function_name: {keys whose value can be None}} for dict-returning factories.

    ⭐ WHOLE-DICT TAINTING IS A PERMANENTLY-FLAGGED FINDING, WHICH TRAINS PEOPLE
    TO IGNORE THE CHECKER. `picture()` returns a dict where only `equity_value`
    uses `.get()`; every other key is a plain subscript that would raise KeyError,
    not yield None. Tainting the whole return flagged
    `scen["enterprise_value"] - base["enterprise_value"]` forever — a finding
    nobody can act on and nobody can close.

    So nullability is tracked PER KEY."""
    out = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for r in ast.walk(node):
            if not isinstance(r, ast.Return) or not isinstance(r.value, ast.Dict):
                continue
            keys = set()
            for k, v in zip(r.value.keys, r.value.values):
                if not isinstance(k, ast.Constant) or not isinstance(k.value, str):
                    continue
                for sub in ast.walk(v):
                    if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) \
                            and sub.func.attr == "get" and len(sub.args) == 1:
                        keys.add(k.value); break
            if keys:
                out.setdefault(node.name, set()).update(keys)
    return out


def nullable_factories(tree, dict_keyed=()):
    """Functions in this module that RETURN a possibly-None series or value.

    ⭐ WITHOUT THIS THE CHECKER FAILED ITS OWN NEGATIVE CONTROL. Reintroducing the
    exact production defect — `rev[i] - cogs[i] - opex[i] - da[i]` — produced ZERO
    findings, because `rev` comes from `_series(...)`, a function call, and the
    scanner only recognised a literal `.get()`. It was decorative for precisely
    the bug it was written for.

    So a function whose return value is built from `.get()` with no default is
    itself treated as nullable, and calls to it taint their target."""
    out = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name in dict_keyed:
            continue          # handled per-key, not wholesale
        for r in ast.walk(node):
            if not isinstance(r, ast.Return) or r.value is None:
                continue
            for sub in ast.walk(r.value):
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) \
                        and sub.func.attr == "get" and len(sub.args) == 1:
                    out.add(node.name)
    return out


class Scan(ast.NodeVisitor):
    def __init__(self, factories=(), dict_keys=None, absence_keys=()):
        self.factories = set(factories)
        self.absence_keys = set(absence_keys)
        self.dict_keys = dict_keys or {}      # fn -> {nullable key names}
        self.from_fn = {}                     # local name -> factory it came from
        self.local_dicts = {}                 # local name -> keys nullable in it
        self.risky = set()      # names bound to a possibly-None expression
        self.hits = []
        self.fn = "<module>"

    # ---- does this expression evaluate to something that can be None? -------
    def _nullable(self, node):
        if isinstance(node, ast.Call):
            f = node.func
            # x.get(k)  with no default
            if isinstance(f, ast.Attribute) and f.attr == "get" and len(node.args) == 1:
                return True
            # a call to a function that builds its result from .get()
            if isinstance(f, ast.Name) and f.id in self.factories:
                return True
        if isinstance(node, ast.Subscript):
            # ⭐ a key that engines.py builds with _n() is None BY CONSTRUCTION,
            # whoever is holding the dict. This is what makes the EVA expression
            # a finding at every site rather than at the one that happened to be
            # reported.
            k0 = node.slice
            # ⭐ A HOLDER BUILT RIGHT HERE ANSWERS FOR ITSELF. `deterministic`
            # in valuation/engines.py is a dict literal whose net_debt is
            # `company["_debt_book"] - bs["cash"][ys]` — plain arithmetic, not
            # _n. It merely SHARES A KEY NAME with the ratios dict, and matching
            # on the name alone produced five false positives there. When the
            # holder is a local dict literal, its own construction decides.
            if isinstance(node.value, ast.Name) and node.value.id in self.local_dicts:
                return (isinstance(k0, ast.Constant)
                        and k0.value in self.local_dicts[node.value.id])
            if isinstance(k0, ast.Constant) and k0.value in self.absence_keys:
                return True
            # a dict from a per-key factory: only the nullable keys are risky
            if isinstance(node.value, ast.Name) and node.value.id in self.from_fn:
                fn = self.from_fn[node.value.id]
                k = node.slice
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    return k.value in self.dict_keys.get(fn, set())
                return False
            return self._nullable(node.value) or (
                isinstance(node.value, ast.Name) and node.value.id in self.risky)
        if isinstance(node, ast.Name):
            return node.id in self.risky
        if isinstance(node, ast.ListComp):
            return self._nullable(node.elt)
        if isinstance(node, ast.BinOp):
            return self._nullable(node.left) or self._nullable(node.right)
        return False

    def visit_FunctionDef(self, node):
        prev, self.fn = self.fn, node.name
        prev_risky = set(self.risky)
        # ⭐ A PARAMETER NAMED AFTER AN ABSENCE-BUILT KEY IS THE SAME VALUE, ONE
        # CALL LATER. health_index(roic, wacc_value, current_ratio,
        # debt_to_equity, rev_cagr) is handed exactly the ratios-dict values
        # that _n() makes None, and it used `or 0.0` on four of them — but they
        # arrive as bare parameters, so subscript-based matching saw nothing.
        # The caller's key set is the callee's contract; matching on the name is
        # how the taint survives the call boundary without a full interprocedural
        # pass (tried on 30 Jul: 195 findings and still blind).
        self.risky |= {a.arg for a in node.args.args
                       if a.arg in self.absence_keys}
        self.generic_visit(node)
        self.fn, self.risky = prev, prev_risky

    def visit_Assign(self, node):
        # remember which per-key factory a local came from
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) \
                and node.value.func.id in self.dict_keys:
            for t in node.targets:
                if isinstance(t, ast.Name):
                    self.from_fn[t.id] = node.value.func.id
        if isinstance(node.value, ast.Dict):
            nk = set()
            for k, v in zip(node.value.keys, node.value.values):
                if isinstance(k, ast.Constant) and isinstance(k.value, str) \
                        and any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name)
                                and x.func.id == "_n" for x in ast.walk(v)):
                    nk.add(k.value)
            for t in node.targets:
                if isinstance(t, ast.Name):
                    self.local_dicts[t.id] = nk
        if self._nullable(node.value):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    self.risky.add(t.id)
        self.generic_visit(node)

    # ---- guards that make a name safe from here on ------------------------
    def _guarded_names(self, test):
        """Names this test proves non-None: `x is not None`, `if x:`, `x and y`."""
        out = set()
        if isinstance(test, ast.Compare) and len(test.ops) == 1:
            if isinstance(test.ops[0], ast.IsNot) and \
                    isinstance(test.comparators[0], ast.Constant) and \
                    test.comparators[0].value is None and \
                    isinstance(test.left, ast.Name):
                out.add(test.left.id)
        elif isinstance(test, ast.Name):
            out.add(test.id)                      # `if x:`
        elif isinstance(test, ast.BoolOp):
            for v in test.values:
                out |= self._guarded_names(v)
        return out

    def visit_If(self, node):
        # `if x is None: continue/return` protects everything after it
        neg = set()
        t = node.test
        bails = any(isinstance(b, (ast.Continue, ast.Return, ast.Raise))
                    for b in node.body)

        def _is_none_names(x):
            """Names proven non-None AFTER `if <x> is None: bail`.

            ⭐ THE DISJUNCTIVE FORM WAS NOT MODELLED, AND IT FLAGGED A GUARD THIS
            VERY LANE HAD JUST WRITTEN. `if f is None or a is None: continue` is
            the natural way to guard a pair, and the checker saw only the
            single-name shape — so `a - f` three lines later came back as an
            unguarded site. A checker that flags the correct fix teaches people
            to write the incorrect one, or to stop reading it.
            """
            if isinstance(x, ast.Compare) and len(x.ops) == 1 \
                    and isinstance(x.ops[0], ast.Is) \
                    and isinstance(x.comparators[0], ast.Constant) \
                    and x.comparators[0].value is None \
                    and isinstance(x.left, ast.Name):
                return {x.left.id}
            if isinstance(x, ast.BoolOp) and isinstance(x.op, ast.Or):
                out = set()
                for v in x.values:
                    out |= _is_none_names(v)
                return out
            return set()

        if bails:
            neg |= _is_none_names(t)
        saved = set(self.risky)
        self.risky -= self._guarded_names(node.test)      # inside the true branch
        for b in node.body:
            self.visit(b)
        self.risky = saved - neg                          # after the guard
        for b in node.orelse:
            self.visit(b)

    def visit_IfExp(self, node):
        # `expr if (a is not None and b is not None) else None`
        saved = set(self.risky)
        self.risky -= self._guarded_names(node.test)
        self.visit(node.body)
        self.risky = saved
        self.visit(node.orelse)

    def visit_BoolOp(self, node):
        """⭐ `X or 0` ON A VALUE THAT IS None BY CONSTRUCTION — THE OTHER HALF.

        This checker was built for arithmetic that RAISES. The sibling defect
        does not raise: `or 0` swaps absence for a fabricated zero and the code
        runs cleanly to a wrong answer. Both halves were live on 30 Jul in the
        same function — `eva_cur` raised, and four lines later
        `(cur["roic"] or 0) > w["wacc"]` reported "value-eroding" about a company
        whose ROIC was not computable.

        A raise is loud. A fabricated zero is a number a board reads. This flags
        the quiet one, on the same derived key set — so it cannot drift from
        what engines.py actually builds with _n().
        """
        if isinstance(node.op, ast.Or) and len(node.values) == 2:
            left, right = node.values
            zero = (isinstance(right, ast.Constant)
                    and right.value in (0, 0.0) and right.value is not False)
            if zero and self._nullable(left):
                self.hits.append((node.lineno, self.fn,
                                  ast.unparse(node)[:78], "or-0"))
        self.generic_visit(node)

    def visit_BinOp(self, node):
        if isinstance(node.op, ARITH):
            l, r = self._nullable(node.left), self._nullable(node.right)
            if l or r:
                self.hits.append((node.lineno, self.fn,
                                  ast.unparse(node)[:78],
                                  "both" if (l and r) else "one"))
        self.generic_visit(node)


def main():
    total = 0
    per_file = []
    absence_keys, plain_keys = set(), set()
    for rel in TARGETS:
        path = os.path.join(ROOT, rel)
        if os.path.exists(path):
            k, _pl = absence_built_keys(
                ast.parse(open(path, encoding="utf-8").read()))
            absence_keys |= k
    # ⭐ GLOBAL SUBTRACTION WAS WORSE THAN THE PROBLEM IT SOLVED. Subtracting
    # every plainly-built key across all targets meant that ADDING A MODULE
    # REMOVED COVERAGE ELSEWHERE: putting benchmarks/engines.py in TARGETS —
    # which builds roic/roa/invested_capital plainly — collapsed the key set
    # from nine to three and silently un-flagged the EVA expression. The finding
    # count did not move, so nothing announced the loss. A checker that gets
    # quieter when you widen it is the coverage-floor failure in its purest form.
    #
    # Ambiguity is now resolved by HOLDER (see _local_dicts) rather than by
    # deleting key names, so a collision suppresses one expression instead of a
    # whole class.
    for rel in TARGETS:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        src = open(path, encoding="utf-8").read()
        tree = ast.parse(src)
        dk = nullable_dict_keys(tree)
        sc = Scan(nullable_factories(tree, dk), dk, absence_keys)
        sc.visit(tree)
        # a site already routed through _n() is handled
        hits = [h for h in sc.hits if "_n(" not in h[2]]
        per_file.append((rel, hits))
        total += len(hits)

    print(f"  {len(per_file)} module(s) scanned · {total} unguarded arithmetic site(s)\n")
    for rel, hits in per_file:
        if not hits:
            print(f"    {rel:<52} clean")
            continue
        print(f"    {rel}  ({len(hits)})")
        for line, fn, expr, kind in hits[:40]:
            print(f"      :{line:<5} {fn:<28} [{kind}] {expr}")
    print(f"\n  Report-only: some sites are genuinely safe because a caller "
          f"guarantees\n  completeness. The remedy where they are not is "
          f"_n(fn, *vals) — absence\n  propagates; never `or 0`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
