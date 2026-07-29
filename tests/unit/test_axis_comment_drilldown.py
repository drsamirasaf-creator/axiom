"""The axis comment drill-down: the words are shown, the author is not.

⭐ THE RULING NARROWED THE PROMISE AND THEREFORE WIDENED WHAT MUST BE PROVED.
"Aggregate only" was self-enforcing — no text left the server, so no test was
needed. Now the verbatim text IS returned and the only thing standing between a
comment and its author is this endpoint's own discipline. That is a much weaker
guarantee to hold by inspection, so it is held by assertion.

⭐ THE CENTRAL TEST ASSERTS THE PAYLOAD, NOT THE RENDER. A `participant_ref` in
the response is exposed whether or not the UI prints it: it is in devtools, in
the browser cache, in any log that captures response bodies, and in the next
component that decides to use it. `test_no_identity_anywhere_in_the_payload`
walks the whole serialized response rather than checking known field names,
because the field that leaks is the one nobody thought to check.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="drilldown-", suffix=".db"))
import json
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.accounts import (
    SessionLocal, AssessmentCycle, AssessmentResponse,
    _ensure_department, _assess_ensure_framework,
)
from services.api.modules.enterprise_state.models import Enterprise


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def world(_app):
    """One closed cycle with three deliberately awkward axes.

    · axis A — 4 comments from 4 participants  -> ABOVE the floor, readable
    · axis B — 3 comments from ONE participant -> BELOW the floor, suppressed
                (the floor counts PEOPLE; a comment count alone would pass it)
    · axis C — no comments at all              -> the honest-empty state
    """
    db = SessionLocal()
    try:
        # ⭐ TENANT "showcase" ON PURPOSE. `_summary_access` admits anonymous
        # callers ONLY for showcase companies; every other company still requires
        # auth. V2 asks that the drill-down work on the anonymous demo, so the
        # fixture must BE a showcase company — testing it as a private one would
        # assert the wrong gate and leave the demo path unexercised.
        ent = Enterprise(name="Drilldown Co", tenant="showcase")
        db.add(ent); db.commit(); db.refresh(ent)
        cid = ent.id
        _ensure_department(db, cid, "Operations")
        fw = _assess_ensure_framework(db, cid)
        db.commit()

        # ⭐ GROUP BY THE SAME MAP THE ENDPOINT USES. The first version grouped by
        # `item.parent_code` while the endpoint groups by `_l1_maps`'s `l1_code`.
        # They are not the same key, so comments seeded "on axis B" arrived on
        # axis A and the counts were silently wrong — a fixture asserting against
        # its own private idea of the taxonomy rather than the product's.
        from services.api.accounts import _l1_maps, AssessmentItem
        id_map, l1_title = _l1_maps(db, fw.id)
        items = db.query(AssessmentItem).filter_by(framework_id=fw.id).all()
        by_l1 = {}
        for it in items:
            meta = id_map.get(it.id)
            if meta and meta.get("l1_code"):
                by_l1.setdefault(meta["l1_code"], []).append(it)
        leaf = [it for group in by_l1.values() for it in group]
        l1s = sorted(by_l1, key=lambda c: float(c) if str(c).replace(".", "").isdigit() else 99)
        assert len(l1s) >= 3, "fixture needs three axes to cover the three shapes"
        axis_a, axis_b, axis_c = l1s[0], l1s[1], l1s[2]

        now = datetime.utcnow()
        cyc = AssessmentCycle(company_id=cid, framework_id=fw.id, revision=fw.revision,
                              opened_at=now - timedelta(days=10),
                              closed_at=now - timedelta(days=3),
                              anonymity_mode="anonymous", depth="standard",
                              name="Drill Cycle")
        db.add(cyc); db.commit(); db.refresh(cyc)

        def respond(ref, item, comment, dept="Operations", seniority="Mid-level"):
            db.add(AssessmentResponse(
                cycle_id=cyc.id, participant_ref=ref, item_id=item.id,
                score=6, abstained=False, department=dept, seniority=seniority,
                comment=comment))

        # every participant scores every item, so the cei is well-formed
        for p in range(4):
            for it in leaf:
                db.add(AssessmentResponse(
                    cycle_id=cyc.id, participant_ref=f"P{p}", item_id=it.id,
                    score=6, abstained=False, department="Operations",
                    seniority="Mid-level", comment=None))
        db.commit()

        # axis A: four DIFFERENT participants comment -> above the floor
        for p in range(4):
            respond(f"P{p}", by_l1[axis_a][0], f"axis A verbatim from participant {p}")
        # axis B: ONE participant comments three times -> below the floor
        for k in range(min(3, len(by_l1[axis_b]))):
            respond("P0", by_l1[axis_b][k], f"axis B verbatim {k}")
        # axis C: nothing
        db.commit()

        from services.api.accounts import _cycle_cei
        snap = _cycle_cei(db, cyc)
        snap["sentiment_available"] = True
        snap["l1_sentiment"] = {c: {"sentiment": "negative", "theme": "t"} for c in l1s}
        snap["item_sentiment"] = {i.code: {"sentiment": "negative", "theme": "t"}
                                  for i in leaf}
        snap["item_rag"] = {i.code: "amber" for i in leaf}
        snap["item_divergence"] = {i.code: False for i in leaf}
        snap["l1_divergence"] = {c: True for c in l1s}
        cyc.snapshot = snap
        db.commit()
        return {"cid": cid, "a": axis_a, "b": axis_b, "c": axis_c,
                "refs": [f"P{p}" for p in range(4)]}
    finally:
        db.close()


def _get(app_, world_, axis, **params):
    q = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"/companies/{world_['cid']}/assessment/axis/{axis}/comments"
    return app_.get(url + ("?" + q if q else ""))


def test_verbatim_comments_are_returned_above_the_floor(_app, world):
    r = _get(_app, world, world["a"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["has_data"] is True
    assert not body.get("suppressed")
    assert body["n_comments"] == 4, body
    assert body["n_participants"] == 4, body
    texts = [c["comment"] for c in body["comments"]]
    assert len(texts) == 4
    assert all("axis A verbatim" in t for t in texts)


def test_no_identity_anywhere_in_the_payload(_app, world):
    """⭐ THE WHOLE RESPONSE, NOT THE FIELDS WE REMEMBERED TO CHECK.

    Asserting `"participant_ref" not in comment` only proves the field we thought
    of is absent. This serializes the entire body and searches it, so a ref that
    reappears under a new name, nested in the L2 decomposition, or echoed in a
    message is caught too."""
    r = _get(_app, world, world["a"])
    blob = json.dumps(r.json())
    for ref in world["refs"]:
        assert f'"{ref}"' not in blob, f"{ref} is present in the payload"
    for banned in ("participant_ref", "email", "invited_email", "participant_id",
                   "respondent", "name@", "@example"):
        assert banned not in blob, f"{banned!r} is present in the payload"


def test_floor_counts_people_not_comments(_app, world):
    """Three comments from ONE person must suppress. A floor on the comment count
    would let this through — which is the worse exposure, not the safer one."""
    r = _get(_app, world, world["b"])
    body = r.json()
    assert body["suppressed"] is True, body
    assert body["n_participants"] == 1, body
    assert body["n_comments"] >= 2, body
    assert body["comments"] == []
    assert body["reason"] == "below_anonymity_floor"


def test_axis_with_no_comments_uses_the_existing_vocabulary(_app, world):
    """B3: reuse 'no comment signal', do not invent a second phrase for the same
    state."""
    r = _get(_app, world, world["c"])
    body = r.json()
    assert body["has_data"] is True
    assert body["n_comments"] == 0
    assert body["comments"] == []
    assert "no comment signal" in body["message"].lower(), body["message"]


def test_l2_decomposition_is_surfaced(_app, world):
    r = _get(_app, world, world["a"])
    items = r.json()["items"]
    assert items, "the axis's L2 items must be present"
    for it in items:
        for k in ("item_code", "title", "score_rag", "sentiment", "divergence",
                  "n_comments"):
            assert k in it, f"{k} missing from the L2 decomposition"


def test_comment_tone_is_named_as_the_ITEM_s_tone(_app, world):
    """⭐ NOT `sentiment`. The classifier returns one verdict per ITEM over a batch
    of comments; no per-comment tone exists. Calling the field `sentiment` on a
    comment would present a group judgement as a judgement of that sentence."""
    c = _get(_app, world, world["a"]).json()["comments"][0]
    assert "item_sentiment" in c
    assert "sentiment" not in c, \
        "a bare `sentiment` on a comment claims a per-comment tone that is not computed"


def test_both_slice_dimensions_at_once_is_refused(_app, world):
    """B2: department ∩ seniority is frequently one person, and the k-floor cannot
    see that — it counts a compliant number while the CELL names the author."""
    r = _get(_app, world, world["a"], department=1, seniority="Mid-level")
    assert r.status_code == 422, r.text
    assert "not both" in r.json()["detail"].lower()


def test_unknown_axis_is_404_not_an_empty_success(_app, world):
    r = _get(_app, world, "99.9")
    assert r.status_code == 404, r.text


def test_anonymous_access_is_permitted(_app, world):
    """V2: this is a showcase surface. No Authorization header is sent by any
    test in this file — they all run anonymously — so a 200 above already proves
    it. Asserted explicitly so the guarantee is named rather than incidental."""
    r = _get(_app, world, world["a"])
    assert r.status_code == 200
    assert "authorization" not in {k.lower() for k in r.request.headers}
