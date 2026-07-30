#!/usr/bin/env python3
"""Value-agreement step 1: the route table and INDEPENDENT route counts.

⭐ A PRODUCER IS NOT A ROUTE. A module emitting `{"wacc": w}` may be RELAYING a
value another module computed, or RECOMPUTING it. A relay cannot disagree with
its source; only a recompute can. Static analysis cannot separate them by name,
which is why the harness must be a runtime comparison — but it CAN separate them
by what the value expression does, and that is what decides how much work the
comparison actually is.

    RECOMPUTE  the value expression performs arithmetic, or calls a function
               that is not the sole-owner library
    OWNER      the value expression calls services/api/modules/financials/ratios
    RELAY      a bare name, subscript, or a rounding wrapper over one — it
               carries a value computed elsewhere

INDEPENDENT ROUTES = distinct RECOMPUTE sites, plus the owner if used. A quantity
with ONE independent route needs no comparison: sole ownership already holds, and
that is the success condition rather than an absence of coverage.

⭐ THE COMPARISON SET IS THE OUTPUT, NOT THE PRODUCER COUNT. Reporting "9 of 12
quantities have multiple producers" overstates the work if most are relays.

Prints counts and module paths only — no company names, no figures.
"""
import ast
import collections
import os
import sys

ROOTS = ["services"]
OWNER_MODULES = ("financials/ratios.py",)
OWNER_CALLERS = {"ratios", "ratio_lib"}

QUANTITIES = ["net_debt", "invested_capital", "wacc", "roic", "eva",
              "operating_cash_flow", "ebitda_margin", "net_margin",
              "current_ratio", "debt_to_equity", "roa", "roe"]

ROUNDERS = {"_r", "round"}


def scoped_bindings(fn):
    """name -> the expression assigned to it WITHIN ONE FUNCTION.

    Resolving a relayed local back to what produced it is necessary: the table
    first reported `invested_capital: 0 independent routes`, which is impossible
    for a quantity that is produced. The emitter is `_r(ic)` and
    `ic = ratio_lib.invested_capital(...)` twenty lines up, so a classifier that
    stops at the bare name calls the owner a relay. Same local-binding hop that
    made the plain-subscript counter a floor.

    SCOPED, because module-wide was worse than nothing. Taking the last
    assignment anywhere in the file resolved `w` in valuation/engines.py:299 to a
    grid interpolation and in financials/engines.py:755 to a working-capital
    difference — neither of which is a WACC. A binding resolved across a function
    boundary is not that function's binding, and reading one as if it were
    manufactures recomputes that do not exist.
    """
    out = {}
    for n in ast.walk(fn):
        if isinstance(n, ast.Assign) and len(n.targets) == 1 \
                and isinstance(n.targets[0], ast.Name):
            out[n.targets[0].id] = n.value
    return out


def classify(value: ast.AST, binds=None) -> str:
    """RECOMPUTE | OWNER | RELAY for a dict value expression."""
    # unwrap rounding: _r(x) and round(x, n) carry, they do not compute
    node = value
    while (isinstance(node, ast.Call) and node.args
           and ((isinstance(node.func, ast.Name) and node.func.id in ROUNDERS)
                or (isinstance(node.func, ast.Attribute) and node.func.attr in ROUNDERS))):
        node = node.args[0]

    # follow a relayed local back to what produced it, at most a few hops so a
    # cycle cannot spin
    seen = 0
    while isinstance(node, ast.Name) and binds and node.id in binds and seen < 6:
        node = binds[node.id]
        seen += 1
        while (isinstance(node, ast.Call) and node.args
               and ((isinstance(node.func, ast.Name) and node.func.id in ROUNDERS)
                    or (isinstance(node.func, ast.Attribute) and node.func.attr in ROUNDERS))):
            node = node.args[0]

    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            holder = (f.value.id if isinstance(f, ast.Attribute)
                      and isinstance(f.value, ast.Name) else None)
            if holder in OWNER_CALLERS:
                return "OWNER"
    if any(isinstance(n, ast.BinOp) for n in ast.walk(node)):
        return "RECOMPUTE"
    # ⭐ A LOOKUP IS NOT A COMPUTATION. `kpi.get("WACC") or dcf.get("wacc")` and
    # `det.get("wacc_used")` were counted as recomputes because `.get` is a Call.
    # They READ a value someone else produced — the definition of a relay — and
    # counting them inflated wacc from 2 independent routes to 5.
    if isinstance(node, (ast.Attribute, ast.Subscript, ast.BoolOp)):
        return "RELAY"
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute) and f.attr in ("get", "pop"):
                return "RELAY"
            return "RECOMPUTE"
    return "RELAY"


def survey():
    table = collections.defaultdict(list)   # quantity -> [(kind, path, line)]
    seen_sites = set()                      # one row per site, not per scope
    for root in ROOTS:
        for dp, _, fs in os.walk(root):
            if "__pycache__" in dp:
                continue
            for fn in fs:
                if not fn.endswith(".py"):
                    continue
                p = os.path.join(dp, fn)
                try:
                    tree = ast.parse(open(p, encoding="utf-8").read())
                except SyntaxError:
                    continue
                scopes = [f for f in ast.walk(tree)
                          if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))]
                for fn in scopes + [tree]:
                    binds = scoped_bindings(fn)
                    for n in ast.walk(fn):
                        if not isinstance(n, ast.Dict):
                            continue
                        for k, v in zip(n.keys, n.values):
                            if isinstance(k, ast.Constant) and k.value in QUANTITIES:
                                kind = ("OWNER" if any(o in p for o in OWNER_MODULES)
                                        else classify(v, binds))
                                key = (k.value, p, getattr(v, "lineno", 0))
                                if key not in seen_sites:
                                    seen_sites.add(key)
                                    table[k.value].append((kind, p, key[2]))
    return table


def main():
    table = survey()
    print("ROUTE TABLE — producers classified by what the value expression DOES\n")
    print(f"  {'quantity':<22}{'producers':>10}{'recompute':>11}{'owner':>7}{'relay':>7}"
          f"{'independent':>13}")
    print("  " + "-" * 70)
    comparison_set, single = [], []
    for q in QUANTITIES:
        rows = table.get(q, [])
        rec = {(p) for k, p, _ in rows if k == "RECOMPUTE"}
        own = {(p) for k, p, _ in rows if k == "OWNER"}
        rel = [r for r in rows if r[0] == "RELAY"]
        indep = len(rec) + (1 if own else 0)
        print(f"  {q:<22}{len(rows):>10}{len(rec):>11}{len(own):>7}{len(rel):>7}{indep:>13}")
        if indep > 1:
            comparison_set.append((q, sorted(rec)))
        elif indep == 1:
            single.append(q)
    print()
    print(f"  ⭐ COMPARISON SET (>1 independent route): {len(comparison_set)} of {len(QUANTITIES)}")
    for q, mods in comparison_set:
        print(f"       {q}")
        for m in mods:
            print(f"          {m}")
    print(f"\n  sole ownership already holds (1 independent route): {len(single)}")
    print(f"       {', '.join(single) if single else '—'}")
    zero = [q for q in QUANTITIES if not table.get(q)]
    if zero:
        print(f"\n  no producer found: {len(zero)}  {', '.join(zero)}")
        print("       ⭐ NOT 'unimplemented' — a search result. A quantity computed")
        print("       inside a report builder or the frontend is invisible here.")
    print()
    print("READ THE INDEPENDENT COLUMN AS AN UPPER BOUND")
    print("  A shared helper called from two modules counts TWICE. valuation")
    print("  emits `fin.wacc(company)` and financials emits `wacc(company)` —")
    print("  ONE implementation, two call sites, two 'independent routes'. Making")
    print("  the count exact needs callee resolution, which this does not do.")
    print("  The COMPARISON SET is unaffected: a quantity with two call sites into")
    print("  one implementation still cannot disagree with itself, so it belongs")
    print("  in the set only if a genuinely different implementation exists.")
    print()
    print("WHAT THIS CANNOT SEE")
    print("  · Producers that are not dict-literal keys — a value assigned then")
    print("    returned, or built in a report/PDF path, is missed.")
    print("  · The frontend entirely.")
    print("  · Whether two RECOMPUTE sites AGREE. That is the harness's job;")
    print("    this only decides how much work the harness has.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
