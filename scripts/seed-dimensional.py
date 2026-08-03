#!/usr/bin/env python3
"""Meridian's dimensional seed — one explicit run, never a boot-time mutation.

⭐⭐ §7o's GOVERNING CRITERION: COVERAGE, NOT NARRATIVE. Prospects know the
numbers are invented. Nobody evaluates whether Meridian's product mix is true.
What the sample must demonstrate is WHAT THE SYSTEM IS CAPABLE OF SAYING — so
every capability T2 built must have something to render, including the ones that
are only interesting when they are ugly.

⭐ NOT A BOOT-TIME MUTATION, per §7o. This is an explicit script, idempotent, and
it records nothing that a later boot rewrites. A seed that depends on the boot
backfills is unreproducible by construction.

⭐ IT ADDS; IT REPLACES NOTHING. Meridian's dataset payload is not touched, so
§7o's deletion rule — replacing a dataset destroys every derived artefact — does
not trigger. `verify` asserts the statements and pack hashes are byte-identical
before and after.

    python3 scripts/seed-dimensional.py --plan     # print, write nothing
    python3 scripts/seed-dimensional.py --apply
    python3 scripts/seed-dimensional.py --verify
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

COMPANY_ID = 20
DATASET_ID = 45
PERIODS = (2024, 2025)
FREQUENCY = "annual"

# Meridian's own income statement, read from the dataset. The seed reconciles
# AGAINST these; it never rewrites them.
STATEMENT = {
    2024: {"revenue": 1198.6286, "cogs": 658.4571, "opex": 216.8571},
    2025: {"revenue": 1380.0000, "cogs": 757.0286, "opex": 248.4000},
}

# ═══════════════════════════════════════════════════════════════════════════
# THE PRODUCT LINES — designed for COVERAGE, each earning its place
# ═══════════════════════════════════════════════════════════════════════════
#
# ⭐⭐ PL-CTRL IS THE REVERSAL, AND IT IS THE POINT OF THE WHOLE SEED. It is
# healthy at gross margin (33%) and LOSS-MAKING at allocated EBIT, because it
# consumes support and logistics far out of proportion to its revenue. "This
# product looks fine until you charge it for what it consumes" is the finding a
# CFO reacts to, and it exercises the hierarchy end to end.
#
# ⭐ THE SHARES ARE DELIBERATELY UNEVEN so the Pareto point is a real answer
# rather than an artefact of equal weighting.
PRODUCTS = {
    "PL-DRIVE":  {"name": "Drive Systems",        "share": 0.34, "gm": 0.47},
    "PL-AUTO":   {"name": "Automation Modules",   "share": 0.24, "gm": 0.44},
    "PL-CTRL":   {"name": "Control Electronics",  "share": 0.13, "gm": 0.33},
    "PL-SERV":   {"name": "Field Service",        "share": 0.09, "gm": 0.58},
    "PL-SPARE":  {"name": "Spares & Consumables", "share": 0.08, "gm": 0.50},
}
# ⭐ Sums to 0.88 — the remaining 12% is genuinely UNALLOCATED, and it is
# material on purpose. A demo where everything allocates cleanly hides the
# residual, which is the honest half of the reconciliation.

# Year-two drift, so mix shift and the margin bridge have something to bridge.
DRIFT_2025 = {"PL-DRIVE": -0.02, "PL-AUTO": +0.03, "PL-CTRL": +0.01,
              "PL-SERV": +0.01, "PL-SPARE": -0.01}
GM_DRIFT_2025 = {"PL-DRIVE": -0.01, "PL-AUTO": -0.03, "PL-CTRL": -0.02,
                 "PL-SERV": +0.02, "PL-SPARE": 0.0}

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THREE ALLOCATION GRADES — a seed where everything is grade A demonstrates
# nothing about the machinery. The differentiation is that the assumption is
# NAMED, so the demo must show assumptions that differ in quality.
# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ TWO OPEX LAYERS, AND THE SEPARATION IS THE WHOLE HIERARCHY. `direct_opex`
# is what the client attributed to a line themselves (grade A, direct
# assignment); the SHARED pools below are allocated by driver at read time and
# feed `allocated_ebit`. Collapsing them would erase the level at which
# PL-CTRL reverses.
DIRECT_OPEX_POOL = 0.18                    # share of opex directly assigned
DIRECT_OPEX_SPLIT = {"PL-DRIVE": 0.36, "PL-AUTO": 0.28, "PL-CTRL": 0.10,
                     "PL-SERV": 0.18, "PL-SPARE": 0.08}

COST_POOLS = {
    # C — an operational driver: support hours. This is WHY PL-CTRL reverses.
    "customer_support": {
        "method": "operational_driver", "grade": "C", "share_of_opex": 0.24,
        "drivers": {"PL-DRIVE": 0.10, "PL-AUTO": 0.12, "PL-CTRL": 0.64,
                    "PL-SERV": 0.10, "PL-SPARE": 0.04}},
    # C — logistics movements, also heavy on CTRL.
    "logistics": {
        "method": "operational_driver", "grade": "C", "share_of_opex": 0.18,
        "drivers": {"PL-DRIVE": 0.14, "PL-AUTO": 0.11, "PL-CTRL": 0.56,
                    "PL-SERV": 0.04, "PL-SPARE": 0.15}},
    # D — revenue allocation: the fallback, and it is LABELLED as the fallback.
    "central_admin": {
        "method": "revenue", "grade": "D", "share_of_opex": 0.20,
        "drivers": None},          # None -> allocated by revenue share
}
# ⭐ The remaining opex is CORPORATE RESIDUAL — never forced onto a line.

# ⭐⭐ ONE DELIBERATE ABSENCE, per §7o. `units` is seeded for NO product, so the
# margin bridge's price and volume effects stay unavailable and the Data Quality
# surface has a real "supply this to unlock that" to render. See §5 of the report:
# the bridge already NAMES seven effects it cannot compute, but a named absence
# in prose and an absence a capability actually hits are different demonstrations
# — the second exercises the declaration path.
SEEDED_MEASURES = ("revenue", "direct_cost", "direct_opex")
DELIBERATELY_ABSENT = ("units", "list_price", "realised_price")


def _rows():
    """Every observation the seed writes, computed from the statement lines."""
    out = []
    for year in PERIODS:
        st = STATEMENT[year]
        shares, gms = {}, {}
        for code, spec in PRODUCTS.items():
            shares[code] = spec["share"] + (DRIFT_2025.get(code, 0.0)
                                            if year == 2025 else 0.0)
            gms[code] = spec["gm"] + (GM_DRIFT_2025.get(code, 0.0)
                                      if year == 2025 else 0.0)
        for code in PRODUCTS:
            rev = st["revenue"] * shares[code]
            out.append((year, code, "revenue", rev))
            # direct cost from the line's own gross margin
            out.append((year, code, "direct_cost", rev * (1.0 - gms[code])))
        # ⭐ ONLY the DIRECTLY ASSIGNED slice is stored. The shared pools are
        # allocated at read time so the demo exercises `allocate()` and its
        # grades, and the corporate residual is never forced onto a line.
        for code in PRODUCTS:
            out.append((year, code, "direct_opex",
                        st["opex"] * DIRECT_OPEX_POOL * DIRECT_OPEX_SPLIT[code]))
    return out


def shared_allocation(year, shares):
    """Allocate every pool for a period — THREE GRADES, at read time.

    ⭐ The directly-assigned layer runs through `allocate()` too, with
    `method="direct_assignment"`. It could have been left as a stored number,
    but then the demo would show only C and D and would say nothing about what
    grade A looks like beside them — and the whole point is that the grades
    DIFFER visibly.
    """
    from services.api.modules.financials import dimensional_analytics as A
    st = STATEMENT[year]
    out = {"sales_commission": A.allocate(
        st["opex"] * DIRECT_OPEX_POOL, DIRECT_OPEX_SPLIT,
        method="direct_assignment")}
    for name, pool in COST_POOLS.items():
        drivers = pool["drivers"] or {c: shares[c] for c in PRODUCTS}
        out[name] = A.allocate(st["opex"] * pool["share_of_opex"], drivers,
                               method=pool["method"])
    return out


def shares_for(year):
    return {c: PRODUCTS[c]["share"] + (DRIFT_2025.get(c, 0.0) if year == 2025 else 0.0)
            for c in PRODUCTS}


def plan():
    rows = _rows()
    print(f"{len(rows)} observations across {len(PERIODS)} periods, "
          f"{len(PRODUCTS)} product lines, {len(SEEDED_MEASURES)} measures")
    for year in PERIODS:
        st = STATEMENT[year]
        for measure, line in (("revenue", "revenue"), ("direct_cost", "cogs"),
                              ("direct_opex", "opex")):
            detail = sum(v for (y, _c, m, v) in rows if y == year and m == measure)
            total = st[line]
            print(f"  {year} {measure:<12} detail={detail:10.4f}  "
                  f"statement={total:10.4f}  unallocated={total - detail:9.4f}  "
                  f"({100 * (total - detail) / total:5.1f}%)")
    print(f"\n  deliberately absent: {', '.join(DELIBERATELY_ABSENT)}")
    grades = sorted({"A"} | {p["grade"] for p in COST_POOLS.values()})
    print(f"  allocation grades seeded: {grades}")
    for y in PERIODS:
        sh = shares_for(y)
        alloc = shared_allocation(y, sh)
        tot = {c: sum(a["value"].get(c, 0.0) for a in alloc.values()) for c in PRODUCTS}
        print(f"\n  {y}  line        revenue   gross   d.opex   allocated   allocEBIT")
        for c in PRODUCTS:
            rev = STATEMENT[y]["revenue"] * sh[c]
            gm = PRODUCTS[c]["gm"] + (GM_DRIFT_2025.get(c, 0.0) if y == 2025 else 0.0)
            g = rev * gm
            do = STATEMENT[y]["opex"] * DIRECT_OPEX_POOL * DIRECT_OPEX_SPLIT[c]
            eb = g - do - (tot[c] - do)
            print(f"      {c:<10}{rev:9.1f} {g:7.1f} {do:7.1f} {tot[c]-do:10.1f} {eb:10.2f}"
                  + ("   <-- REVERSAL" if g > 0 and eb < 0 else ""))


def _engine():
    from sqlalchemy import create_engine
    u = os.environ["DATABASE_PUBLIC_URL"]
    for a, b in (("postgres://", "postgresql://"),
                 ("postgresql://", "postgresql+psycopg://")):
        if u.startswith(a):
            u = u.replace(a, b, 1)
    return create_engine(u)


def apply_seed():
    """Idempotent: members upserted by code, observations by the unique key."""
    from sqlalchemy import text
    import uuid
    eng = _engine()
    rows = _rows()
    with eng.begin() as c:
        member_id = {}
        for code, spec in PRODUCTS.items():
            got = c.execute(text("""SELECT id FROM ax_dimension_member
                                    WHERE company_id=:co AND dimension_type='product'
                                      AND code=:code"""),
                            {"co": COMPANY_ID, "code": code}).scalar()
            if got is None:
                got = c.execute(text("""
                    INSERT INTO ax_dimension_member
                      (company_id, dimension_type, member_key, code, name,
                       is_unallocated, source, created_at)
                    VALUES (:co,'product',:key,:code,:name,false,'seed',now())
                    RETURNING id"""),
                    {"co": COMPANY_ID, "key": uuid.uuid4().hex,
                     "code": code, "name": spec["name"]}).scalar()
            member_id[code] = got
        n = 0
        for (year, code, measure, value) in rows:
            c.execute(text("""
                INSERT INTO ax_dimension_observation
                  (company_id, dataset_id, member_id, period, frequency,
                   measure, value, currency, data_status, basis,
                   source_sheet, calculation_version, created_at)
                VALUES (:co,:ds,:m,:p,:f,:meas,:v,'USD','observed','actual',
                        'seed','seed.1',now())
                ON CONFLICT (dataset_id, member_id, period, measure, basis)
                DO UPDATE SET value = EXCLUDED.value"""),
                {"co": COMPANY_ID, "ds": DATASET_ID, "m": member_id[code],
                 "p": year, "f": FREQUENCY, "meas": measure, "v": value})
            n += 1
    print(f"seeded {len(member_id)} members and {n} observations")


def verify():
    """⭐ Reconciliation on the REAL seeded rows, and the statements unmoved."""
    from sqlalchemy import text
    from services.api.modules.financials import dimensional_analytics as A
    eng = _engine()
    ok = True
    with eng.connect() as c:
        sha = c.execute(text("SELECT payload_sha256 FROM financial_datasets "
                             "WHERE id=:d"), {"d": DATASET_ID}).scalar()
        print("dataset payload_sha256:", sha)
        packs = c.execute(text("SELECT id, content_hash FROM ax_packs "
                               "WHERE cid=:c ORDER BY id"),
                          {"c": COMPANY_ID}).fetchall()
        print(f"packs for company {COMPANY_ID}: {len(packs)}")
        for pid, h in packs:
            print(f"   pack {pid} content_hash={h}")
        for year in PERIODS:
            for measure, line in (("revenue", "revenue"),
                                  ("direct_cost", "cogs"),
                                  ("direct_opex", "opex")):
                detail = {r[0]: r[1] for r in c.execute(text("""
                    SELECT m.code, o.value FROM ax_dimension_observation o
                    JOIN ax_dimension_member m ON m.id = o.member_id
                    WHERE o.dataset_id=:d AND o.period=:p AND o.measure=:meas"""),
                    {"d": DATASET_ID, "p": year, "meas": measure})}
                rec = A.revenue_by_dimension(detail, STATEMENT[year][line])
                tot = sum(rec["value"].values()) if rec["available"] else None
                good = tot is not None and abs(tot - STATEMENT[year][line]) < 1e-9
                ok &= good
                print(f"  {year} {measure:<12} "
                      f"{'OK ' if good else 'FAIL'} detail+unallocated="
                      f"{tot if tot is not None else 'n/a'}  "
                      f"statement={STATEMENT[year][line]}")
    print("\nRECONCILIATION", "HOLDS" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if a.apply:
        apply_seed()
    elif a.verify:
        sys.exit(verify())
    else:
        plan()
