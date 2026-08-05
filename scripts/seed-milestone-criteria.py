#!/usr/bin/env python3
"""Seed forward-looking acceptance criteria — §4z.4 ruling 2.

⭐⭐ FORWARD-LOOKING ONLY, AND THAT IS THE RULING. Existing milestones are
grandfathered and CANNOT acquire a criterion: writing one now would describe what
already happened while reading like a standard set in advance, which is precisely
what the ruling forbids. All 21 of Meridian's milestones predate the rule and stay
bare.

⭐ SO THE MECHANISM IS DEMONSTRATED ON NEW, FUTURE-DATED MILESTONES, each created
WITH its criterion, and the four evidence states are all made reachable:

    evidenced — done, with an achievement recorded against the criterion
    asserted  — done, with NOTHING recorded  ⭐ THE FINDING
    open      — not yet due, criterion on record
    predates  — the 21 that already existed

⛔ Meridian only, by id AND name. Nothing deleted, nothing revoked.

    python3 scripts/seed-milestone-criteria.py --plan
    python3 scripts/seed-milestone-criteria.py --apply
"""
import argparse
import os
import sys
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

COMPANY_ID = 20
COMPANY_NAME = "Meridian Industries, Inc."

# (ref, title, criterion, achievement-or-None, status, days-from-base)
# ⭐ ONE OF THEM IS DELIBERATELY LEFT WITHOUT AN ACHIEVEMENT while marked done —
# that is the complete-by-assertion finding, and a seed that evidenced everything
# would demonstrate a tidy picture and hide the state the field exists to expose.
SEEDS = [
    ("A7", "Cutover rehearsal signed off",
     "Two full rehearsals complete with zero P1 defects outstanding.",
     "Both rehearsals run 12 and 19 Aug; no P1 outstanding at sign-off.",
     "done", -30),
    ("A6", "Close cycle under five days",
     "Month-end close completes within five working days for two consecutive months.",
     None, "done", -20),
    ("A8", "Second source qualified",
     "A qualified alternate supplier for each single-source component, audited.",
     None, "pending", 45),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not (a.plan or a.apply):
        print("Refusing to guess. Pass --plan or --apply.")
        return 2

    from services.api.accounts import (Initiative, InitiativeMilestone,
                                       SessionLocal, User,
                                       milestone_evidence_state)
    from services.api.modules.enterprise_state.models import Enterprise

    db = SessionLocal()
    try:
        ent = db.get(Enterprise, COMPANY_ID)
        if ent is None or ent.name != COMPANY_NAME:
            print(f"  ✗ company {COMPANY_ID} is not {COMPANY_NAME!r} — refusing.")
            return 1
        actor = db.query(User).filter_by(
            email="ops.admin@meridian-demo.example").first()
        if actor is None:
            print("  ✗ the Meridian seed admin does not exist.")
            return 1

        by_ref = {i.ref_code: i for i in
                  db.query(Initiative).filter_by(company_id=COMPANY_ID).all()}
        base = date(2026, 8, 5)
        print(f"SEED MILESTONE CRITERIA — company {COMPANY_ID}, "
              f"{'APPLY' if a.apply else 'PLAN'}\n")

        pre = (db.query(InitiativeMilestone)
                 .filter(InitiativeMilestone.initiative_id.in_(
                     [i.id for i in by_ref.values()]))
                 .filter(InitiativeMilestone.predates_criterion.is_(True)).count())
        print(f"  ⛔ existing milestones grandfathered: {pre} — they stay bare, "
              f"because a criterion written now would describe what happened")

        planned = []
        for ref, title, crit, ach, status, off in SEEDS:
            i = by_ref.get(ref)
            if i is None:
                print(f"  ⚠ {ref} not found — skipped")
                continue
            dup = (db.query(InitiativeMilestone)
                     .filter_by(initiative_id=i.id, title=title).first())
            if dup:
                print(f"  · {ref} {title!r} already present — skipped")
                continue
            st = milestone_evidence_state(status=status, criterion=crit,
                                          achievement=ach, predates=False)
            planned.append((i, title, crit, ach, status,
                            (base + timedelta(days=off)).isoformat(), st["state"]))

        for _i, title, _c, _a, _s, when, state in planned:
            print(f"  ⭐ {state:<10} {when}  {title}")
        if not planned:
            print("  nothing to add")

        if a.plan:
            db.rollback()
            print("\n  PLAN ONLY — nothing was written.")
            return 0

        for i, title, crit, ach, status, when, _st in planned:
            db.add(InitiativeMilestone(
                initiative_id=i.id, title=title, target_date=when,
                status=status, owner_name=i.owner_name, position=950,
                criterion=crit,
                achievement=ach,
                achieved_by=(actor.id if ach else None),
                achieved_at=(datetime.utcnow() if ach else None)))
        db.commit()
        print(f"\n  COMMITTED. {len(planned)} milestone(s) created WITH criteria.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
