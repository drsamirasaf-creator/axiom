#!/usr/bin/env python3
"""Seed Meridian's owners and dates — §4z.4 ruling 1.

⭐⭐ THE CLAIM WAS FALSE ABOUT THE DATA, NOT THE CAPABILITY.
"Named accountability on every initiative" is on a prospect-facing page;
`Initiative.owner_name` is a real field, and 11 of 15 Meridian initiatives carry
none. Softening the sentence would understate the product — §4z.3's own recorded
failure mode — so the data is fixed instead.

⭐ AND DATES, SO THE GANTT DRAWS RATHER THAN DECLARES. 12 of 15 initiatives carry
no dated work today.

⭐⭐ BUT NOT ALL OF THEM. The absent path is real, it is now proven in the
browser, and a seed that dated everything would delete the demonstration. At
least one initiative stays deliberately undated — and it is the one the Schedule
harness asserts against, so filling it would break a passing proof.

⛔ MERIDIAN ONLY, by id AND name. Nothing deleted, nothing revoked, no boot hook.

    python3 scripts/seed-execution-coverage.py --plan
    python3 scripts/seed-execution-coverage.py --apply
"""
import argparse
import os
import sys
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

COMPANY_ID = 20
COMPANY_NAME = "Meridian Industries, Inc."

# ⭐ OWNERS BY DEPARTMENT — the department's own head, so the owner is somebody
# the org chart already names rather than a fabricated person.
OWNER_BY_DEPT = {
    12: "Eleanor Voss",
    13: "Marcus Chen",
    14: "Priya Nair",
    15: "Diego Alvarez",
    16: "Sofia Ianni",
    17: "Tomas Berg",
    18: "Grace Okafor",
}
# ⭐ For the two initiatives with no department at all, an explicit owner rather
# than a blank — an unowned initiative with no department is two absences, and
# ruling 1 is about the first.
FALLBACK_OWNER = "Eleanor Voss"

# ⭐⭐ DELIBERATELY LEFT UNDATED. "Platform v2 migration wave 1" is the initiative
# `verify-project-schedule.py` asserts the ABSENT path against. Dating it would
# turn a passing proof red and delete the state the proof exists to demonstrate.
LEAVE_UNDATED = {"A3", "A5"}

# ⭐ MILESTONES ARE THE UNIT, and each gets one target date. Deterministic — a
# reproducible seed cannot roll dice, or a re-run silently changes the demo.
BASE = date(2026, 9, 15)
STEP_DAYS = 21


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not (a.plan or a.apply):
        print("Refusing to guess. Pass --plan or --apply.")
        return 2

    from services.api.accounts import (Initiative, InitiativeMilestone,
                                       SessionLocal)
    from services.api.modules.enterprise_state.models import Enterprise

    db = SessionLocal()
    try:
        ent = db.get(Enterprise, COMPANY_ID)
        if ent is None or ent.name != COMPANY_NAME:
            print(f"  ✗ company {COMPANY_ID} is not {COMPANY_NAME!r} — refusing.")
            return 1
        print(f"SEED EXECUTION COVERAGE — company {COMPANY_ID}, "
              f"{'APPLY' if a.apply else 'PLAN'}\n")

        inis = (db.query(Initiative).filter_by(company_id=COMPANY_ID)
                  .order_by(Initiative.id).all())

        owners, dated, skipped = [], [], []
        for n, i in enumerate(inis):
            if not (i.owner_name or "").strip():
                who = OWNER_BY_DEPT.get(i.department_id) or FALLBACK_OWNER
                owners.append((i.ref_code, who))
            have = (db.query(InitiativeMilestone)
                      .filter_by(initiative_id=i.id)
                      .filter(InitiativeMilestone.target_date.isnot(None)).count())
            if have:
                continue
            if i.ref_code in LEAVE_UNDATED:
                skipped.append(i.ref_code)
                continue
            # one milestone, one date — the minimum that makes a Gantt draw
            dated.append((i.ref_code, i.id,
                          (BASE + timedelta(days=STEP_DAYS * n)).isoformat()))

        print(f"  initiatives {len(inis)}")
        print(f"  ⭐ owners to set   {len(owners):>3}")
        for ref, who in owners:
            print(f"       {ref:<5} -> {who}")
        print(f"  ⭐ milestones to add {len(dated):>3}  (one dated milestone each)")
        print(f"  ⛔ left deliberately undated: {sorted(skipped)}")
        print("     — the absent path is real and the Schedule proof asserts it")

        if a.plan:
            db.rollback()
            print("\n  PLAN ONLY — nothing was written.")
            return 0

        by_ref = {i.ref_code: i for i in inis}
        for ref, who in owners:
            by_ref[ref].owner_name = who
        made = 0
        for ref, iid, when in dated:
            db.add(InitiativeMilestone(
                initiative_id=iid,
                title="Phase 1 complete",
                target_date=when,
                status="in_progress",
                owner_name=by_ref[ref].owner_name,
                position=900))
            made += 1
        db.commit()
        print(f"\n  COMMITTED. owners set {len(owners)} · milestones added {made}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
