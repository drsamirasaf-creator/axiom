#!/usr/bin/env python3
"""STRUCTURAL GUARD — no HTTP path registered twice.

⭐ WHY THIS EXISTS. `/companies/{company_id}/roster` was declared twice in
accounts.py: once returning invitations + assessment participants, once
returning Membership JOIN User. FastAPI resolves to the FIRST registration, so
the membership view was written, correct, and NEVER SERVED. An administrator's
"who has access" screen answered a different question, on a real customer's
tenant, silently.

⭐ THE STRICTER GATE NEVER APPLIED EITHER. The shadowed route required
`require_company_admin`; the winner used the looser `_roster_access`. A shadowed
route takes its access control with it.

This class is mechanically detectable, which is why it is a CI guard rather than
a review habit: nothing in either function is wrong, and reading either one in
isolation shows no defect. Only the PAIR is the defect.

Detection is on (method, resolved-path). Router prefixes are tracked by
following reassignments of the decorated variable in file order.
"""
import re, sys, pathlib, collections

# ⭐ A COVERAGE FLOOR. A guard that finds NOTHING TO CHECK must be red, never
# green: "0 shadowed routes in 0 registrations" and "0 in 338" print the same
# tick and mean opposite things.
#
# The floor is the observed count when written. It is not a target — it is the
# assertion that the COLLECTOR still collects.
MIN_REGISTRATIONS = 300


ROOT = pathlib.Path(__file__).resolve().parent.parent / "services" / "api"
DEC = re.compile(r'^\s*@(\w+)\.(get|post|put|patch|delete)\(\s*([\'"])(.*?)\3')
NEWROUTER = re.compile(r'^\s*(\w+)\s*=\s*APIRouter\((.*)$')
PREFIX = re.compile(r'prefix\s*=\s*[\'"]([^\'"]*)[\'"]')

# ── EXPLICIT, DATED EXEMPTIONS ───────────────────────────────────────────────
# Visible exceptions, not a suppressed guard. Each entry names WHY it is exempt
# and what must happen for it to go. A guard that fails on known-open items
# teaches everyone to skip it; a guard that names them keeps failing on NEW ones.
ALLOWLIST = {
    ("POST", "/companies/{company_id}/kpis"): (
        "2026-07-28 — accounts.py:4032 (KpiPlan) serves; planning.py:234 "
        "(KpiDefinition) is shadowed. Both gate on require_company_admin, so no "
        "access-control divergence. PENDING THE KpiDefinition LANE: whether that "
        "model is superseded (routes and model should go) or orphaned (a feature "
        "that silently does not exist) is unanswered, and no route may change "
        "until it is."),
    ("DELETE", "/companies/{company_id}/kpis/{kpi_id}"): (
        "2026-07-28 — accounts.py:4079 (KpiPlan) serves; planning.py:268 "
        "(KpiDefinition) is shadowed. Same pairing, same pending lane as the POST "
        "above."),
}

seen = collections.defaultdict(list)
for f in sorted(ROOT.rglob("*.py")):
    prefixes = {}                     # var name -> prefix currently bound
    for n, line in enumerate(f.read_text(errors="ignore").splitlines(), 1):
        m = NEWROUTER.match(line)
        if m:
            var, rest = m.group(1), m.group(2)
            p = PREFIX.search(rest)
            prefixes[var] = p.group(1) if p else ""
            continue
        d = DEC.match(line)
        if d:
            var, method, path = d.group(1), d.group(2).upper(), d.group(4)
            full = prefixes.get(var, "") + path
            seen[(method, full)].append(f"{f.name}:{n}")

dupes = {k: v for k, v in seen.items() if len(v) > 1}
exempt = {k: v for k, v in dupes.items() if k in ALLOWLIST}
dupes = {k: v for k, v in dupes.items() if k not in ALLOWLIST}
print(f"  scanned {len(seen)} unique (method, path) registrations")
if len(seen) < MIN_REGISTRATIONS:
    print(f"\nFAIL — scanned only {len(seen)} registration(s), floor is "
          f"{MIN_REGISTRATIONS}. The route collector stopped collecting, so "
          f"'no shadowing' means 'no routes seen'.")
    raise SystemExit(1)
for (method, path), locs in sorted(exempt.items()):
    print(f"  ALLOWED (dated, pending a named lane): {method} {path}")
    print(f"      {ALLOWLIST[(method, path)]}")
    for i, l in enumerate(locs):
        print(f"      {'SERVED  ' if i == 0 else 'SHADOWED'} {l}")
if dupes:
    print(f"✗ route-shadowing check FAILED: {len(dupes)} path(s) registered more than once")
    for (method, path), locs in sorted(dupes.items()):
        print(f"    {method:6} {path}")
        for i, l in enumerate(locs):
            print(f"           {'SERVED  ' if i == 0 else 'SHADOWED'} {l}")
    sys.exit(1)
print("✓ route-shadowing: no path registered twice")
