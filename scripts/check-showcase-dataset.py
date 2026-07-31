#!/usr/bin/env python3
"""The showcase's ACTIVE dataset must be the one its published packs are frozen
against.

⭐⭐ WHY THE SINGLE-ACTIVE GUARD COULD NOT SEE THIS. `check-single-active-dataset`
asserts that at most ONE dataset is active. On 1 Aug that invariant was perfectly
satisfied — and the single active dataset was the WRONG ONE. Five demo surfaces
rendered empty, the valuation halved, and every gate stayed green.

⭐ A CONSTRAINT ON CARDINALITY CANNOT CATCH AN ERROR OF IDENTITY. This guard names
the identity: the packs are immutable and pin a `dataset_id`, so they are the
evidence of which dataset is the real one.

⭐ THE CONTROL IS PLANTED IN MEMORY AND NEVER IN PRODUCTION SOURCE — the
guard-planting cleanup failure has happened twice.

Structural control by default. `--against-db` also checks live showcase rows.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SHOWCASE_TENANT = "showcase"


def mismatches(companies):
    """`companies` = [{company_id, active_dataset_id, pack_dataset_ids:[…]}].

    -> the companies whose active dataset is not the one their packs pin.

    ⭐ PURE OVER A LIST, so the control and the live check run the SAME code. A
    guard whose control exercises a different function has tested nothing.
    """
    out = []
    for c in companies:
        pinned = set(c.get("pack_dataset_ids") or [])
        if not pinned:
            # ⭐ NO PACKS IS NOT A MISMATCH. A showcase company that has never
            # published has nothing to disagree with, and failing on it would
            # make the gate unpassable for a new demo.
            continue
        active = c.get("active_dataset_id")
        if active is None:
            out.append({**c, "why": "packs exist but no dataset is active"})
        elif active not in pinned:
            out.append({**c, "why": f"active ds {active} is not among the "
                                    f"dataset(s) the packs pin: {sorted(pinned)}"})
    return out


def _control():
    fails = []
    cases = [
        # the exact shape of the 1 Aug regression
        ([{"company_id": 20, "active_dataset_id": 3, "pack_dataset_ids": [45]}],
         True, "active is the seed row while packs pin the upload"),
        ([{"company_id": 20, "active_dataset_id": 45, "pack_dataset_ids": [45]}],
         False, "agreement"),
        ([{"company_id": 20, "active_dataset_id": None, "pack_dataset_ids": [45]}],
         True, "packs exist and nothing is active"),
        ([{"company_id": 21, "active_dataset_id": 9, "pack_dataset_ids": []}],
         False, "no packs — nothing to disagree with"),
    ]
    for rows, should_flag, label in cases:
        if bool(mismatches(rows)) != should_flag:
            fails.append(f"{label}: expected flag={should_flag}")
    return fails


def main():
    fails = _control()
    if fails:
        print("✗ check-showcase-dataset: THE CONTROL FAILED")
        for f in fails:
            print("   ", f)
        return 1
    print("  ✓ control: flags a seed row active while packs pin an upload; "
          "flags packs-with-nothing-active; accepts agreement and no-packs")

    if "--against-db" not in sys.argv:
        print("✓ check-showcase-dataset: structural control passed "
              "(pass --against-db to check live rows)")
        return 0

    url = os.environ.get("DATABASE_URL") or os.environ.get("DATABASE_PUBLIC_URL")
    if not url:
        print("✗ --against-db requested with no DATABASE_URL")
        return 1
    os.environ["DATABASE_URL"] = url
    from services.api.core.db import SessionLocal, init_db
    init_db()
    from services.api import pack as P
    from services.api.accounts import _active_company_dataset
    from services.api.modules.enterprise_state.models import Enterprise
    db = SessionLocal()

    ents = db.query(Enterprise).filter_by(tenant=SHOWCASE_TENANT).all()
    rows = []
    for e in ents:
        ds = _active_company_dataset(db, e.id)
        pinned = set()
        for pk in db.query(P.Pack).filter(P.Pack.cid == e.id).all():
            try:
                blk = ((P.frozen_inputs(db, pk).get("classes") or {})
                       .get("active_financial_dataset") or {})
                d = blk.get("dataset_id") or blk.get("id")
                if d:
                    pinned.add(d)
            except Exception:
                pass
        rows.append({"company_id": e.id, "name": e.name,
                     "active_dataset_id": getattr(ds, "id", None),
                     "pack_dataset_ids": sorted(pinned)})

    # ⭐ COVERAGE PRINTED. "0 mismatches in 0 companies" and "0 in 3" print the
    # same tick and mean opposite things.
    print(f"  checked {len(rows)} showcase company(ies)")
    for r in rows:
        print(f"    company {r['company_id']} ({r['name']}): active="
              f"{r['active_dataset_id']} packs pin {r['pack_dataset_ids'] or 'none'}")
    if not rows:
        print("✗ zero showcase companies examined — a broken selector, not a "
              "clean corpus")
        return 1
    bad = mismatches(rows)
    if bad:
        print(f"✗ {len(bad)} showcase company(ies) resolve the wrong dataset:")
        for b in bad:
            print(f"   company {b['company_id']}: {b['why']}")
        return 1
    print("✓ every showcase company resolves the dataset its packs are frozen against")
    return 0


if __name__ == "__main__":
    sys.exit(main())
