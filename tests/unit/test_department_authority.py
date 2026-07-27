"""Stage 2 authority — proven BEHAVIOURALLY in all four directions.

Per the standing principle: a guard is only proven by attempting what it forbids
AND by showing it permits what it must permit. A guard tested only where it
refuses is untested; so is one tested only where it allows. Both directions, and
the refusals are exercised through can_author() against real grant rows rather
than asserted from the model.
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.accounts import SessionLocal, Department, Base
from services.api.overrides import (
    DepartmentAuthority, MetricOverride, can_author, AuthorityError, GrantError,
    grant_department, revoke_department, grants_for, department_state,
    department_authority,
)

CO = 771001
ADMIN, CFO, CHRO = 9001, 9002, 9003


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
        s.query(MetricOverride).filter_by(company_id=CO).delete()
        s.query(DepartmentAuthority).filter_by(company_id=CO).delete()
        s.query(Department).filter_by(company_id=CO).delete()
        s.commit()
    _clean()
    fin = Department(company_id=CO, dept_key="auth-fin", name="Finance and Accounting")
    hr = Department(company_id=CO, dept_key="auth-hr", name="Human Resources")
    s.add_all([fin, hr]); s.commit()
    try:
        yield s, fin, hr
    finally:
        _clean(); s.close()


# ── the slot Stage 1 left open ───────────────────────────────────────────────

def test_stage_1_fail_closed_default_is_now_a_real_lookup(_app):
    """Stage 1's department_authority() reads Base._department_authority_model
    and returned False for everyone because it was absent. The model now fills
    that slot — without Stage 1's function changing."""
    assert getattr(Base, "_department_authority_model", None) is DepartmentAuthority


def test_no_grant_still_means_no_authority(env):
    """The fail-closed default survives the model existing."""
    s, fin, _ = env
    assert department_authority(s, CO, CFO, fin.id) is False


# ── DIRECTION 1: permits a validly granted CXO on their own department ───────

def test_permits_a_granted_cxo_on_their_own_department(env):
    s, fin, _ = env
    grant_department(s, CO, fin.id, user_id=CFO, granted_by=ADMIN,
                     role_label="CFO"); s.commit()
    assert department_authority(s, CO, CFO, fin.id) is True
    assert can_author(s, CO, U(CFO), "department", fin.id) is True


# ── DIRECTION 2: refuses cross-department authoring ──────────────────────────

def test_refuses_cross_department_authoring(env):
    """A CFO must not be able to override HR's numbers. The requirement the §4l
    spec omitted entirely, and the one most likely to be discovered by a
    customer rather than by us."""
    s, fin, hr = env
    grant_department(s, CO, fin.id, user_id=CFO, granted_by=ADMIN); s.commit()
    assert can_author(s, CO, U(CFO), "department", fin.id) is True
    with pytest.raises(AuthorityError, match="Not authorised to override"):
        can_author(s, CO, U(CFO), "department", hr.id)


def test_holding_two_departments_is_two_rows_and_revoking_one_leaves_the_other(env):
    """§7.3. Automatic once grants are rows; would have needed special-casing
    under a role field."""
    s, fin, hr = env
    grant_department(s, CO, fin.id, user_id=CFO, granted_by=ADMIN)
    grant_department(s, CO, hr.id, user_id=CFO, granted_by=ADMIN); s.commit()
    assert len(grants_for(s, CO, user_id=CFO)) == 2

    revoke_department(s, CO, hr.id, user_id=CFO, revoked_by=ADMIN); s.commit()
    assert can_author(s, CO, U(CFO), "department", fin.id) is True, "the other grant is undisturbed"
    with pytest.raises(AuthorityError):
        can_author(s, CO, U(CFO), "department", hr.id)


# ── DIRECTION 3: refuses the company admin exercising a grant they can ISSUE ─

def test_refuses_the_admin_who_issued_the_grant_from_exercising_it(env):
    """§7.1 — the spine of the feature. The admin decides who speaks for a
    department and can never speak for one. Otherwise 'the CFO's owned number'
    is unfalsifiable, because an admin could have written it."""
    s, fin, _ = env
    grant_department(s, CO, fin.id, user_id=CFO, granted_by=ADMIN); s.commit()
    # The admin issued that grant. It buys them nothing.
    with pytest.raises(AuthorityError, match="Not authorised to override"):
        can_author(s, CO, U(ADMIN), "department", fin.id)


def test_granting_to_oneself_still_does_not_help_an_admin_without_a_grant(env):
    """The rule is enforced by the absence of a grant ROW, not by comparing the
    actor to granted_by — so an admin cannot escape it by routing around who
    issued what."""
    s, fin, _ = env
    with pytest.raises(AuthorityError):
        can_author(s, CO, U(ADMIN), "department", fin.id)


# ── DIRECTION 4: refuses platform staff entirely ─────────────────────────────

def test_refuses_platform_staff_from_authoring(env):
    """Explicit carve-out: require_company_admin grants operator bypass
    everywhere else. We must never be able to author a customer's signed board
    figure — that would be indefensible if discovered, whatever the intent."""
    s, fin, _ = env
    grant_department(s, CO, fin.id, user_id=CFO, granted_by=ADMIN); s.commit()
    with pytest.raises(AuthorityError, match="Platform staff"):
        can_author(s, CO, U(CFO, staff=True), "department", fin.id)


def test_refuses_platform_staff_from_GRANTING_too(env):
    """Being unable to author is worthless if we can grant ourselves authority a
    moment earlier. The exclusion has to hold at both steps."""
    s, fin, _ = env
    with pytest.raises(GrantError, match="Platform staff cannot issue"):
        grant_department(s, CO, fin.id, user_id=CFO, granted_by=ADMIN,
                         actor=U(ADMIN, staff=True))


# ── §7.4: REVOCATION NEVER TOUCHES HISTORY — byte-identical ──────────────────

def test_revocation_leaves_prior_overrides_byte_identical(env):
    """⭐ The worst possible defect on this feature would be a revocation that
    cascaded into historical attestations. A board figure that LOSES its
    attester is worse than one that never had an attester: the first reads as
    covered-up authorship, the second merely as unsigned.

    Asserted behaviourally — perform the revocation and compare the rows — not
    by observing that no cascade is declared."""
    s, fin, _ = env
    grant_department(s, CO, fin.id, user_id=CFO, granted_by=ADMIN,
                     role_label="CFO"); s.commit()
    o = MetricOverride(
        company_id=CO, target_scope="department", department_id=fin.id,
        metric_ref=f"{fin.id}|ebitda margin %", metric_label="EBITDA margin %",
        override_value=21.8, computed_value_at_override=19.4,
        reason_category="data_error", reason_note="miscoded at source",
        author_user_id=CFO, author_label="CFO — J. Chen",
        created_at=datetime(2026, 7, 27))
    s.add(o); s.commit()

    FIELDS = ("company_id", "target_scope", "department_id", "metric_ref",
              "metric_label", "override_value", "computed_value_at_override",
              "reason_category", "reason_note", "author_user_id", "author_label",
              "created_at", "superseded_at", "superseded_by_id", "supersession_kind")
    before = {f: getattr(o, f) for f in FIELDS}

    revoke_department(s, CO, fin.id, user_id=CFO, revoked_by=ADMIN,
                      reason="departed"); s.commit()
    s.expire_all()

    after_row = s.query(MetricOverride).filter_by(company_id=CO).one()
    after = {f: getattr(after_row, f) for f in FIELDS}
    assert after == before, "revocation mutated a historical override"
    assert after["author_label"] == "CFO — J. Chen", \
        "the departed executive's frozen label must survive verbatim"

    # And the person can no longer author, which is the point of revoking.
    with pytest.raises(AuthorityError):
        can_author(s, CO, U(CFO), "department", fin.id)


def test_revocation_is_a_timestamp_not_a_deletion(env):
    """§7.2. The row survives, carrying who revoked it and why."""
    s, fin, _ = env
    grant_department(s, CO, fin.id, user_id=CFO, granted_by=ADMIN); s.commit()
    revoke_department(s, CO, fin.id, user_id=CFO, revoked_by=ADMIN,
                      reason="replaced"); s.commit()

    live = grants_for(s, CO, department_id=fin.id)
    allr = grants_for(s, CO, department_id=fin.id, include_revoked=True)
    assert live == [] and len(allr) == 1
    assert allr[0].revoked_at is not None
    assert allr[0].revoked_by == ADMIN and allr[0].revoke_reason == "replaced"
    assert allr[0].granted_by == ADMIN, "who issued it is still on the record"


def test_a_regrant_after_revocation_is_a_new_row_not_a_resurrection(env):
    """Each grant is a distinct historical fact. Deliberately no unique
    constraint on (company, user, department) — that would forbid the history."""
    s, fin, _ = env
    grant_department(s, CO, fin.id, user_id=CFO, granted_by=ADMIN); s.commit()
    revoke_department(s, CO, fin.id, user_id=CFO, revoked_by=ADMIN); s.commit()
    grant_department(s, CO, fin.id, user_id=CFO, granted_by=ADMIN); s.commit()
    assert len(grants_for(s, CO, department_id=fin.id, include_revoked=True)) == 2
    assert len(grants_for(s, CO, department_id=fin.id)) == 1
    assert can_author(s, CO, U(CFO), "department", fin.id) is True


# ── §7.6: vacancy vs never-assigned vs assigned ──────────────────────────────

def test_vacant_and_never_assigned_are_different_states(env):
    """§7.6 — and the same three-state discipline as the suppression reasons and
    the CEI cards: absence is never one state. A department nobody has ever been
    accountable for is not a department whose CXO just left."""
    s, fin, hr = env
    assert department_state(s, CO, hr.id)["state"] == "never_assigned"

    grant_department(s, CO, fin.id, user_id=CFO, granted_by=ADMIN); s.commit()
    assert department_state(s, CO, fin.id)["state"] == "assigned"

    revoke_department(s, CO, fin.id, user_id=CFO, revoked_by=ADMIN,
                      reason="departed"); s.commit()
    st = department_state(s, CO, fin.id)
    assert st["state"] == "vacant"
    assert st["since"] is not None and st["reason"] == "departed"


def test_no_admin_signoff_ever_is_expressible_from_the_state(env):
    """§7.6: authority does NOT revert to the admin on vacancy. Nothing in the
    vacant state names a fallback holder, so there is no one for a UI to offer."""
    s, fin, _ = env
    grant_department(s, CO, fin.id, user_id=CFO, granted_by=ADMIN); s.commit()
    revoke_department(s, CO, fin.id, user_id=CFO, revoked_by=ADMIN); s.commit()
    st = department_state(s, CO, fin.id)
    assert st["holders"] == 0 and "user_ids" not in st
    with pytest.raises(AuthorityError):
        can_author(s, CO, U(ADMIN), "department", fin.id)


# ── grant hygiene ────────────────────────────────────────────────────────────

def test_cannot_grant_a_department_belonging_to_another_company(env):
    s, fin, _ = env
    with pytest.raises(GrantError, match="does not belong to this company"):
        grant_department(s, 999999, fin.id, user_id=CFO, granted_by=ADMIN)


def test_regranting_a_live_grant_is_idempotent(env):
    s, fin, _ = env
    a = grant_department(s, CO, fin.id, user_id=CFO, granted_by=ADMIN); s.commit()
    b = grant_department(s, CO, fin.id, user_id=CFO, granted_by=ADMIN); s.commit()
    assert a.id == b.id
    assert len(grants_for(s, CO, department_id=fin.id)) == 1


def test_revoking_nothing_refuses_rather_than_silently_succeeding(env):
    s, fin, _ = env
    with pytest.raises(GrantError, match="No live grant"):
        revoke_department(s, CO, fin.id, user_id=CFO, revoked_by=ADMIN)


def test_role_label_is_frozen_at_grant_time(env):
    """§7.5: display renders the role AS IT WAS — 'Signed off by J. Chen, then
    CHRO'. Without it a CEO wonders why the head of Operations signed HR's
    numbers. Same reason author_label is frozen text on an override."""
    s, fin, _ = env
    g = grant_department(s, CO, fin.id, user_id=CHRO, granted_by=ADMIN,
                         role_label="CHRO"); s.commit()
    assert g.role_label == "CHRO"
    assert DepartmentAuthority.__table__.columns["role_label"].nullable is True
