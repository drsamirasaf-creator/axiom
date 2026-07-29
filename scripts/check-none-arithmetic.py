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

The remedy is `_n(fn, *vals)` in financials/engines.py: absence propagates, and
never `or 0`, because a missing revenue is not zero revenue.
"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = [
    "services/api/modules/financials/engines.py",
    "services/api/modules/financials/proforma.py",
    "services/api/modules/financials/oci.py",
    "services/api/modules/financials/router.py",
    "services/api/modules/valuation/engines.py",
    "services/api/modules/intelligence/engines.py",
    "services/api/modules/twin/engines.py",
]
ARITH = (ast.Sub, ast.Add, ast.Mult, ast.Div)


def nullable_factories(tree):
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
        for r in ast.walk(node):
            if not isinstance(r, ast.Return) or r.value is None:
                continue
            for sub in ast.walk(r.value):
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) \
                        and sub.func.attr == "get" and len(sub.args) == 1:
                    out.add(node.name)
    return out


class Scan(ast.NodeVisitor):
    def __init__(self, factories=()):
        self.factories = set(factories)
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
        self.generic_visit(node)
        self.fn, self.risky = prev, prev_risky

    def visit_Assign(self, node):
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
        if isinstance(t, ast.Compare) and len(t.ops) == 1 and isinstance(t.ops[0], ast.Is) \
                and isinstance(t.comparators[0], ast.Constant) \
                and t.comparators[0].value is None and isinstance(t.left, ast.Name) \
                and any(isinstance(b, (ast.Continue, ast.Return, ast.Raise)) for b in node.body):
            neg.add(t.left.id)
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
    for rel in TARGETS:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        src = open(path, encoding="utf-8").read()
        tree = ast.parse(src)
        sc = Scan(nullable_factories(tree))
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
