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
# ⭐⭐ ACTUAL PERIODS ONLY, NEVER FORECAST (ruled 3 Aug). Meridian's dataset
# holds ten periods — five historical and five forecast — and the dimensional
# layer covers four of the actuals. A product-line allocation of a PROJECTION
# compounds two estimates: the forecast's own uncertainty and the allocation
# assumption on top of it, and a CFO would rightly question the result. The
# surface states the shortfall rather than implying a series it does not hold.
PERIODS = (2022, 2023, 2024, 2025)
FREQUENCY = "annual"

# Meridian's own income statement, READ FROM THE DATASET (id 45) on 4 Aug. The
# seed reconciles AGAINST these; it never rewrites them, and `verify` asserts
# they are byte-identical before and after.
STATEMENT = {
    2022: {"revenue": 906.8571, "cogs": 500.7429, "opex": 161.6571},
    2023: {"revenue": 1040.9143, "cogs": 571.7143, "opex": 189.2571},
    2024: {"revenue": 1198.6286, "cogs": 658.4571, "opex": 216.8571},
    2025: {"revenue": 1380.0000, "cogs": 757.0286, "opex": 248.4000},
}

# ═══════════════════════════════════════════════════════════════════════════
# THE PRODUCT LINES — designed for COVERAGE, each earning its place
# ═══════════════════════════════════════════════════════════════════════════
#
# ⭐⭐ PL-CTRL IS THE REVERSAL, AND IT DEVELOPS. Healthy at gross margin
# throughout and loss-making at allocated EBIT from 2024, because it consumes
# support and logistics far out of proportion to its revenue — and that
# consumption has been GROWING for three years.
#
#   PL-CTRL allocated EBIT:  2022 +18.6   2023 +8.0   2024 -6.0   2025 -13.6
#
# ⭐⭐ FOUR PERIODS WITH A DEVELOPING STORY, NOT FOUR RANDOM ONES. "This has been
# deteriorating for three years, and here is the driver" is an ARGUMENT. "This
# is bad now" is a data point. Two periods could only ever produce the second.
PRODUCTS = {
    "PL-DRIVE":  {"name": "Drive Systems"},
    "PL-AUTO":   {"name": "Automation Modules"},
    "PL-CTRL":   {"name": "Control Electronics"},
    "PL-SERV":   {"name": "Field Service"},
    "PL-SPARE":  {"name": "Spares & Consumables"},
}

# ⭐⭐ THE MIX STORY, AND EVERY LINE OF IT HAS A CAUSE.
#   PL-AUTO  GAINS SHARE (19% -> 27%) while its margin THINS (47% -> 41%) —
#            growth bought with price, which is what the mix-shift effect in
#            the margin bridge exists to surface.
#   PL-DRIVE SHRINKS (36% -> 32%) while its margin IMPROVES (46% -> 48%) —
#            the opposite trade, so the bridge's two effects point in opposite
#            directions and neither can be mistaken for the other.
#   PL-CTRL  holds its share and loses margin every year.
# A drift constant could not express any of this; the shares are stated per
# period so the story is legible in the data rather than in a comment.
SHARE = {
    2022: {"PL-DRIVE": 0.36, "PL-AUTO": 0.19, "PL-CTRL": 0.15,
           "PL-SERV": 0.09, "PL-SPARE": 0.09},
    2023: {"PL-DRIVE": 0.35, "PL-AUTO": 0.21, "PL-CTRL": 0.14,
           "PL-SERV": 0.09, "PL-SPARE": 0.09},
    2024: {"PL-DRIVE": 0.34, "PL-AUTO": 0.24, "PL-CTRL": 0.13,
           "PL-SERV": 0.09, "PL-SPARE": 0.08},
    2025: {"PL-DRIVE": 0.32, "PL-AUTO": 0.27, "PL-CTRL": 0.14,
           "PL-SERV": 0.10, "PL-SPARE": 0.07},
}
# ⭐ Sums to 0.88-0.90 — the remainder is genuinely UNALLOCATED and material on
# purpose. A demo where everything allocates cleanly hides the residual, which
# is the honest half of the reconciliation.

GROSS_MARGIN = {
    2022: {"PL-DRIVE": 0.46, "PL-AUTO": 0.47, "PL-CTRL": 0.36,
           "PL-SERV": 0.56, "PL-SPARE": 0.50},
    2023: {"PL-DRIVE": 0.47, "PL-AUTO": 0.45, "PL-CTRL": 0.35,
           "PL-SERV": 0.57, "PL-SPARE": 0.50},
    2024: {"PL-DRIVE": 0.47, "PL-AUTO": 0.44, "PL-CTRL": 0.34,
           "PL-SERV": 0.58, "PL-SPARE": 0.50},
    2025: {"PL-DRIVE": 0.48, "PL-AUTO": 0.41, "PL-CTRL": 0.32,
           "PL-SERV": 0.60, "PL-SPARE": 0.50},
}

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

# ⭐⭐ THE DRIVERS DEVELOP, AND THAT IS THE CAUSE OF THE REVERSAL. PL-CTRL's
# share of the support pool climbs 34% -> 64% and of logistics 30% -> 56% while
# its REVENUE share barely moves. The reversal is therefore explainable from
# the data — "it consumes more support every year" — rather than being an
# unexplained sign change. A constant driver set would have produced a line that
# is simply unprofitable, which no analyst can act on.
SUPPORT_DRIVERS = {
    2022: {"PL-DRIVE": 0.20, "PL-AUTO": 0.16, "PL-CTRL": 0.34,
           "PL-SERV": 0.20, "PL-SPARE": 0.10},
    2023: {"PL-DRIVE": 0.17, "PL-AUTO": 0.15, "PL-CTRL": 0.44,
           "PL-SERV": 0.16, "PL-SPARE": 0.08},
    2024: {"PL-DRIVE": 0.12, "PL-AUTO": 0.13, "PL-CTRL": 0.56,
           "PL-SERV": 0.13, "PL-SPARE": 0.06},
    2025: {"PL-DRIVE": 0.10, "PL-AUTO": 0.12, "PL-CTRL": 0.64,
           "PL-SERV": 0.10, "PL-SPARE": 0.04},
}
LOGISTICS_DRIVERS = {
    2022: {"PL-DRIVE": 0.25, "PL-AUTO": 0.18, "PL-CTRL": 0.30,
           "PL-SERV": 0.10, "PL-SPARE": 0.17},
    2023: {"PL-DRIVE": 0.22, "PL-AUTO": 0.16, "PL-CTRL": 0.40,
           "PL-SERV": 0.07, "PL-SPARE": 0.15},
    2024: {"PL-DRIVE": 0.18, "PL-AUTO": 0.13, "PL-CTRL": 0.50,
           "PL-SERV": 0.05, "PL-SPARE": 0.14},
    2025: {"PL-DRIVE": 0.14, "PL-AUTO": 0.11, "PL-CTRL": 0.56,
           "PL-SERV": 0.04, "PL-SPARE": 0.15},
}

COST_POOLS = {
    # C — an operational driver: support hours. This is WHY PL-CTRL reverses.
    "customer_support": {"method": "operational_driver", "grade": "C",
                         "share_of_opex": 0.24, "drivers": SUPPORT_DRIVERS},
    # C — logistics movements, also heavy on CTRL and heavier every year.
    "logistics": {"method": "operational_driver", "grade": "C",
                  "share_of_opex": 0.18, "drivers": LOGISTICS_DRIVERS},
    # D — revenue allocation: the fallback, and it is LABELLED as the fallback.
    "central_admin": {"method": "revenue", "grade": "D",
                      "share_of_opex": 0.20, "drivers": None},
}
# ⭐ The remaining opex is CORPORATE RESIDUAL — never forced onto a line.

# ⭐⭐ ONE DELIBERATE ABSENCE, per §7o. `units` is seeded for NO product, so the
# margin bridge's price and volume effects stay unavailable and the Data Quality
# surface has a real "supply this to unlock that" to render. A named absence in
# prose and an absence a capability actually HITS are different demonstrations
# — the second exercises the declaration path.
SEEDED_MEASURES = ("revenue", "direct_cost", "direct_opex")
DELIBERATELY_ABSENT = ("units", "list_price", "realised_price")


def _rows():
    """Every observation the seed writes, computed from the statement lines."""
    out = []
    for year in PERIODS:
        st = STATEMENT[year]
        for code in PRODUCTS:
            rev = st["revenue"] * SHARE[year][code]
            out.append((year, code, "revenue", rev))
            # direct cost from the line's own gross margin for that year
            out.append((year, code, "direct_cost",
                        rev * (1.0 - GROSS_MARGIN[year][code])))
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

    ⭐ THE DRIVERS ARE PER PERIOD. PL-CTRL's support share climbs 34% -> 64%
    across the four years while its revenue share holds, which is what makes
    the reversal explainable rather than merely true.
    """
    from services.api.modules.financials import dimensional_analytics as A
    st = STATEMENT[year]
    out = {"sales_commission": A.allocate(
        st["opex"] * DIRECT_OPEX_POOL, DIRECT_OPEX_SPLIT,
        method="direct_assignment")}
    for name, pool in COST_POOLS.items():
        drivers = pool["drivers"][year] if pool["drivers"] else dict(shares)
        out[name] = A.allocate(st["opex"] * pool["share_of_opex"], drivers,
                               method=pool["method"])
    return out


def shares_for(year):
    return dict(SHARE[year])


def margins_for(year):
    return dict(GROSS_MARGIN[year])


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
            gm = GROSS_MARGIN[y][c]
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
