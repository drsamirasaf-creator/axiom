#!/usr/bin/env python3
"""Emit the browser harness's `/metrics/ratios` fixture FROM THE REAL ENDPOINT.

⭐⭐ THE HAND-WRITTEN FIXTURE IS WHY THE BROWSER NEVER SAW THIS. The harness
stubbed the ratio surface with a payload someone typed, carrying
`"text": "is.gross_profit"` and no display fields at all. The page rendered it
faithfully, the assertions passed, and the leak the client was looking at was
invisible to every gate — the same failure recorded as CORE §8g one lane
earlier, on a different surface.

This records the endpoint's own output and REFUSES to write a recording that
still contains the artefact, so a broken explainer cannot be captured as if it
worked.

Read-only against production: builds its own temporary SQLite database, no
network. Writes one JSON file, path given on argv.
"""
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="ratiofix-", suffix=".db"))

from fastapi.testclient import TestClient                      # noqa: E402

from services.api.main import app                              # noqa: E402
from services.api.core.db import SessionLocal                  # noqa: E402
from services.api.modules.financials import models as fin_models   # noqa: E402
from tests.fixtures.refcases import meridian                    # noqa: E402

EMAIL = "ratio-fixture@example.test"
ARTEFACT = re.compile(r"\bIS_\.")
# The keys a surface renders. An identifier here is only permissible for a
# token the payload itself declares as unnamed.
DISPLAY = {"formula_display", "text_display", "expr_display", "needs_display",
           "definition_display", "name", "field_label"}
IDENT = re.compile(r"\b(?:is|bs|cf|mk|po|hc|sa)\.[a-z_][a-z_0-9]*")


def walk(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, f"{path}.{k}" if path else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


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
        data = meridian()
        ds = fin_models.FinancialDataset(
            tenant=tenant, name="Ratio Fixture Co",
            standard=data["company"]["standard"],
            ownership=data["company"]["ownership"], source="direct",
            data=data, validation={"warnings": []})
        db.add(ds); db.commit()
        did = ds.id
        db.close()

        resp = client.get(f"/api/v1/metrics/ratios/{did}")
        resp.raise_for_status()
        payload = resp.json()

    # ⭐ CHECKED BEFORE IT IS WRITTEN. Recording a payload that still leaks would
    # make the browser proof green over the defect — precisely the failure this
    # generator exists to end.
    bad = []
    for ratio in payload.get("ratios", []):
        declared = set()
        for p in ratio.get("periods", []):
            declared |= set(p.get("unnamed_tokens") or ())
        for path, s in walk(ratio):
            key = re.sub(r"\[\d+\]", "", path).rsplit(".", 1)[-1]
            if ARTEFACT.search(s):
                bad.append(f"{ratio['id']} {path}: IS_ in {s!r}")
            elif key in DISPLAY and (set(IDENT.findall(s)) - declared):
                bad.append(f"{ratio['id']} {path}: {s!r}")
    assert not bad, "refusing to record a leaking payload:\n  " + "\n  ".join(bad[:10])
    assert any(r.get("formula_display") for r in payload["ratios"]), \
        "no display formula in the payload — the endpoint predates the fix"

    payload["_provenance"] = (
        "RECORDED FROM THE ENDPOINT by scripts/gen-ratios-fixture.py in the "
        "axiom repo, over the Meridian reference case. Do not hand-edit: the "
        "hand-written version of this fixture is why the browser never saw the "
        "identifier leak. Regenerate instead.")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(f"recorded {out_path}: {len(payload['ratios'])} ratios, "
          f"{len(payload.get('absent', []))} absent, "
          f"coverage {payload['coverage']}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
