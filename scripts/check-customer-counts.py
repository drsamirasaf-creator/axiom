#!/usr/bin/env python3
"""G13 guard — a count of customers must not silently include test accounts.

⭐⭐ WHY THIS EXISTS. The eleventh wrong entry was produced by exactly this: four
accounts read `plan=business, subscription_status=active` and were counted as
customers. All four are test-mode. ⭐ A COUNT THAT SILENTLY INCLUDES TEST ACCOUNTS
IS THE DEFECT, not a rounding error — the true number was ZERO.

THE RULE. Any aggregate over `User`/`Account` that filters or groups on `plan` or
`subscription_status` must EITHER

  * also constrain `subscription_livemode` / `livemode`, or
  * carry the marker  # COUNTS-TEST-ACCOUNTS: <reason>
    — an explicit statement that the number includes them.

⭐ THE MARKER IS DELIBERATELY AVAILABLE. Some counts legitimately want every
account (storage sizing, an ops dashboard). ⭐⭐ THE RULE IS NOT "EXCLUDE THEM", IT
IS "NEVER DO IT SILENTLY" — a guard that forbade the honest case would be routed
around, and a routed-around guard protects nothing.

⭐⭐ COVERAGE IS PRINTED, NOT IMPLIED (III.4). At the time of writing THERE ARE NO
AGGREGATE COUNT SURFACES AT ALL — the per-user entitlement checks are not counts.
"0 problems in 0 files" and "0 problems in 400 files" print the same tick, so this
guard states how many sites it examined and carries a KNOWN POSITIVE proving it
can still fire. ⭐ A GUARD WRITTEN BEFORE ITS SURFACE EXISTS HAS NEVER BEEN TESTED
BY REALITY, AND SAYING SO IS THE POINT.
"""
import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = ROOT / "services" / "api"

BILLING_FIELDS = {"plan", "subscription_status"}
LIVEMODE_FIELDS = {"subscription_livemode", "livemode"}
MARKER = "COUNTS-TEST-ACCOUNTS:"
AGGREGATES = {"count", "sum", "scalar"}


def _names(node):
    """Every identifier mentioned anywhere under `node`."""
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            out.add(n.value)
        elif isinstance(n, ast.keyword) and n.arg:
            out.add(n.arg)
    return out


def _is_aggregate_chain(node):
    """A call chain ending in .count()/.sum()/.scalar()."""
    cur = node
    while isinstance(cur, ast.Call):
        f = cur.func
        if isinstance(f, ast.Attribute) and f.attr in AGGREGATES:
            return True
        cur = f.value if isinstance(f, ast.Attribute) else None
        if not isinstance(cur, ast.Call):
            break
    return False


def scan_source(src, path="<mem>"):
    """-> (problems, sites_examined). Shared by the repo scan and the control."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return [], 0
    lines = src.splitlines()
    problems, sites = [], 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_aggregate_chain(node):
            continue
        used = _names(node)
        if not (used & BILLING_FIELDS):
            continue                       # not a billing aggregate
        sites += 1
        if used & LIVEMODE_FIELDS:
            continue                       # constrained — fine
        lo = max(0, node.lineno - 4)
        hi = min(len(lines), getattr(node, "end_lineno", node.lineno) + 1)
        if any(MARKER in ln for ln in lines[lo:hi]):
            continue                       # declared — fine
        problems.append((path, node.lineno,
                         "billing aggregate does not constrain livemode and "
                         "does not declare that it counts test accounts"))
    return problems, sites


# ── ⭐⭐ THE KNOWN POSITIVE ────────────────────────────────────────────────────
# A guard that has never fired has not been tested. This is the exact shape that
# produced the eleventh wrong entry.
_CONTROL_BAD = """
def customer_count(db):
    return db.query(User).filter(User.plan == "business",
                                 User.subscription_status == "active").count()
"""
_CONTROL_OK_FILTER = """
def customer_count(db):
    return db.query(User).filter(User.plan == "business",
                                 User.subscription_status == "active",
                                 User.subscription_livemode.is_(True)).count()
"""
_CONTROL_OK_MARKER = """
def all_accounts(db):
    # COUNTS-TEST-ACCOUNTS: ops storage sizing wants every row
    return db.query(User).filter(User.plan == "business").count()
"""


def _control():
    bad, n_bad = scan_source(_CONTROL_BAD, "<control-bad>")
    ok1, n1 = scan_source(_CONTROL_OK_FILTER, "<control-filter>")
    ok2, n2 = scan_source(_CONTROL_OK_MARKER, "<control-marker>")
    fails = []
    if not bad:
        fails.append("the guard did NOT flag an unconstrained customer count "
                     "— it cannot detect the defect it exists for")
    if not (n_bad and n1 and n2):
        fails.append("the control shapes were not recognised as billing "
                     "aggregates at all (saw %d/%d/%d)" % (n_bad, n1, n2))
    if ok1:
        fails.append("a livemode-constrained count was flagged (false positive)")
    if ok2:
        fails.append("a declared count was flagged (false positive)")
    return fails


def main():
    fails = _control()
    if fails:
        print("✗ check-customer-counts: THE CONTROL FAILED")
        for f in fails:
            print("   ", f)
        return 1
    print("  ✓ control: flags an unconstrained count, accepts a constrained "
          "one and a declared one")

    problems, sites, files = [], 0, 0
    for p in sorted(API.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        files += 1
        pr, n = scan_source(p.read_text(encoding="utf-8"),
                            str(p.relative_to(ROOT)))
        problems += pr
        sites += n

    # ⭐ COVERAGE FLOOR — the number examined is printed, always.
    print(f"  scanned {files} files; {sites} billing aggregate(s) examined")
    if sites == 0:
        print("  ⭐ NOTE: ZERO billing aggregates exist in the codebase today. "
              "This guard has never been exercised by a real site — it is armed "
              "for the surface that does not yet exist, and its control is the "
              "only evidence it works.")
    if problems:
        print(f"✗ {len(problems)} unconstrained billing aggregate(s):")
        for path, line, msg in problems:
            print(f"   {path}:{line}  {msg}")
        print("\n  Fix: constrain subscription_livemode, or add "
              f"'# {MARKER} <reason>' to state that test accounts are included.")
        return 1
    print("✓ check-customer-counts: no silent test-account counting")
    return 0


if __name__ == "__main__":
    sys.exit(main())
