#!/usr/bin/env python3
"""A revoked department must not reappear anywhere on the serving path.

## ⛔⭐⭐ WHY A GUARD AND NOT A CODE REVIEW

The state was authorized before it existed: `ax_departments` had **no
`revoked_at`**, and the nearest column — `flagged_absent` — was filtered by
**zero of 22** `query(Department)` call sites. A revoked department therefore
rendered exactly like a live one, and adding a column without the readers would
have made the work *look* done while changing nothing.

⭐ **One reader owns the exclusion**: `accounts.live_departments`. Every serving
path goes through it, so a 23rd call site cannot quietly reintroduce a revoked
department.

## ⛔⭐⭐ IT DERIVES ITS OWN DENOMINATOR — COVERAGE, NOT ACTIVITY

**A guard that enumerates must prove its enumeration complete.** This one does
not carry a list of 22 files to check; it **parses every module under
`services/api` and finds every `query(Department)` itself**. A new call site
appears in the denominator the moment it is written, which is exactly what a
hand-synced list cannot do (§III.4).

Each site must be one of:

- ⭐ routed through `live_departments`, or
- ⛔ **EXEMPT BY NAME WITH A REASON** — and every exemption must be HIT, or it
  is an allowlist entry that grew silently (the opposite ratchet, §4v.3).

⭐ CONTROLS ARE IN MEMORY. Nothing is written to disk.
"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "services", "api")
OWNER = "live_departments"

# ⛔ READERS THAT MUST SEE REVOKED DEPARTMENTS — each with the reason it is not a
# serving path. An exemption is a decision someone has to overturn, not a hole.
EXEMPT = {
    ("accounts.py", "live_departments"):
        "THE OWNER ITSELF. It is the one place the exclusion is expressed, so "
        "it must query the table directly — exempting it is not a hole, it is "
        "the definition.",
    ("accounts.py", "_resolve_department"):
        "HISTORY RESOLUTION. A response, objective or issue recorded under a "
        "department that has since been revoked must still RESOLVE to it — that "
        "is the whole point of revoking rather than deleting. Meridian's 2,418 "
        "'Sales & Marketing' answers depend on this exemption.",
    ("accounts.py", "_rekey_departments"):
        "MAINTENANCE. It mints stable dept_keys across the whole table; skipping "
        "a revoked row would leave it unkeyed and unresolvable later.",
    ("accounts.py", "_backfill_owner_persons"):
        "MAINTENANCE, as above — a backfill that skipped revoked rows would "
        "leave history half-resolved.",
    ("core/seed_meridian.py", None):
        "SEEDING. It rebuilds a demo company from scratch and must see every "
        "row it is replacing, revoked or not.",
    ("core/seed_assessment.py", None):
        "SEEDING, as above.",
    ("changeset_template.py", None):
        "TEMPLATE EXPORT. A workbook round-trip must carry the rows a company "
        "actually has, so a revoked department is not silently dropped from a "
        "file the client edits and re-uploads.",
    ("watch.py", None):
        "THE WATCH runs over stored history and must not lose a signal because "
        "the department was retired after the event.",
}


def sites():
    """Every `query(Department)` call, by AST. ⭐ The denominator, derived."""
    found = []
    for base, _d, fs in os.walk(SRC):
        for f in sorted(fs):
            if not f.endswith(".py"):
                continue
            p = os.path.join(base, f)
            rel = os.path.relpath(p, SRC)
            src = open(p, encoding="utf-8").read()
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            # map lineno -> enclosing function, so an exemption can name one
            fn_at = {}
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for i in range(node.lineno, (node.end_lineno or node.lineno) + 1):
                        fn_at[i] = node.name
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "query"):
                    continue
                for a in node.args:
                    nm = (a.id if isinstance(a, ast.Name)
                          else a.attr if isinstance(a, ast.Attribute) else None)
                    if nm == "Department":
                        found.append((rel, node.lineno, fn_at.get(node.lineno)))
    return found


def owner_uses():
    """Where the one owner is called — also derived."""
    out = []
    for base, _d, fs in os.walk(SRC):
        for f in sorted(fs):
            if not f.endswith(".py"):
                continue
            p = os.path.join(base, f)
            src = open(p, encoding="utf-8").read()
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Name)
                        and node.func.id == OWNER):
                    out.append((os.path.relpath(p, SRC), node.lineno))
    return out


def exemption_for(rel, fn):
    if (rel, fn) in EXEMPT:
        return (rel, fn)
    if (rel, None) in EXEMPT:
        return (rel, None)
    return None


def main():
    raw = sites()
    used = owner_uses()
    # ⭐ §III.4 — an empty corpus FAILS. "0 of 0 sites are covered" prints the
    # same tick as "22 of 22".
    if len(raw) < 5 or not used:
        print(f"  ✗ the recogniser found {len(raw)} call site(s) and "
              f"{len(used)} owner call(s) — it has drifted, and an empty "
              f"corpus is not a pass")
        return 1

    covered, exempt_hit, unfiltered = [], set(), []
    for rel, ln, fn in raw:
        ex = exemption_for(rel, fn)
        if ex:
            exempt_hit.add(ex)
            covered.append((rel, ln, "exempt"))
        else:
            unfiltered.append((rel, ln, fn))

    print(f"  DENOMINATOR (derived, by AST): {len(raw)} query(Department) call "
          f"site(s) across {len({r for r, _l, _f in raw})} module(s)")
    print(f"    routed through {OWNER}() : {len(used)} call(s)")
    print(f"    exempt by name           : {len(covered)} site(s), "
          f"{len(exempt_hit)}/{len(EXEMPT)} exemption(s) hit")
    print(f"    ⛔ neither               : {len(unfiltered)}")

    fails = []
    for rel, ln, fn in unfiltered:
        fails.append(f"{rel}:{ln} (in {fn or '<module>'}) queries Department "
                     f"directly — a revoked department reappears here. Route it "
                     f"through {OWNER}(), or exempt it BY NAME WITH A REASON.")
    # ⭐⭐ THE OPPOSITE RATCHET — an exemption nothing hits is an allowlist entry
    # that grew silently, and this is how two unhit entries survived in §4v.3.
    for key in EXEMPT:
        if key not in exempt_hit:
            fails.append(f"exemption {key} is never hit — remove it. An "
                         f"exemption that cannot fire is not a decision, it is "
                         f"an unexamined hole.")

    # ── controls, in memory, both directions ─────────────────────────────
    tree = ast.parse("x = db.query(Department).filter_by(company_id=1).all()\n")
    hits = [n for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == "query"]
    assert hits, "control: the recogniser cannot see a direct query"
    tree2 = ast.parse("x = live_departments(db, 1).all()\n")
    assert not [n for n in ast.walk(tree2)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "query"], \
        "control: the routed form was counted as a direct query"
    assert [n for n in ast.walk(tree2) if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name) and n.func.id == OWNER], \
        "control: the owner call is invisible to the recogniser"
    print("  ✓ controls: a direct query is seen, the routed form is not, and "
          "the owner call is recognised")

    for f in sorted(set(fails)):
        print(f"      ✗ {f}")
    if fails:
        print(f"\n  ✗ {len(set(fails))} site(s) can still surface a revoked "
              f"department.")
        return 1
    print(f"\n  ✓ every one of the {len(raw)} call sites is routed or exempt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
