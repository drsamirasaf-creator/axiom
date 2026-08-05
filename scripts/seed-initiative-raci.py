#!/usr/bin/env python3
"""Seed Meridian's RACI — §4z.4 ruling 4.

⭐⭐ COVERAGE, NOT A TIDY PICTURE (§7o). Three states are seeded deliberately:

    FULL      — all four roles, several Responsible, many Consulted/Informed
    BARE      — an Accountable and nothing else
    ⭐ NONE   — no one accountable at all, which is THE FINDING

A seed that gave every initiative a full grid would demonstrate a neat table and
hide the state the model exists to expose.

⛔ Meridian only, by id AND name. Nothing deleted, nothing revoked.

    python3 scripts/seed-initiative-raci.py --plan
    python3 scripts/seed-initiative-raci.py --apply
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

COMPANY_ID = 20
COMPANY_NAME = "Meridian Industries, Inc."

# ref -> {role: [parties]}. ⭐ Written out, never generated: a RACI assignment is
# a declaration, and a generated one asserts something nobody decided.
SEEDS = {
    # FULL — the demonstration
    "A7": {"accountable": ["Sofia Ianni"],
           "responsible": ["Platform Engineering Lead", "SRE Lead"],
           "consulted": ["Marcus Chen", "External Security Auditor"],
           "informed": ["Eleanor Voss", "Diego Alvarez", "Audit Committee"]},
    # ⭐ ACCOUNTABLE DIFFERS FROM THE OWNER — the two are distinct concepts and
    # the surface must show it rather than let a reader assume they agree.
    "A6": {"accountable": ["Eleanor Voss"],
           "responsible": ["Finance Systems Lead"],
           "consulted": ["Marcus Chen"],
           "informed": ["Audit Committee"]},
    # BARE — accountable and nothing else
    "A8": {"accountable": ["Tomas Berg"]},
}
# ⭐⭐ LEFT WITH NO RACI AT ALL, DELIBERATELY. "No one is accountable for this"
# is the finding a CXO needs, and it must be visible on the demo.
LEAVE_BARE = ("A1", "A3", "A9", "A11", "A13")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not (a.plan or a.apply):
        print("Refusing to guess. Pass --plan or --apply.")
        return 2

    from services.api.accounts import (Base, Initiative, InitiativeRaci,
                                       SessionLocal, User, engine, live_raci,
                                       raci_grid)
    from services.api.modules.enterprise_state.models import Enterprise

    # ⭐ The same call the app makes at boot, scoped to one table.
    Base.metadata.create_all(engine, tables=[InitiativeRaci.__table__])

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
        print(f"SEED RACI — company {COMPANY_ID}, "
              f"{'APPLY' if a.apply else 'PLAN'}\n")

        planned = []
        for ref, grid in SEEDS.items():
            i = by_ref.get(ref)
            if i is None:
                print(f"  ⚠ {ref} not found"); continue
            have = live_raci(db.query(InitiativeRaci)
                               .filter_by(company_id=COMPANY_ID,
                                          initiative_id=i.id).all())
            if have:
                print(f"  · {ref} already has {len(have)} assignment(s) — skipped")
                continue
            for role, parties in grid.items():
                for p in parties:
                    planned.append((ref, i, role, p))
            g = raci_grid([type("X", (), {"role": r, "party": p[0],
                                          "revoked_at": None})()
                           for r, p in grid.items() if p],
                          owner_name=i.owner_name)
            kind = "FULL" if len(grid) == 4 else "BARE"
            same = "owner IS accountable" if g["owner_matches_accountable"] \
                else f"⭐ owner {i.owner_name!r} ≠ accountable {grid['accountable'][0]!r}"
            print(f"  ⭐ {ref:<4} {kind:<5} {sum(len(v) for v in grid.values()):>2} "
                  f"assignment(s) · {same}")

        print(f"\n  ⛔ left with NO RACI, deliberately: {list(LEAVE_BARE)}")
        print("     — 'no one is accountable' is the finding, and it must be "
              "visible on the demo")
        print(f"\n  total assignments to write: {len(planned)}")

        if a.plan:
            db.rollback()
            print("\n  PLAN ONLY — nothing was written.")
            return 0

        for _ref, i, role, party in planned:
            db.add(InitiativeRaci(
                company_id=COMPANY_ID, initiative_id=i.id, role=role,
                party=party, department_id=i.department_id,
                declared_by=actor.id,
                declared_by_label=actor.name or actor.email,
                note="Seeded declaration."))
        db.commit()
        print(f"\n  COMMITTED. {len(planned)} assignment(s).")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
