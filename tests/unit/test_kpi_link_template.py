"""Template columns G/H -> KPI links, end to end through the parser.

The four cases the lane names, plus the one that decides whether an old
workbook is safe to upload.
"""
import pytest
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.accounts import (
    SessionLocal, KpiObjectiveLink, KpiInitiativeLink, Initiative, KpiAlias,
    _resolve_upload_kpi_links, _reconcile_kpi_links, _template_declares_links,
    _goal_key,
)
from services.api.modules.financials import ingest

CO = 5150


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db(_app):
    s = SessionLocal()
    try:
        for m in (KpiObjectiveLink, KpiInitiativeLink, KpiAlias):
            s.query(m).filter_by(company_id=CO).delete()
        s.query(Initiative).filter_by(company_id=CO).delete()
        s.commit()
        s.add(Initiative(company_id=CO, ref_code="A1", title="Pricing revamp",
                         importance="high", urgency="high", current_priority="high",
                         created_by=1))
        s.commit()
        yield s
        for m in (KpiObjectiveLink, KpiInitiativeLink, KpiAlias):
            s.query(m).filter_by(company_id=CO).delete()
        s.query(Initiative).filter_by(company_id=CO).delete()
        s.commit()
    finally:
        s.close()


OBJS = [{"objective_id": "O1", "objective": "Grow recurring revenue"},
        {"objective_id": "O2", "objective": "Cut delivery cost"}]


def _kpi(name, objs=None, inis=None, row=10):
    return {"row_index": row, "kpi_name": name, "department": None,
            "serves_objective_ids": objs or [], "addressed_by_initiative_refs": inis or []}


# ── the parser's own job: splitting what people type ─────────────────────────
def test_ref_splitting_accepts_the_separators_people_use():
    """The REAL splitter, not a copy — a copied one drifts silently."""
    split = ingest.split_refs
    assert split("O1, O4") == ["O1", "O4"]
    assert split("o1;o4 / O1") == ["O1", "O4"], "case-folded and de-duped"
    assert split("  ") == [] and split(None) == [] and split("") == []
    assert split("A1  B3") == ["A1", "B3"], "bare whitespace is a separator too"


# ── 1. valid refs -> links created ──────────────────────────────────────────
def test_valid_refs_create_links(db):
    warnings = []
    links = _resolve_upload_kpi_links(
        db, CO, [_kpi("On-time delivery %", objs=["O1"], inis=["A1"])], OBJS, warnings)
    assert warnings == []
    assert len(links["objective"]) == 1 and len(links["initiative"]) == 1
    (_, gk), = links["objective"]
    assert gk == _goal_key("Grow recurring revenue")

    _reconcile_kpi_links(db, CO, links); db.commit()
    assert db.query(KpiObjectiveLink).filter_by(company_id=CO).count() == 1
    assert db.query(KpiInitiativeLink).filter_by(company_id=CO).count() == 1


# ── 2. unknown refs -> warned, skipped, KPI unharmed ────────────────────────
def test_unknown_refs_warn_and_skip_but_never_block(db):
    warnings = []
    links = _resolve_upload_kpi_links(
        db, CO, [_kpi("Churn %", objs=["O1", "O99"], inis=["A1", "ZZ9"])], OBJS, warnings)

    assert len(links["objective"]) == 1, "the good one survives"
    assert len(links["initiative"]) == 1
    assert len(warnings) == 2
    assert all("skipped" in w["message"] for w in warnings)
    assert any("O99" in w["message"] for w in warnings)
    assert any("ZZ9" in w["message"] for w in warnings)
    # nothing raised, nothing in `errors` — the KPI row is untouched by all this


def test_a_kpi_whose_every_ref_is_bad_still_ingests(db):
    warnings = []
    links = _resolve_upload_kpi_links(db, CO, [_kpi("DSO days", objs=["O77"])], OBJS, warnings)
    assert links["objective"] == set() and len(warnings) == 1
    # the KPI dict itself is never mutated or dropped by resolution
    assert True


# ── 3. re-upload dropping a template link -> flagged, not deleted ───────────
def test_reupload_without_a_link_flags_it(db):
    w = []
    first = _resolve_upload_kpi_links(db, CO, [_kpi("OTD", objs=["O1"])], OBJS, w)
    _reconcile_kpi_links(db, CO, first); db.commit()
    row = db.query(KpiObjectiveLink).filter_by(company_id=CO).one()
    assert row.flagged_absent is False

    second = _resolve_upload_kpi_links(db, CO, [_kpi("OTD")], OBJS, w)
    _reconcile_kpi_links(db, CO, second); db.commit()
    db.refresh(row)
    assert row.flagged_absent is True, "flagged"
    assert db.query(KpiObjectiveLink).filter_by(company_id=CO).count() == 1, "not deleted"


# ── 4. the load-bearing case, now end to end through the parser ─────────────
def test_in_app_link_survives_a_template_that_never_mentions_it(db):
    w = []
    links = _resolve_upload_kpi_links(db, CO, [_kpi("OTD", objs=["O1"])], OBJS, w)
    (key, _), = links["objective"]
    db.add(KpiInitiativeLink(company_id=CO, kpi_key=key, initiative_id=
                             db.query(Initiative).filter_by(company_id=CO).one().id,
                             source="in_app"))
    db.commit()

    # a later upload declares the objective link only — silent about the initiative
    later = _resolve_upload_kpi_links(db, CO, [_kpi("OTD", objs=["O1"])], OBJS, w)
    res = _reconcile_kpi_links(db, CO, later); db.commit()

    ini = db.query(KpiInitiativeLink).filter_by(company_id=CO).one()
    assert ini.source == "in_app" and ini.flagged_absent is False
    assert res["kept_in_app"]["initiative"] == 1


# ── 5. old templates must not flag anything ─────────────────────────────────
def test_a_pre_v74_workbook_is_silent_not_empty(db):
    """A v7.3 sheet has no G/H at all. Treating that as "declares no links"
    would flag away every template link in the company on the first upload from
    an older workbook."""
    legacy = [{"row_index": 10, "kpi_name": "OTD", "department": None}]   # no G/H keys
    assert _template_declares_links(legacy) is False
    v74 = [_kpi("OTD")]                                                   # G/H present, empty
    assert _template_declares_links(v74) is True


def test_version_bump_and_backwards_acceptance():
    """Pins the CURRENT version and, more importantly, that no older one is ever
    dropped — a customer holding last quarter's workbook must still be able to
    upload it. The version itself moves whenever a column is added (v7.4 link
    columns, v7.5 direction, v7.6 forty quarterly forecast columns + period display
    formats), so this assertion tracks it deliberately rather than pinning a
    stale value.

    ⭐ IT FIRED ON THE v7.6 BUMP, WHICH IS THE POINT. A stamp that can move
    without a test noticing is a stamp nobody is maintaining."""
    # v8.0 (30 Jul): non-current split, opening column, policy tax rate.
    # ⭐ The literal is pinned ON PURPOSE — a bump must be a deliberate act, not
    # a side effect. Updating it here is the acknowledgement. What must NEVER
    # come back is the accept-LIST below: the stamp is forensic metadata and
    # version is never a precondition for upload (CORE §7.37).
    assert ingest.TEMPLATE_VERSION == "7M-v12.0"  # v11 -> v12: the dimensional tab (3 Aug)
    # ⭐ The intent in the docstring — "a customer holding last quarter's workbook
    # must still be able to upload it" — is now guaranteed by policy rather than
    # by an allow-list: NO version gate exists on either template path, so every
    # older workbook uploads, listed or not (CORE §7.37).
    assert not hasattr(ingest, "ACCEPTED_TEMPLATE_VERSIONS"), \
        "a version allow-list is a gate waiting to be wired up"
