"""Stage 2 sign-off — both directions, and the three states explicitly.

Sign-off is REVIEW THEN ATTEST, one act. These prove who may perform it, who may
not, and — the part that does not fall out of the model — that `vacant` and
`unsigned` are distinguishable at the data layer rather than collapsing into one
"no signature" boolean.
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.accounts import SessionLocal, Department, KpiPlan
from services.api import accounts as A
from services.api.overrides import (
    DashboardSignoff, DepartmentAuthority, MetricOverride, AuthorityError,
    grant_department, revoke_department, sign_off, signoff_state,
    active_signoff, signed_dashboard_state, state_digest, _attestation_line,
)

CO = 772002
ADMIN, CFO, CHRO = 8001, 8002, 8003


class U:
    def __init__(self, uid, staff=False):
        self.id = uid
        self.is_staff = staff


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def env(_app):
    s = SessionLocal()

    def _clean():
        for m in (DashboardSignoff, MetricOverride, DepartmentAuthority, KpiPlan, Department):
            s.query(m).filter_by(company_id=CO).delete()
        s.commit()
    _clean()
    fin = Department(company_id=CO, dept_key="so-fin", name="Finance and Accounting")
    hr = Department(company_id=CO, dept_key="so-hr", name="Human Resources")
    s.add_all([fin, hr]); s.flush()
    ds = type("DS", (), {"id": 88801, "original_filename": "so.xlsx",
                         "uploaded_at": datetime(2026, 7, 1), "data": {},
                         "version": 1, "is_active": True})()
    real = A._active_company_dataset
    A._active_company_dataset = lambda db, cid: (ds if cid == CO else real(db, cid))
    s.add_all([
        KpiPlan(company_id=CO, dataset_id=ds.id, row_index=1, kpi_name="EBITDA margin %",
                unit="%", ytd_plan=20.0, ytd_actual=19.4, full_year_target=22.0,
                department_id=fin.id, direction="higher_better"),
        KpiPlan(company_id=CO, dataset_id=ds.id, row_index=2, kpi_name="DSO days",
                unit="days", ytd_plan=45.0, ytd_actual=44.0, full_year_target=40.0,
                department_id=fin.id, direction="lower_better"),
    ])
    s.commit()
    try:
        yield s, fin, hr
    finally:
        A._active_company_dataset = real
        _clean(); s.close()


def _grant(s, dep, uid=CFO, role="CFO"):
    g = grant_department(s, CO, dep.id, user_id=uid, granted_by=ADMIN,
                         role_label=role)
    s.commit()
    return g


# ── DIRECTION 1: a granted CXO can sign their own department ─────────────────

def test_a_granted_cxo_can_sign_their_own_department(env):
    s, fin, _ = env
    _grant(s, fin)
    row = sign_off(s, CO, fin.id, user=U(CFO), signer_label="J. Chen"); s.commit()
    assert row.signer_user_id == CFO and row.signer_label == "J. Chen"
    assert row.signed_at is not None
    st = signoff_state(s, CO, fin.id)
    assert st["state"] == "signed" and st["signed"] is True


def test_the_attestation_is_a_board_visible_artifact(env):
    """WHO, and WHEN, in one line a board can read."""
    s, fin, _ = env
    _grant(s, fin)
    row = sign_off(s, CO, fin.id, user=U(CFO), signer_label="J. Chen",
                   now=datetime(2026, 3, 14)); s.commit()
    line = _attestation_line(row)
    assert line == "Signed off by J. Chen, then CFO, 14 Mar 2026"
    assert signoff_state(s, CO, fin.id)["attestation"] == line


def test_role_is_rendered_AS_IT_WAS_for_a_signer_since_moved(env):
    """§7.5. Without the 'then', a CEO wonders why the head of Operations signed
    HR's numbers — the attestation looks wrong precisely because the display is
    showing today's org chart against a historical act."""
    s, fin, hr = env
    _grant(s, hr, uid=CHRO, role="CHRO")
    row = sign_off(s, CO, hr.id, user=U(CHRO), signer_label="J. Chen",
                   now=datetime(2026, 3, 14)); s.commit()
    # The person later moves: grant revoked, re-granted elsewhere under a new role.
    revoke_department(s, CO, hr.id, user_id=CHRO, revoked_by=ADMIN,
                      reason="replaced"); s.commit()
    _grant(s, fin, uid=CHRO, role="COO")
    s.expire_all()
    again = s.query(DashboardSignoff).filter_by(company_id=CO, department_id=hr.id).one()
    assert "then CHRO" in _attestation_line(again), \
        "the signature must keep the role held AT SIGNING, not the current one"


# ── DIRECTION 2: refusals ────────────────────────────────────────────────────

def test_a_cxo_cannot_sign_a_department_they_hold_no_live_grant_on(env):
    s, fin, hr = env
    _grant(s, fin)
    with pytest.raises(AuthorityError, match="Not authorised to override"):
        sign_off(s, CO, hr.id, user=U(CFO), signer_label="J. Chen")


def test_a_revoked_cxo_can_no_longer_sign(env):
    """The grant must be LIVE, not merely to have existed."""
    s, fin, _ = env
    _grant(s, fin)
    sign_off(s, CO, fin.id, user=U(CFO), signer_label="J. Chen"); s.commit()
    revoke_department(s, CO, fin.id, user_id=CFO, revoked_by=ADMIN); s.commit()
    with pytest.raises(AuthorityError):
        sign_off(s, CO, fin.id, user=U(CFO), signer_label="J. Chen")


def test_an_admin_cannot_sign_at_all(env):
    """§7.1 spine: the admin decides who speaks for a department and can never
    speak for one. Signing is speaking for it."""
    s, fin, _ = env
    _grant(s, fin)                       # the admin ISSUED this grant
    with pytest.raises(AuthorityError, match="Not authorised to override"):
        sign_off(s, CO, fin.id, user=U(ADMIN), signer_label="Admin")


def test_platform_staff_cannot_sign(env):
    s, fin, _ = env
    _grant(s, fin)
    with pytest.raises(AuthorityError, match="Platform staff"):
        sign_off(s, CO, fin.id, user=U(CFO, staff=True), signer_label="Staff")


# ── ⭐ THE THREE STATES, at the data layer ───────────────────────────────────

def test_signed_unsigned_and_vacant_are_distinguishable_not_a_boolean(env):
    """§7.6, and the assertion the user asked for explicitly because this
    failure is SILENT and visually similar. `vacant` and `unsigned` are both
    "no signature"; rendering them identically converts an organisational gap
    into an apparent individual failure."""
    s, fin, hr = env

    # VACANT — no grant has ever existed.
    v = signoff_state(s, CO, hr.id)
    assert v["state"] == "vacant" and v["signed"] is False
    assert v["authority"] == "never_assigned"
    # ⭐ THE PROPERTY, NOT THE OLD WORDING. This pinned "no one to sign off",
    # which was half of the contradiction fixed 4 Aug: the sentence denied the
    # department had anybody while the page displayed its head. What must hold
    # is that the note distinguishes a MISSING GRANT from an UNSIGNED
    # dashboard, and that it never denies a head the surface is rendering.
    assert "sign-off authority" in v["note"]
    assert "yet" in v["note"].lower(), "a never-granted post must read as not-yet"
    # ⛔ AND IT MUST NOT DENY A HEAD. Both departments here are never_assigned,
    # so their notes are legitimately identical; vacant-vs-never_assigned is
    # asserted in test_authority_vs_head.py against a department that HAS a head.
    assert "No CXO is assigned to this department" not in v["note"]

    # UNSIGNED — assigned, but no signature yet.
    _grant(s, fin)
    u = signoff_state(s, CO, fin.id)
    assert u["state"] == "unsigned" and u["signed"] is False
    assert u["authority"] == "assigned"

    # SIGNED.
    sign_off(s, CO, fin.id, user=U(CFO), signer_label="J. Chen"); s.commit()
    g = signoff_state(s, CO, fin.id)
    assert g["state"] == "signed" and g["signed"] is True

    # The three are distinct VALUES, not one boolean plus inference.
    assert len({v["state"], u["state"], g["state"]}) == 3
    assert v["signed"] == u["signed"] is False, "a boolean alone cannot tell these apart"


def test_vacancy_after_revocation_reports_since_and_reason(env):
    s, fin, _ = env
    _grant(s, fin)
    revoke_department(s, CO, fin.id, user_id=CFO, revoked_by=ADMIN,
                      reason="departed"); s.commit()
    st = signoff_state(s, CO, fin.id)
    assert st["state"] == "vacant"
    assert st["since"] is not None and st["reason"] == "departed"


def test_a_signature_survives_the_signers_departure(env):
    """A vacancy does not un-sign what was already attested — §7.4 applied to
    signatures. The dashboard keeps its artifact and reports the vacancy
    separately."""
    s, fin, _ = env
    _grant(s, fin)
    sign_off(s, CO, fin.id, user=U(CFO), signer_label="J. Chen"); s.commit()
    revoke_department(s, CO, fin.id, user_id=CFO, revoked_by=ADMIN); s.commit()
    st = signoff_state(s, CO, fin.id)
    assert st["signed"] is True and st["signer"] == "J. Chen"
    assert st["authority"] == "vacant", "the department is vacant AND the signature stands"


# ── what the signature captures, so §8 can be built later ────────────────────

def test_the_signature_persists_the_displayed_values_not_only_a_digest(env):
    """⭐ THE FORWARD-COMPATIBILITY ASSERTION. A digest answers "something
    moved"; §8.3's re-sign-off diff must answer "these moved, by this much".
    Storing only a digest would make stage 4 unbuildable without a migration —
    and worse, without the PRE-CHANGE VALUES, which by then are unrecoverable
    because the whole point is that they changed."""
    s, fin, _ = env
    _grant(s, fin)
    row = sign_off(s, CO, fin.id, user=U(CFO), signer_label="J. Chen"); s.commit()

    metrics = row.signed_state["metrics"]
    assert len(metrics) == 2
    one = next(m for m in metrics.values() if m["metric"] == "EBITDA margin %")
    assert one["display"] == 19.4 and one["plan"] == 20.0
    assert one["variance"] == "unfavorable"
    assert one["adjusted"] is False
    assert row.state_digest and len(row.state_digest) == 64


def test_the_dependency_set_is_computed_from_the_resolver_not_hand_listed(env):
    """§8.2. A hand-maintained list is correct the day it is written and
    silently stale after the next panel is added — the defect class already
    recorded twice in this ledger."""
    import inspect
    from services.api import overrides as ov
    src = inspect.getsource(ov.signed_dashboard_state)
    assert "company_kpi_variance" in src, \
        "the signed set must come from the serializer the dashboard renders from"


def test_the_digest_is_order_stable(env):
    """A spurious invalidation is not harmless: §8.1's too-broad failure trains
    executives to click without reviewing, which destroys the feature more
    quietly than a bug would."""
    a = {"metrics": {"1": {"x": 1}, "2": {"y": 2}}, "dataset_id": 5}
    b = {"dataset_id": 5, "metrics": {"2": {"y": 2}, "1": {"x": 1}}}
    assert state_digest(a) == state_digest(b)


def test_an_override_makes_the_signature_signed_with_adjustments(env):
    """Derived from the state, never self-declared."""
    s, fin, _ = env
    _grant(s, fin)
    s.add(MetricOverride(
        company_id=CO, target_scope="department", department_id=fin.id,
        metric_ref=A._kpi_scope_key(fin.id, "EBITDA margin %"),
        metric_label="EBITDA margin %", override_value=21.8,
        computed_value_at_override=19.4, reason_category="data_error",
        author_user_id=CFO, author_label="CFO — J. Chen",
        created_at=datetime(2026, 7, 27)))
    s.commit()
    row = sign_off(s, CO, fin.id, user=U(CFO), signer_label="J. Chen"); s.commit()
    assert row.with_adjustments is True
    assert signoff_state(s, CO, fin.id)["state"] == "signed_with_adjustments"
    m = next(m for m in row.signed_state["metrics"].values()
             if m["metric"] == "EBITDA margin %")
    assert m["display"] == 21.8 and m["computed"] == 19.4
    assert m["adjusted_by"] == "CFO — J. Chen"
    assert "(with adjustments)" in signoff_state(s, CO, fin.id)["attestation"]


# ── supersession ─────────────────────────────────────────────────────────────

def test_re_signing_supersedes_rather_than_overwrites(env):
    s, fin, _ = env
    _grant(s, fin)
    first = sign_off(s, CO, fin.id, user=U(CFO), signer_label="J. Chen",
                     now=datetime(2026, 3, 14)); s.commit()
    second = sign_off(s, CO, fin.id, user=U(CFO), signer_label="J. Chen",
                      now=datetime(2026, 6, 1)); s.commit()
    s.expire_all()
    rows = s.query(DashboardSignoff).filter_by(company_id=CO, department_id=fin.id).all()
    assert len(rows) == 2, "the earlier attestation survives"
    old = s.get(DashboardSignoff, first.id)
    assert old.superseded_at is not None and old.superseded_by_id == second.id
    assert active_signoff(s, CO, fin.id).id == second.id
