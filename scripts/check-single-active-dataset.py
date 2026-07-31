#!/usr/bin/env python3
"""A company may hold at most ONE active financial dataset.

⭐⭐ WHY. Measured 1 Aug: enterprise 20 (`showcase`, Meridian) held TWO —
ds 3 (payload `public`, `source=direct`) and ds 45 (payload `private`,
`source=upload`). ⭐ `_active_company_dataset` orders by `version DESC` so it
returned ds 45 and behaviour was correct — DETERMINISTIC BY ACCIDENT RATHER THAN
BY CONSTRUCTION, and the ownership ruling rested on it.

⭐⭐ THE MECHANISM WAS A SECOND WRITER THAT RE-ARMED ON EVERY BOOT. The showcase
seed set `is_active = True` directly, without clearing siblings, and
`seed_showcase()` runs from `core/db.py` at startup — so clearing the flag by hand
would have been undone by the next deploy.

⭐ THE CONTROL IS PLANTED IN MEMORY AND NEVER IN PRODUCTION SOURCE. The
guard-planting cleanup failure has occurred twice (sentinel.py,
benchmarks/router.py), each time leaving a live NameError when a timeout killed
the run mid-control. Nothing here writes a file.

Structural control by default. `--against-db` also checks every live company.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── ⭐⭐ THE KNOWN POSITIVE — in memory, no file touched ──────────────────────
class _Row:
    def __init__(self, i, eid, active, version):
        self.id, self.enterprise_id, self.is_active, self.version = i, eid, active, version


def violations(rows):
    """-> {company_id: [dataset_id, …]} for companies with >1 active row.

    ⭐ Pure over a row list, so the control and the live check run the SAME code.
    A guard whose control exercises a different function has tested nothing.
    """
    by = {}
    for r in rows:
        if getattr(r, "is_active", False) and r.enterprise_id is not None:
            by.setdefault(r.enterprise_id, []).append(r.id)
    return {c: ids for c, ids in by.items() if len(ids) > 1}


def _control():
    fails = []
    # ⭐ the exact shape found live: one seed row and one upload row, both active
    planted = [_Row(3, 20, True, 1), _Row(45, 20, True, 3), _Row(42, 20, False, 1)]
    if not violations(planted):
        fails.append("did NOT flag two active rows on one company — the guard "
                     "cannot detect the defect it exists for")
    if violations(planted).get(20) != [3, 45]:
        fails.append("flagged the wrong rows")
    # single active is fine
    if violations([_Row(45, 20, True, 3), _Row(42, 20, False, 1)]):
        fails.append("flagged a single active row (false positive)")
    # zero active is fine — a company awaiting its first upload
    if violations([_Row(42, 20, False, 1)]):
        fails.append("flagged a company with no active row (false positive)")
    # two active rows on DIFFERENT companies is fine
    if violations([_Row(1, 10, True, 1), _Row(2, 11, True, 1)]):
        fails.append("flagged two companies with one active row each")
    return fails


def main():
    fails = _control()
    if fails:
        print("✗ check-single-active-dataset: THE CONTROL FAILED")
        for f in fails:
            print("   ", f)
        return 1
    print("  ✓ control: flags two active rows on one company; accepts one, "
          "accepts none, accepts one-each across companies")

    if "--against-db" not in sys.argv:
        print("✓ check-single-active-dataset: structural control passed "
              "(pass --against-db to check live rows)")
        return 0

    url = os.environ.get("DATABASE_URL") or os.environ.get("DATABASE_PUBLIC_URL")
    if not url:
        print("✗ --against-db requested with no DATABASE_URL")
        return 1
    os.environ["DATABASE_URL"] = url
    from services.api.core.db import SessionLocal
    from services.api.modules.financials.models import FinancialDataset
    db = SessionLocal()
    rows = db.query(FinancialDataset).all()
    bad = violations(rows)
    # ⭐ COVERAGE PRINTED. "0 violations in 0 datasets" and "0 in 36" print the
    # same tick and mean opposite things.
    n_active = sum(1 for r in rows if r.is_active)
    print(f"  checked {len(rows)} datasets ({n_active} active) across "
          f"{len({r.enterprise_id for r in rows if r.enterprise_id})} companies")
    if not rows:
        print("✗ zero datasets examined — a broken selector, not a clean corpus")
        return 1
    if bad:
        print(f"✗ {len(bad)} company(ies) hold more than one active dataset:")
        for c, ids in sorted(bad.items()):
            print(f"   company {c}: datasets {ids}")
        return 1
    print("✓ every company holds at most one active dataset")
    return 0


if __name__ == "__main__":
    sys.exit(main())
