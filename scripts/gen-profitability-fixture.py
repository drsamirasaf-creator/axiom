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
STATEMENT = {"revenue": 1000.0, "cogs": 600.0, "opex": 300.0}
LINES = {
    "PL-A": ("Alpha Systems",     360.0, 180.0, 12.0),
    "PL-B": ("Beta Controls",     180.0, 126.0,  6.0),   # thin — reverses
    "PL-C": ("Gamma Instruments", 200.0, 110.0,  7.0),
    "PL-D": ("Delta Modules",     100.0,  62.0,  3.0),
    "PL-E": ("Epsilon Services",   60.0,  32.0,  2.0),
}
PERIODS = (2024, 2025)
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
                  "periods": {"historical": list(PERIODS), "forecast": [],
                              "frequency": "annual"},
                  "income_statement": {k: {str(p): v for p in PERIODS}
                                       for k, v in STATEMENT.items()}},
            validation={"warnings": []})
        db.add(ds); db.flush()
        for code, (name, rev, dc, do) in LINES.items():
            m = DimensionMember(company_id=1, dimension_type="product",
                                member_key=f"k-{code}", code=code, name=name,
                                source="fixture")
            db.add(m); db.flush()
            for period in PERIODS:
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
    assert cur["totals"]["revenue"]["value"] == STATEMENT["revenue"]
    assert cur["revenue"]["value"].get("__unallocated__"), "no residual to show"

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
