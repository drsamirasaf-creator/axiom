#!/usr/bin/env python3
"""Seed Meridian's issues and ratings — §4u.1's issues rulings.

⭐⭐ THE GROUPING IS DECLARED, NOT DERIVED, and the seed obeys that: each issue is
attached to REAL assessment comments by (cycle, participant_ref, item_id), the
same key the product's own attach endpoint uses. Nothing is clustered by text
similarity — that is the inference this codebase refuses, and KeyResult.kpi_key
is null on all 82 rows because of it.

⭐ THE FREQUENCY IS REAL. Meridian's comments genuinely repeat: five people say
strategy shifts every quarter, five say nobody can name their part in the vision,
four say tools are bought to fix process problems. Weight is a count of those
declarations, not a number chosen to look convincing.

⭐⭐ COVERAGE, NOT A TIDY PICTURE (§7o). Every state is reachable:
    open · addressed · accepted            — the three dispositions
    rated above the floor                  — an average publishes
    rated BELOW the floor                  — withheld, count still shown
    unrated                                — not the same as rated zero
    weight below the floor at department grain

⛔ Meridian only, by id AND name. Nothing deleted, nothing revoked.

    python3 scripts/seed-issues.py --plan
    python3 scripts/seed-issues.py --apply
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

COMPANY_ID = 20
COMPANY_NAME = "Meridian Industries, Inc."

# (title, the verbatim it groups, status, department_id, [stars], answers-ref)
SEEDS = [
    ("Strategy is re-set faster than teams can absorb it",
     "Strategy shifts every quarter — teams can't keep up.",
     "open", 12, [4, 5, 4, 5], None),
    ("The vision is known but personal contribution is not",
     "Everyone can recite the vision. Nobody can name their part in it.",
     "addressed", 12, [3, 4, 4], "A13"),
    ("Tools are bought to fix process problems",
     "We buy tools to fix process problems and then keep the process.",
     # ⭐ ACCEPTED — the company has decided to live with it, and it is STILL TRUE
     "accepted", 16, [5, 5], None),          # ⛔ 2 raters — BELOW the floor
    ("One customer record, four systems, four answers",
     "We have four systems that hold the same customer record differently.",
     # ⭐ UNRATED — not the same as rated zero
     "open", 16, [], None),
    ("Priorities are not communicated despite good scores",
     "We score well on paper but priorities aren't communicated.",
     # ⛔ weight 2 at department grain — below the floor, suppression demonstrates
     "open", 13, [4, 4, 5], None),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not (a.plan or a.apply):
        print("Refusing to guess. Pass --plan or --apply.")
        return 2

    from sqlalchemy import text as _sql
    from services.api.accounts import (Base, Initiative, Issue, IssueComment,
                                       ItemRating, SessionLocal, User, engine,
                                       rating_block)
    from services.api.issues import live_only, weight, weight_block
    from services.api.modules.enterprise_state.models import Enterprise

    Base.metadata.create_all(engine, tables=[ItemRating.__table__])

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
        inis = {i.ref_code: i for i in
                db.query(Initiative).filter_by(company_id=COMPANY_ID).all()}

        print(f"SEED ISSUES + RATINGS — company {COMPANY_ID}, "
              f"{'APPLY' if a.apply else 'PLAN'}\n")
        if db.query(Issue).filter_by(company_id=COMPANY_ID).count():
            print("  · issues already present — skipped")
            return 0

        rows = db.execute(_sql("""
            select r.cycle_id, r.participant_ref, r.item_id, btrim(r.comment) c
            from ax_assessment_responses r
            join ax_assessment_cycles k on k.id = r.cycle_id
            where k.company_id = :cid and r.comment is not null
              and btrim(r.comment) <> ''"""), {"cid": COMPANY_ID}).fetchall()
        by_text = {}
        for cyc, ref, item, c in rows:
            by_text.setdefault(c, []).append((cyc, ref, item))

        planned = []
        for title, verbatim, status, dept, stars, answers in SEEDS:
            hits = by_text.get(verbatim, [])
            rb = rating_block(stars)
            wb = weight_block(n=len(hits), department_scoped=True)
            planned.append((title, verbatim, status, dept, stars, answers, hits, rb, wb))
            print(f"  ⭐ {status:<10} weight {len(hits)} "
                  f"({'published' if wb['publishable'] else 'WITHHELD'}) · "
                  f"rating {rb['state']}"
                  f"{'' if rb['average'] is None else ' ' + str(rb['average'])}"
                  f" n={rb['n']}  {title[:44]}")
        print(f"\n  issues {len(planned)} · comment attachments "
              f"{sum(len(p[6]) for p in planned)} · ratings "
              f"{sum(len(p[4]) for p in planned)}")

        if a.plan:
            db.rollback()
            print("\n  PLAN ONLY — nothing was written.")
            return 0

        for title, verbatim, status, dept, stars, answers, hits, _rb, _wb in planned:
            iss = Issue(company_id=COMPANY_ID, title=title,
                        description=f"Raised from assessment feedback: “{verbatim}”",
                        status=status, department_id=dept,
                        initiative_id=(inis[answers].id if answers and answers in inis else None),
                        created_by=actor.id)
            db.add(iss); db.flush()
            for cyc, ref, item in hits:
                db.add(IssueComment(company_id=COMPANY_ID, issue_id=iss.id,
                                    cycle_id=cyc, participant_ref=ref,
                                    item_id=item, declared_by=actor.id))
            for n, st in enumerate(stars):
                db.add(ItemRating(company_id=COMPANY_ID, target_kind="issue",
                                  target_id=iss.id, rater_key=f"u:{actor.id}:{n}",
                                  stars=st))
        db.commit()
        print(f"\n  COMMITTED. {len(planned)} issue(s).")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
