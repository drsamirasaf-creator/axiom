#!/usr/bin/env python3
"""Seed Meridian's link layers so a strategy map has edges to lay out.

⭐⭐ WHY THE CHAIN REGRESSED, MEASURED. CORE records §7o's causal chain COMPLETE
AT FIVE HOPS (31 Jul, `9055f0d`). Today hops 3, 4 and 5 are ALL ZERO on Meridian:
no KR→initiative link, no KR carrying a `kpi_key`, no initiative→statement-line
link anywhere in the database.

⛔ THE CHAIN DID NOT BREAK — IT WAS OVERWRITTEN. `core/seed_meridian.reseed()`
DELETES departments, objectives, KRs, KPIs and initiatives and rewrites its own
nine-department demo. Later lanes re-seeded Meridian with a richer seven-
department, four-period structure that never carried the links. ⭐ RUNNING
`reseed()` TO "RESTORE" THE CHAIN WOULD DESTROY FIVE LANES OF WORK — the
dimensional seed, the 41 KPI→objective links, capacity, avoidability, segments
and the department-authority grants. This script adds the missing links to the
CURRENT structure instead.

⭐ WRITE PATHS, NOT INSERTS, WHERE ONE EXISTS (the department-authority seed
established this):
  · KR→initiative   -> `_set_initiative_links()`  — the production writer
  · initiative→line -> `initiative_lines.declare()` — B10's writer
  · ⛔ KR→KPI       -> NO WRITE PATH EXISTS. `KeyResult.kpi_key` is assigned in
    exactly ONE place in the whole codebase — `core/seed_meridian.py:279` — and
    NOWHERE in the product. `PATCH /key-results/{id}` does not accept it, and the
    OKR reconciliation only PROPAGATES an existing value, so a null stays null
    forever. The field is set directly here and the missing writer is REPORTED,
    not quietly invented.

⛔ SCOPED TO MERIDIAN BY ID **AND** NAME. Nothing is backfilled elsewhere.
⛔ NOTHING IS DELETED and no revocation is written — `revoked_at` stays NULL.
⛔ NO BOOT HOOK. This is an explicit callable, idempotent, and re-running it is
a no-op.

    python3 scripts/seed-link-layers.py --plan
    python3 scripts/seed-link-layers.py --apply
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

COMPANY_ID = 20
COMPANY_NAME = "Meridian Industries, Inc."

# ⭐⭐ COVERAGE, NOT NARRATIVE (§7o). The map must show CONNECTED **and**
# UNCONNECTED at every layer, so a fraction of each layer is deliberately left
# unlinked. A seed that connects everything demonstrates a tidy picture and
# proves nothing about how the surface renders a gap — and the gap is exactly
# what a CXO needs to see.
#
# ⭐ DETERMINISTIC BY INDEX, NEVER RANDOM. A reproducible seed cannot roll dice:
# the same rows must be chosen on every run, or a re-seed silently changes the
# demo and no test can pin it.
KR_KPI_SKIP_EVERY = 3          # every 3rd KR is left with no measuring KPI
KR_INI_SKIP_EVERY = 2          # every 2nd KR is left unresourced

# ⭐ TWO INITIATIVES ON ONE LINE, SUMMING TO 0.60 — the shares CORE recorded for
# the five-hop chain. A single-linked line cannot distinguish "split correctly"
# from "took everything", and a declared total of 1.00 would make the residual
# zero, which is the fudge §7o's own entry warns about. 40% stays undeclared.
LINE_DECLARATIONS = [("revenue", 0.35), ("revenue", 0.25)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not (a.plan or a.apply):
        print("Refusing to guess. Pass --plan or --apply.")
        return 2

    from services.api.accounts import (Department, Initiative, KeyResult,
                                       KpiPlan, KrInitiativeLink, Objective,
                                       SessionLocal, _set_initiative_links)
    from services.api.initiative_lines import InitiativeLineLink, declare
    from services.api.modules.enterprise_state.models import Enterprise

    db = SessionLocal()
    try:
        ent = db.get(Enterprise, COMPANY_ID)
        if ent is None or ent.name != COMPANY_NAME:
            print(f"  ✗ company {COMPANY_ID} is not {COMPANY_NAME!r} — refusing.")
            return 1
        mode = "APPLY" if a.apply else "PLAN"
        print(f"SEED LINK LAYERS — company {COMPANY_ID}, {mode}\n")

        deps = {d.id: d.name for d in
                db.query(Department).filter_by(company_id=COMPANY_ID)
                  .order_by(Department.id).all()}
        objs = (db.query(Objective)
                  .filter_by(company_id=COMPANY_ID, archived=False)
                  .order_by(Objective.id).all())
        obj_by_ref = {o.objective_id: o for o in objs}
        krs = (db.query(KeyResult)
                 .filter_by(company_id=COMPANY_ID, archived=False)
                 .order_by(KeyResult.id).all())
        kpis = (db.query(KpiPlan)
                  .filter_by(company_id=COMPANY_ID, archived=False)
                  .order_by(KpiPlan.id).all())
        inis = (db.query(Initiative).filter_by(company_id=COMPANY_ID)
                  .order_by(Initiative.id).all())

        kpis_by_dept, inis_by_dept = {}, {}
        for k in kpis:
            kpis_by_dept.setdefault(k.department_id, []).append(k)
        for i in inis:
            inis_by_dept.setdefault(i.department_id, []).append(i)

        planned_kpi, planned_ini, skipped_kpi, skipped_ini = [], [], [], []
        for n, kr in enumerate(krs):
            parent = obj_by_ref.get(kr.objective_id)
            did = getattr(parent, "department_id", None)
            pool_k = kpis_by_dept.get(did) or []
            pool_i = inis_by_dept.get(did) or []
            # ── layer 1 · KR → the KPI that measures it ──────────────────
            if not pool_k or n % KR_KPI_SKIP_EVERY == 0:
                skipped_kpi.append(kr)
            elif not kr.kpi_key:
                planned_kpi.append((kr, pool_k[n % len(pool_k)]))
            # ── layer 2 · KR → the initiative delivering it ──────────────
            if not pool_i or n % KR_INI_SKIP_EVERY == 0:
                skipped_ini.append(kr)
            else:
                planned_ini.append((kr, pool_i[n % len(pool_i)]))

        # ── layer 3 · B10, the fifth hop ────────────────────────────────
        line_targets = [i for i in inis if i.department_id is not None][:2]
        have_lines = db.query(InitiativeLineLink).filter_by(
            company_id=COMPANY_ID).count()

        # ── the coverage state §7o requires and Meridian lacks ──────────
        bare_needed = not [o for o in objs
                           if not any(k.objective_id == o.objective_id for k in krs)]

        print(f"  departments {len(deps)} · objectives {len(objs)} · "
              f"key results {len(krs)} · KPIs {len(kpis)} · initiatives {len(inis)}\n")
        print(f"  KR → KPI          link {len(planned_kpi):>3}   "
              f"⭐ leave unmeasured {len(skipped_kpi):>3}")
        print(f"  KR → initiative   link {len(planned_ini):>3}   "
              f"⭐ leave unresourced {len(skipped_ini):>3}")
        print(f"  initiative → line link {len(LINE_DECLARATIONS) if not have_lines else 0:>3}   "
              f"(existing {have_lines})")
        print(f"  bare objective needed: {bare_needed}")

        if a.plan:
            db.rollback()
            print("\n  PLAN ONLY — nothing was written.")
            return 0

        # ⭐ THE SEED'S OWN ACTOR. Every link carries who declared it; a link with
        # no declarer is "an inference wearing a declaration's clothes" (B10).
        from services.api.accounts import User
        actor = db.query(User).filter_by(
            email="ops.admin@meridian-demo.example").first()
        if actor is None:
            print("  ✗ the Meridian seed admin does not exist — run "
                  "seed-department-authority.py first.")
            return 1

        for kr, kpi in planned_kpi:
            # ⛔ DIRECT FIELD WRITE, AND IT IS THE ONLY ONE. No product path sets
            # KeyResult.kpi_key; see the module docstring. A writer is OWED.
            kr.kpi_key = kpi.kpi_key
        by_ini = {}
        for kr, ini in planned_ini:
            by_ini.setdefault(ini.id, []).append(kr.kr_key)
        for iid, kr_keys in by_ini.items():
            _set_initiative_links(db, COMPANY_ID, iid, actor.id,
                                  objective_keys=[], kr_keys=kr_keys,
                                  kpi_keys=[], source="in_app")
        if not have_lines:
            for (line, w), ini in zip(LINE_DECLARATIONS, line_targets):
                declare(db, COMPANY_ID, ini.id, line, weight=w, user=actor,
                        note="§7o hop 5 — declared share, deliberately under 1.0")
        if bare_needed:
            ds_id = objs[0].dataset_id if objs else None
            db.add(Objective(
                company_id=COMPANY_ID, dataset_id=ds_id,
                row_index=9000, objective="Establish a board-level ESG position",
                objective_id="O90", obj_key="seed-bare-objective-esg",
                department_id=objs[0].department_id if objs else None,
                priority="Low", horizon="Long", status="Amber",
                source="in_app", created_by_user_id=actor.id,
                created_by_name=actor.name, archived=False))
        db.commit()
        print(f"\n  COMMITTED. KR→KPI {len(planned_kpi)} · "
              f"KR→initiative {len(planned_ini)} · "
              f"lines {0 if have_lines else len(LINE_DECLARATIONS)}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
