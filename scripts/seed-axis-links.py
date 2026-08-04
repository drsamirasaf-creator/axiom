#!/usr/bin/env python3
"""Seed the axis→objective edge on Meridian, and leave axes deliberately unlinked.

⭐⭐ THE EDGE THAT CLOSES THE CYCLE. §7o's chain runs sentiment → initiative → KR
→ KPI → statement line and STOPS. Nothing reports back whether the intervention
moved the axis score. This seeds the return edge on real rows.

⭐⭐ AND IT LEAVES AXES UNLINKED ON PURPOSE. An axis nobody has connected to an
objective is the finding a CXO needs — "we score badly here and no objective
addresses it" is the single most useful thing this edge can surface. A seed that
linked all thirteen would demonstrate a tidy picture and hide the point.

⛔ DECLARED, NEVER INFERRED. Each pairing below is written down, not matched by
title similarity. `KeyResult.kpi_key` was designed to be matched by normalised
text and is null on all 82 rows.

⛔ Meridian only, by id AND name. Nothing deleted. No revocation seeded.

    python3 scripts/seed-axis-links.py --plan
    python3 scripts/seed-axis-links.py --apply
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

COMPANY_ID = 20
COMPANY_NAME = "Meridian Industries, Inc."

# ⭐ DECLARED PAIRINGS, BY HAND. Axis code -> the department whose objective
# should address it. The objective itself is chosen deterministically as that
# department's first unarchived objective, so the seed is reproducible.
#
# ⭐⭐ SEVEN OF THIRTEEN AXES ARE LINKED. The remaining six are the demonstration:
#   2.0  Products, Services & Sustainable Value
#   6.0  Customer Service & Experience
#   10.0 Assets & Enterprise Resources
#   11.0 Risk, Compliance & Resilience
#   12.0 Stakeholder & External Relationships
#   13.0 Transformation, Process & Business Capability Management
# Each renders as "No objective is declared to address this axis."
PAIRINGS = [
    ("1.0", "Executive Management"),            # Strategy, Purpose & Governance
    ("3.0", "Sales & Marketing"),               # Marketing, Sales & Customer Growth
    ("4.0", "Supply Chain and Logistics"),      # Supply Chain, Procurement & Logistics
    ("5.0", "Operations"),                      # Service Delivery & Operations
    ("7.0", "Human Resources"),                 # People, Culture & Leadership
    ("8.0", "Information Technology"),          # Technology, Data & Innovation
    ("9.0", "Finance and Accounting"),          # Finance & Enterprise Performance
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not (a.plan or a.apply):
        print("Refusing to guess. Pass --plan or --apply.")
        return 2

    from services.api.accounts import (AxisObjectiveLink, Department, Objective,
                                       SessionLocal, User)
    from services.api.modules.enterprise_state.models import Enterprise

    # ⭐ THE SAME MECHANISM THE APP USES AT BOOT, scoped to ONE table. New ax_
    # tables are created by Base.metadata.create_all (no Alembic for them), and
    # the app has not redeployed yet. This is that call, restricted so it cannot
    # touch anything else — not an alternative driver.
    from services.api.accounts import Base, engine
    Base.metadata.create_all(engine, tables=[AxisObjectiveLink.__table__])

    db = SessionLocal()
    try:
        ent = db.get(Enterprise, COMPANY_ID)
        if ent is None or ent.name != COMPANY_NAME:
            print(f"  ✗ company {COMPANY_ID} is not {COMPANY_NAME!r} — refusing.")
            return 1
        print(f"SEED AXIS→OBJECTIVE — company {COMPANY_ID}, "
              f"{'APPLY' if a.apply else 'PLAN'}\n")

        deps = {d.name: d.id for d in
                db.query(Department).filter_by(company_id=COMPANY_ID).all()}
        actor = db.query(User).filter_by(
            email="ops.admin@meridian-demo.example").first()
        if actor is None:
            print("  ✗ the Meridian seed admin does not exist — run "
                  "seed-department-authority.py first.")
            return 1

        planned, missing = [], []
        for code, dept_name in PAIRINGS:
            did = deps.get(dept_name)
            if did is None:
                missing.append(dept_name)
                continue
            obj = (db.query(Objective)
                     .filter_by(company_id=COMPANY_ID, department_id=did,
                                archived=False)
                     .order_by(Objective.id).first())
            if obj is None or not obj.obj_key:
                missing.append(f"{dept_name} (no objective)")
                continue
            planned.append((code, dept_name, obj.obj_key, obj.objective))

        for code, dept_name, key, title in planned:
            print(f"  ⭐ axis {code:<5} -> {dept_name:<28} {str(title)[:44]}")
        if missing:
            print(f"\n  ⚠ skipped, nothing to link to: {missing}")
        print(f"\n  linked {len(planned)} axes · ⭐ 6 left deliberately unlinked, "
              f"which is the finding")

        if a.plan:
            db.rollback()
            print("\n  PLAN ONLY — nothing was written.")
            return 0

        made = 0
        for code, _dn, key, _t in planned:
            if db.query(AxisObjectiveLink).filter_by(
                    company_id=COMPANY_ID, l1_code=code, obj_key=key,
                    revoked_at=None).first():
                continue
            db.add(AxisObjectiveLink(
                company_id=COMPANY_ID, l1_code=code, obj_key=key,
                source="in_app", declared_by=actor.id,
                declared_by_label=actor.name or actor.email,
                note="Seeded declaration — this objective addresses this axis."))
            made += 1
        db.commit()
        print(f"\n  COMMITTED. {made} new declaration(s).")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
