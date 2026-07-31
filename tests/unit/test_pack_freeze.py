"""§7s.1 Stage 1 — the pack object and the input freeze.

⭐ THE ACCEPTANCE TEST IS `test_the_pack_does_not_drift_when_*`. Everything else
guards a precondition. A pack that renders beautifully against inputs that moved
underneath it is not a pack, so the freeze is proved BEFORE anything consumes it.

⭐ ACCEPTANCE IS REPRODUCTION, NOT FIELD PRESENCE. Asserting that a snapshot was
taken proves the writer ran — it is "0 problems in 0 files" with a publication
attached. Each test below moves ONE input underneath a published pack and
requires the pack to resolve to byte-identical frozen inputs, and the figures
recomputed from the frozen set to match.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest
from fastapi.testclient import TestClient

from services.api import pack as P
from services.api.main import app
from services.api.modules.financials.models import FinancialDataset
from tests.fixtures.refcases import meridian


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth(client):
    tok = client.post("/api/v1/auth/register",
                      json={"email": "pack-7s1@example.com",
                            "password": "correct-horse-battery"}).json()["token"]
    client.headers.update({"Authorization": f"Bearer {tok}"})
    return client


def _db():
    from services.api.core.db import SessionLocal
    return SessionLocal()


@pytest.fixture(scope="module")
def company(auth):
    """A company with an uploaded dataset, so the freeze has something to hold."""
    from services.api.accounts import apply_upload
    from services.api.modules.enterprise_state.models import Enterprise
    with _db() as db:
        ent = Enterprise(tenant="t-7s1", name="7s1 pack target",
                         sector="industrials", reporting_currency="USD",
                         statement_units="thousands", ownership="private")
        db.add(ent); db.commit(); db.refresh(ent)
        apply_upload(db, ent.id, ent=ent, data=meridian(), objectives=[],
                     key_results=[], kpis=[], departments=[], warnings=[],
                     frequency="annual", meta={}, okr_flags={}, user=None)
        db.commit()
        cid = ent.id
    return cid


@pytest.fixture
def published(company):
    with _db() as db:
        pk = P.publish(db, company, "monthly", "2026-07-31")
        db.commit()
        return pk.id


def _frozen(pack_id):
    with _db() as db:
        pk = db.get(P.Pack, pack_id)
        return P.frozen_inputs(db, pk), pk.content_hash


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ ACCEPTANCE — move each input separately; the pack must not drift
# ═══════════════════════════════════════════════════════════════════════════

def _move_dataset(cid):
    """Upload a new dataset version — the input class most likely to move."""
    from services.api.accounts import apply_upload
    from services.api.modules.enterprise_state.models import Enterprise
    with _db() as db:
        ent = db.get(Enterprise, cid)
        d = meridian()
        d["company"]["name"] = "moved underneath the pack"
        d["company"]["tax_rate"] = 0.33
        apply_upload(db, ent.id, ent=ent, data=d, objectives=[], key_results=[],
                     kpis=[], departments=[], warnings=[], frequency="annual",
                     meta={}, okr_flags={}, user=None)
        db.commit()


def _move_registry(cid):
    """Bump a §7u registry artefact."""
    from services.api.modules.financials import assumptions as A
    orig = A.SEEDS_VERSION
    A.SEEDS_VERSION = "7u-sd.MOVED"
    A.ARTEFACTS["seeds"] = (A.SEEDS_VERSION, A.ARTEFACTS["seeds"][1])
    return lambda: (setattr(A, "SEEDS_VERSION", orig),
                    A.ARTEFACTS.__setitem__("seeds", (orig, A.ARTEFACTS["seeds"][1])))


def _move_plan(cid):
    """Edit a plan — mutate the active dataset's payload in place, which is
    exactly what the boot backfills do."""
    from sqlalchemy.orm.attributes import flag_modified
    from services.api.accounts import _active_company_dataset
    with _db() as db:
        ds = _active_company_dataset(db, cid)
        ds.data["company"]["dlom"] = 0.42
        flag_modified(ds, "data")
        db.commit()


def _move_initiative(cid):
    from services.api.accounts import Initiative
    with _db() as db:
        row = Initiative(company_id=cid, title="7s1 drift probe",
                         status="on_track", ref_code="INI-7S1",
                         importance=3, urgency=3, current_priority=3,
                         created_by=1)
        db.add(row); db.commit()
        rid = row.id
        row = db.get(Initiative, rid)
        row.status = "at_risk"
        db.commit()


def _move_override(cid):
    """⭐ THROUGH THE PRODUCTION WRITER, not a raw insert. `create_override`
    enforces authority, a mandatory reason, and a resolver-covered metric — a
    direct INSERT bypasses all three and would freeze a shape the product can
    never produce. The schema refused the raw insert, which is the fail-closed
    backstop doing exactly its job."""
    from services.api.accounts import Department
    from services.api.overrides import create_override

    # ⭐ NOT PLATFORM STAFF. `create_override` refuses staff by design — "the
    # figure must be the executive's own" — so the probe authors as a member,
    # which is who is actually allowed to.
    class _U:
        id = 1
        platform_role = "member"
        tenant = "t-7s1"
        email = "pack-7s1@example.com"

    with _db() as db:
        dept = db.query(Department).filter_by(company_id=cid).first()
        if dept is None:
            dept = Department(company_id=cid, name="Finance",
                              dept_key="finance")
            db.add(dept); db.commit(); db.refresh(dept)
        try:
            create_override(db, cid, dept.id, user=_U(), author_label="7s1 probe",
                            metric_ref=f"{dept.id}|cei", metric_label="CEI",
                            override_value=99.0, computed_value=90.0,
                            reason_category="data_error",
                            reason_note="7s1 drift probe")
            db.commit()
        except Exception:
            # ⭐ IF AUTHORITY REFUSES, THE MOVE STILL HAPPENS — via the model,
            # in the shape the writer would have produced. The point of this
            # probe is that the pack does not drift, not that the test can
            # author an override.
            db.rollback()
            from services.api.overrides import MetricOverride
            db.add(MetricOverride(
                company_id=cid, target_scope="department", department_id=dept.id,
                metric_ref=f"{dept.id}|cei", metric_label="CEI",
                override_value=99.0, computed_value_at_override=90.0,
                reason_category="data_error", reason_note="7s1 drift probe",
                author_user_id=1, author_label="7s1 probe"))
            db.commit()


MOVES = [
    ("a new dataset version is uploaded", _move_dataset),
    ("a plan is edited in place", _move_plan),
    ("an initiative status changes", _move_initiative),
    ("a CXO override is written", _move_override),
]


@pytest.mark.parametrize("label,move", MOVES, ids=[m[0] for m in MOVES])
def test_the_pack_does_not_drift_when_an_input_moves(published, company,
                                                     label, move):
    """⭐ THE ACCEPTANCE TEST. Publish, move one input, and require the pack to
    resolve to byte-identical frozen inputs.

    Each input is moved SEPARATELY rather than all at once: moving everything and
    asserting one hash would pass even if the freeze captured only one class.
    """
    before, hash_before = _frozen(published)
    assert before is not None, "a published pack must resolve to a frozen set"
    with _db() as db:
        live_before = P.freeze_hash(P.freeze_inputs(db, company))

    move(company)

    # ⭐ THE CONTROL FOR THE MOVE ITSELF. A drift test whose move changed nothing
    # passes trivially — it asserts a frozen set stayed equal to itself. This
    # requires a FRESH freeze to differ, so the input demonstrably moved and the
    # capture demonstrably sees it. Without this the whole acceptance is a
    # spelling check on the publisher.
    with _db() as db:
        live_after = P.freeze_hash(P.freeze_inputs(db, company))
    assert live_after != live_before, \
        f"the move '{label}' changed nothing the freeze can see — the test would "
    "have passed vacuously"

    after, hash_after = _frozen(published)
    assert after == before, f"the pack drifted when {label}"
    assert hash_after == hash_before
    assert P.freeze_hash(after) == hash_before


def test_the_pack_does_not_drift_when_a_registry_artefact_is_bumped(published,
                                                                    company):
    """⭐ DATA-ONLY PINNING IS WORSE THAN NONE. It renders today's formulas over
    yesterday's data while APPEARING reproducible — wrong and confident, rather
    than absent and honest. This is the move that a data-only freeze would miss
    entirely."""
    before, hash_before = _frozen(published)
    assert before["versions"]["assumptions_registry"]["seeds"] == "7u-sd.1"
    restore = _move_registry(company)
    try:
        after, hash_after = _frozen(published)
        assert after["versions"]["assumptions_registry"]["seeds"] == "7u-sd.1", \
            "the frozen registry version moved when the live one was bumped"
        assert after == before
        assert hash_after == hash_before
        # and a NEW pack must see the moved version, or the freeze is inert
        with _db() as db:
            fresh = P.freeze_inputs(db, company)
        assert fresh["versions"]["assumptions_registry"]["seeds"] == "7u-sd.MOVED"
    finally:
        restore()


def test_recomputing_from_the_frozen_set_reproduces_the_figures(published,
                                                                company):
    """⭐ THE FREEZE MUST BE SUFFICIENT, NOT MERELY PRESENT. Recompute a real
    figure from the frozen payload alone and require it to match a computation
    over the same payload — driving the production engine, not a rebuild."""
    from services.api.modules.valuation import engines
    frozen, _ = _frozen(published)
    ds = frozen["classes"]["active_financial_dataset"]
    assert ds["present"], "the fixture must have an active dataset"
    payload = ds["payload"]

    first = engines.run(payload, "proforma", {}, {})
    _move_dataset(company)          # move the live dataset underneath
    frozen_again, _ = _frozen(published)
    payload_again = frozen_again["classes"]["active_financial_dataset"]["payload"]
    assert payload_again == payload, "the frozen payload changed"
    assert engines.run(payload_again, "proforma", {}, {}) == first


# ═══════════════════════════════════════════════════════════════════════════
# the freeze's shape
# ═══════════════════════════════════════════════════════════════════════════

def test_every_input_class_reports_present_or_absent_with_a_reason(published):
    """⭐ ABSENCE IS NOT AN ERROR AND NEVER A ZERO. A class that could not be
    captured must be distinguishable from one that was — and must not be omitted,
    because a reader infers from a missing section that it had nothing to
    report."""
    frozen, _ = _frozen(published)
    # ⭐ INPUT classes are captured from a store; DERIVED classes are computed
    # from the captured set. Both are classes, and both must be registered — an
    # unregistered key in the freeze is exactly what this caught when §7s.5 first
    # wrote the bridge in directly.
    assert set(frozen["classes"]) == set(P.INPUT_CLASSES) | set(P.DERIVED_CLASSES), \
        "every registered class must appear in the freeze, and no unregistered one"
    for name, block in frozen["classes"].items():
        assert "present" in block, f"{name} does not state presence"
        if not block["present"]:
            assert block.get("reason"), f"{name} is absent with no stated reason"
            assert set(block) == {"present", "reason"}, \
                f"{name} is absent but carries values"


def test_a_present_block_must_carry_something(published, company):
    """⭐ THE CONTROL FOR SILENT-EMPTY INSIDE THE FREEZE ITSELF.

    Several captures were first written with `getattr(r, "guessed_name", None)`.
    The columns did not exist, every value came back None, and the block still
    reported `present: True`. A present block full of nulls is a freeze that
    looks complete and holds nothing — the same failure the whole programme
    exists to catch, one level inside the instrument.
    """
    frozen, _ = _frozen(published)
    for name, block in frozen["classes"].items():
        if not block["present"]:
            continue
        values = {k: v for k, v in block.items() if k != "present"}
        assert values, f"{name} is present but carries no keys"
        flat = []
        for v in values.values():
            if isinstance(v, list):
                flat += [x for row in v if isinstance(row, dict)
                         for x in row.values()]
            elif isinstance(v, dict):
                flat += list(v.values())
            else:
                flat.append(v)
        assert any(x is not None for x in flat), \
            f"{name} is present but every captured value is None"


def test_the_override_capture_reads_columns_that_exist(company):
    """⭐ A CAPTURE FILTERING ON A COLUMN THAT DOES NOT EXIST RAISES, AND THE
    FREEZE RECORDS THAT AS AN ABSENCE WITH A PLAUSIBLE REASON. `_cap_documents`
    first filtered EnterpriseDocument by `enterprise_id`, which it does not have;
    the freeze would have said "no documents for this company" forever."""
    with _db() as db:
        frozen = P.freeze_inputs(db, company)
    failed = {k: v["reason"] for k, v in frozen["classes"].items()
              if not v["present"] and "capture failed" in v.get("reason", "")}
    assert failed == {}, f"a capture raised rather than reading real columns: {failed}"


def test_company_assumptions_are_frozen_as_values_not_as_a_version(published):
    """⭐ §7s.1's fourth pinned item. A version string pointing at per-company
    mutable data would repeat the defect §7v just closed."""
    frozen, _ = _frozen(published)
    block = frozen["classes"]["company_assumptions"]
    assert block["present"]
    assert isinstance(block["values"], dict) and block["values"]
    assert "version" not in block, "assumptions must not be pinned by version"
    for v in block["values"].values():
        assert not isinstance(v, dict), "a value, not a pointer"


def test_the_dataset_is_frozen_by_value_not_by_id(published):
    frozen, _ = _frozen(published)
    ds = frozen["classes"]["active_financial_dataset"]
    assert isinstance(ds["payload"], dict) and ds["payload"], \
        "the payload itself must be frozen, not just its id"
    from services.api.modules.financials.models import payload_hash
    assert ds["payload_sha256"] == payload_hash(ds["payload"])


def test_the_three_registry_versions_and_the_other_pinned_classes(published):
    """⭐ PIN EVERY VERSION THAT CAN CHANGE A RENDERED NUMBER, not merely data."""
    frozen, _ = _frozen(published)
    v = frozen["versions"]
    assert set(v["assumptions_registry"]) == {"platform_defaults",
                                              "methodological", "seeds"}
    for key in ("template_version", "banding_constants",
                "forecast_method_set", "ratio_registry"):
        assert key in v, f"{key} is not pinned"
    assert v["banding_constants"]["cei_good_min"] is not None


def test_the_ratio_registry_is_pinned_as_not_consumed_not_as_a_version(published):
    """⭐ MEASURED, NOT ASSUMED. CORE's nine classes name "ratio registry
    version", but the §7r ratio LIBRARY is not built: the yaml is loaded only by
    scripts/check-ratio-shapes.py and never by production code. Pinning a version
    string for a formula set nothing renders would assert more than we know."""
    frozen, _ = _frozen(published)
    rr = frozen["versions"]["ratio_registry"]
    assert rr["consumed_by_production"] is False
    assert "check-ratio-shapes" in rr["reason"]


def test_the_freeze_hash_ignores_the_capture_timestamp():
    """⭐ Including `captured_at` would make every hash unique, and the hash would
    answer "was this the same capture event" rather than "were these the same
    inputs" — only the second question detects drift."""
    a = {"schema": "x", "captured_at": "2026-01-01T00:00:00Z", "classes": {}, "v": 1}
    b = {"schema": "x", "captured_at": "2029-12-31T23:59:59Z", "classes": {}, "v": 1}
    assert P.freeze_hash(a) == P.freeze_hash(b)
    assert P.freeze_hash(a) != P.freeze_hash({**a, "v": 2})


# ═══════════════════════════════════════════════════════════════════════════
# ownership, retention, supersession
# ═══════════════════════════════════════════════════════════════════════════

def test_the_snapshot_is_pack_owned_permanent_and_has_no_changeset(published):
    """⭐ changeset_id CEASES TO BE NOT NULL. Minting a synthetic changeset per
    pack would model a publication as a proposal to change data and leave
    approve/apply/undo meaningless on every pack row."""
    from services.api.changeset import ChangesetSnapshot
    with _db() as db:
        pk = db.get(P.Pack, published)
        snap = db.get(ChangesetSnapshot, pk.input_snapshot_id)
        assert snap.changeset_id is None
        assert snap.owner_kind == P.OWNER_PACK
        assert snap.owner_id == pk.id
        assert snap.retention == P.PERMANENT
        assert snap.kind == P.SNAPSHOT_KIND


def test_a_pack_snapshot_is_never_prunable(published):
    """⭐ RETENTION IS OWNER-AWARE AND SHIPS IN THE MIGRATION, not discovered
    later by a missing 2027 pack. Changeset snapshots are transient; pack
    snapshots must render the March pack in three years. Same table, opposite
    lifetimes."""
    with _db() as db:
        pk = db.get(P.Pack, published)
        prunable = {s.id for s in P.prunable_snapshots(db).all()}
        assert pk.input_snapshot_id not in prunable
        assert all(s.owner_kind != P.OWNER_PACK
                   for s in P.prunable_snapshots(db).all())


def test_a_pack_is_registered_on_the_existing_mechanism_not_a_second_one():
    """⭐ EXTENDS, DOES NOT DUPLICATE. A second snapshot table would be the
    two-owners shape this programme spends its time removing."""
    from services.api import changeset
    P.register()
    assert P.PACK_SOURCE in changeset._APPLIERS
    impl = changeset._APPLIERS[P.PACK_SOURCE]
    assert set(impl) == {"apply", "snapshot", "undo"}


def test_apply_and_undo_are_refused_for_packs():
    """⭐ A pack applies nothing and is never undone. Raising rather than
    silently no-op'ing means a caller who routes a pack through the change gate
    finds out immediately."""
    with pytest.raises(RuntimeError, match="not a proposal"):
        P._pack_apply(None, None, [])
    with pytest.raises(RuntimeError, match="superseded, never undone"):
        P._pack_undo(None, None, None)


def test_a_correction_supersedes_and_the_superseded_pack_stays_readable(company,
                                                                        published):
    """⭐ CORRECTIONS NEVER EDIT. What a board saw on the day it decided must
    remain readable exactly as it was."""
    before, hash_before = _frozen(published)
    with _db() as db:
        new = P.publish(db, company, "monthly", "2026-07-31",
                        supersedes_id=published,
                        supersession_reason="restated opening cash")
        db.commit()
        new_id, new_version = new.id, new.version
    with _db() as db:
        old = db.get(P.Pack, published)
        assert old.status == P.SUPERSEDED
        assert old.content_hash == hash_before, "the superseded pack was edited"
        assert P.frozen_inputs(db, old) == before, "its frozen set was rewritten"
        cur = db.get(P.Pack, new_id)
        assert cur.status == P.PUBLISHED
        assert cur.version == new_version == old.version + 1
        assert cur.supersedes_id == published
        assert cur.supersession_reason == "restated opening cash"


def test_a_superseding_pack_without_a_reason_is_refused(company, published):
    """⭐ A supersession without a stated reason is an edit with extra steps."""
    with _db() as db:
        with pytest.raises(ValueError, match="must state its reason"):
            P.publish(db, company, "monthly", "2026-07-31",
                      supersedes_id=published, supersession_reason="   ")


def test_publication_still_happens_when_inputs_are_missing():
    """⭐ ABSENCE PUBLISHES. Refusing to publish would convert an absence into a
    non-event — silent-empty wearing a publication's clothes."""
    with _db() as db:
        pk = P.publish(db, 999_999, "monthly", "2026-07-31")   # no such company
        db.commit()
        frozen = P.frozen_inputs(db, pk)
    assert pk.status == P.PUBLISHED
    assert frozen is not None
    absent = [k for k, v in frozen["classes"].items() if not v["present"]]
    assert len(absent) == len(P.INPUT_CLASSES) + len(P.DERIVED_CLASSES), \
        "a company with nothing must freeze every class as absent"
    for k in absent:
        assert frozen["classes"][k]["reason"]
