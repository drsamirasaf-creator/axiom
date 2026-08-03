#!/usr/bin/env python3
"""Emit the browser harness's `/profitability` fixture FROM THE REAL ENDPOINT.

⭐⭐ WHY THIS SCRIPT EXISTS. The harness's first fixture was HAND-WRITTEN. It
contained `allocated_ebit` values and the reversal, so the browser assertion
"the reversal leads the page" passed — while the production endpoint was
returning `available: false` for that level on every line of every dataset. The
page was proven to render a payload nobody's code produces.

A fixture written by hand tests the fixture. This one is a recording of the
endpoint's own output over rows written through the ORM, so if the endpoint
stops producing allocated EBIT, the browser proof goes red with it.

Read-only against production: it builds its own temporary SQLite database and
never opens a network connection. Writes one JSON file, path given on argv.

    python3 scripts/gen-profitability-fixture.py \
        ../optimization-anchor/scripts/fixtures/profitability-payload.json
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="fixgen-", suffix=".db"))

from fastapi.testclient import TestClient                      # noqa: E402

from services.api.main import app                              # noqa: E402
from services.api.core.db import SessionLocal                  # noqa: E402
from services.api.dimensional import (DimensionMember,         # noqa: E402
                                      DimensionObservation)
from services.api.modules.financials import models as fin_models   # noqa: E402

# ⭐ MERIDIAN'S SHAPE, NOT MERIDIAN'S FIGURES. The fixture is committed to a
# public repo, so it carries no customer numbers: five lines, an incomplete
# decomposition on every measure, and one line that reverses — the properties
# the page must render, at figures that belong to nobody.
# ⭐ OPEX GROWS FASTER THAN REVENUE (25% -> 36% of it). That is the CAUSE of the
# reversal: the shared pool a line is charged for outruns the gross profit it
# earns, so a line whose own margin never moves still slides into loss. The
# first draft held opex at a flat 30% of revenue — every line then scaled
# together, nothing diverged, and the generator REFUSED TO RECORD ITSELF.
STATEMENT = {2022: {"revenue": 800.0, "cogs": 480.0, "opex": 200.0},
             2023: {"revenue": 900.0, "cogs": 540.0, "opex": 255.0},
             2024: {"revenue": 1000.0, "cogs": 600.0, "opex": 320.0},
             2025: {"revenue": 1100.0, "cogs": 660.0, "opex": 395.0}}

# ⭐⭐ FOUR PERIODS WITH THE DEVELOPING REVERSAL. A two-period fixture can only
# prove that a reversal RENDERS; it cannot prove the trend panel or the
# trajectory finding, both of which need a direction. PL-B's gross margin holds
# while its allocated EBIT falls every year — the divergence the module exists
# to surface.
NAMES = {"PL-A": "Alpha Systems", "PL-B": "Beta Controls",
         "PL-C": "Gamma Instruments", "PL-D": "Delta Modules",
         "PL-E": "Epsilon Services"}
SHARE = {2022: {"PL-A": 0.38, "PL-B": 0.18, "PL-C": 0.18, "PL-D": 0.10, "PL-E": 0.06},
         2023: {"PL-A": 0.37, "PL-B": 0.18, "PL-C": 0.19, "PL-D": 0.10, "PL-E": 0.06},
         2024: {"PL-A": 0.36, "PL-B": 0.18, "PL-C": 0.20, "PL-D": 0.10, "PL-E": 0.06},
         2025: {"PL-A": 0.34, "PL-B": 0.18, "PL-C": 0.22, "PL-D": 0.10, "PL-E": 0.06}}
GM = {2022: {"PL-A": 0.50, "PL-B": 0.31, "PL-C": 0.44, "PL-D": 0.38, "PL-E": 0.46},
      2023: {"PL-A": 0.50, "PL-B": 0.31, "PL-C": 0.43, "PL-D": 0.38, "PL-E": 0.46},
      2024: {"PL-A": 0.51, "PL-B": 0.31, "PL-C": 0.42, "PL-D": 0.38, "PL-E": 0.46},
      2025: {"PL-A": 0.52, "PL-B": 0.31, "PL-C": 0.40, "PL-D": 0.38, "PL-E": 0.46}}
# direct opex share of the company opex line, per line — small and stable, so
# the movement in allocated EBIT comes from the SHARED pool as it does on a real
# dataset (the endpoint allocates the residual by revenue).
DOPEX = {"PL-A": 0.040, "PL-B": 0.020, "PL-C": 0.023, "PL-D": 0.010, "PL-E": 0.007}
PERIODS = (2022, 2023, 2024, 2025)
# Statement-only periods: no dimensional detail exists for them, by design.
EARLIER = {2018: {"revenue": 520.0, "cogs": 312.0, "opex": 130.0},
           2019: {"revenue": 585.0, "cogs": 351.0, "opex": 146.0},
           2020: {"revenue": 610.0, "cogs": 372.0, "opex": 158.0},
           2021: {"revenue": 700.0, "cogs": 420.0, "opex": 175.0}}
STATEMENT_ONLY = tuple(sorted(EARLIER))
# Forecast periods: never carry dimensional detail, BY RULING rather than by
# omission — the distinction the coverage block has to make.
PROJECTED = {2026: {"revenue": 1200.0, "cogs": 720.0, "opex": 430.0},
             2027: {"revenue": 1310.0, "cogs": 786.0, "opex": 470.0}}
FORECAST = tuple(sorted(PROJECTED))
EMAIL = "fixture-gen@example.test"


def main(out_path):
    with TestClient(app) as client:
        creds = {"email": EMAIL, "password": "correct-horse-battery"}
        r = client.post("/api/v1/auth/register", json=creds)
        if r.status_code == 409:
            r = client.post("/api/v1/auth/login", json=creds)
        r.raise_for_status()
        client.headers.update({"Authorization": f"Bearer {r.json()['token']}"})

        db = SessionLocal()
        from services.api.modules.identity import models as id_models
        tenant = db.query(id_models.User).filter_by(email=EMAIL).one().tenant
        ds = fin_models.FinancialDataset(
            tenant=tenant, name="Fixture Co", standard="ifrs",
            ownership="private", source="direct",
            data={"company": {"name": "Fixture Co", "ownership": "private"},
                  # ⭐⭐ EIGHT PERIODS OF STATEMENTS, FOUR OF DIMENSIONAL DETAIL
                  # — the real shape, and the one the surface must be honest
                  # about. A fixture whose statement matched its detail exactly
                  # could not prove that the page STATES what it lacks, which is
                  # the whole point of the coverage block.
                  # ⭐⭐ AND FORECAST PERIODS, because the surface must
                  # distinguish "no detail was supplied" from "AXIOM refuses to
                  # produce it". The first version of this fixture had none, and
                  # the endpoint reported Meridian's five forecast years among
                  # the periods with no product-line detail — one line above a
                  # note saying it does not produce one.
                  "periods": {"historical": list(STATEMENT_ONLY) + list(PERIODS),
                              "forecast": list(FORECAST), "frequency": "annual"},
                  "income_statement": {
                      k: {**{str(p): v[k] for p, v in EARLIER.items()},
                          **{str(p): STATEMENT[p][k] for p in PERIODS},
                          **{str(p): v[k] for p, v in PROJECTED.items()}}
                      for k in ("revenue", "cogs", "opex")}},
            validation={"warnings": []})
        db.add(ds); db.flush()
        for code, name in NAMES.items():
            m = DimensionMember(company_id=1, dimension_type="product",
                                member_key=f"k-{code}", code=code, name=name,
                                source="fixture")
            db.add(m); db.flush()
            for period in PERIODS:
                st = STATEMENT[period]
                rev = st["revenue"] * SHARE[period][code]
                dc = rev * (1.0 - GM[period][code])
                do = st["opex"] * DOPEX[code]
                for measure, value in (("revenue", rev), ("direct_cost", dc),
                                       ("direct_opex", do)):
                    db.add(DimensionObservation(
                        company_id=1, dataset_id=ds.id, member_id=m.id,
                        period=period, frequency="annual", measure=measure,
                        value=value, data_status="observed", basis="actual"))
        db.commit()
        did = ds.id
        db.close()

        resp = client.get(f"/api/v1/metrics/profitability/{did}")
        resp.raise_for_status()
        payload = resp.json()

    # ⭐ THE RECORDING IS CHECKED BEFORE IT IS WRITTEN. A fixture that captured
    # the defect would make the browser proof green over a broken surface — the
    # exact failure this script was written to end.
    block = payload["by_type"]["product"]
    cur = block["by_period"][str(block["periods"][-1])]
    reversing = [c for c, h in cur["lines"].items()
                 if h["allocated_ebit"]["available"]
                 and h["allocated_ebit"]["value"] < 0
                 and (h["gross_profit"]["margin"] or 0) > 0.15]
    assert reversing, "the endpoint produced no reversal — refusing to record it"
    assert cur["totals"]["revenue"]["value"] == STATEMENT[PERIODS[-1]]["revenue"]
    assert cur["revenue"]["value"].get("__unallocated__"), "no residual to show"
    # ⭐ THE FOUR-PERIOD CAPABILITIES MUST BE IN THE RECORDING, or the browser
    # proof of the trend panel and the findings would be over a payload that
    # cannot express them.
    assert len(block["periods"]) == 4, "the fixture is not four periods"
    assert len(block.get("mix_shift_series") or []) == 3, "no mix-shift series"
    diverging = [c for c, t in (block.get("trend") or {}).items() if t["diverging"]]
    assert diverging, "no line diverges — the trend panel would say nothing"
    kinds = {f["id"].split(":")[0] for f in (block.get("findings") or [])}
    assert "reversal_trajectory" in kinds, f"no trajectory finding: {kinds}"
    assert "mix_dilutive" in kinds, f"no mix-shift finding: {kinds}"
    # ⭐ AND THE SHORTFALL IS IN THE RECORDING. Without it the browser could not
    # prove the surface states what it does not hold.
    cov = payload["coverage"]
    assert cov["missing_periods"] == list(STATEMENT_ONLY), cov
    assert cov["excluded_forecast_periods"] == list(FORECAST), cov

    payload["_provenance"] = (
        "RECORDED FROM THE ENDPOINT by scripts/gen-profitability-fixture.py in "
        "the axiom repo. Do not hand-edit: a hand-written fixture is how the "
        "browser proof passed while allocated EBIT was unavailable in "
        "production. Regenerate instead.")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(f"recorded {out_path}: {len(cur['lines'])} lines, "
          f"{len(block['periods'])} periods, reversal on {reversing}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
