"""§4x Stage 2 — the READ endpoints, exercised over HTTP.

Riskiest-last: these expose no new capability. Every assertion goes through the
app rather than the service functions beneath it, because an endpoint that is
correct only because its service is correct is one refactor away from being
wrong.
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.accounts import (SessionLocal, Department, KpiPlan, User,
                                   make_token, _kpi_scope_key)
from services.api import accounts as A
from services.api.overrides import (
    DashboardSignoff, DepartmentAuthority, MetricOverride,
    grant_department, revoke_department, sign_off, create_override,
)

CO = 775005
ADMIN_UID, CFO_UID = 5001, 5002
KPI = "EBITDA margin %"


class U:
    def __init__(self, uid, staff=False):
        self.id = uid; self.is_staff = staff


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def env(client):
    s = SessionLocal()

    def _clean():
        for m in (DashboardSignoff, MetricOverride, DepartmentAuthority, KpiPlan, Department):
            s.query(m).filter_by(company_id=CO).delete()
        s.query(User).filter(User.email.like("sorx-%@t.local")).delete()
        s.commit()
    _clean()
    fin = Department(company_id=CO, dept_key="ep-fin", name="Finance and Accounting")
    hr = Department(company_id=CO, dept_key="ep-hr", name="Human Resources")
    s.add_all([fin, hr]); s.flush()
    ds = type("DS", (), {"id": 88804, "original_filename": "e.xlsx",
                         "uploaded_at": datetime(2026, 7, 1), "data": {},
                         "version": 1, "is_active": True})()
    real = A._active_company_dataset
    A._active_company_dataset = lambda db, cid: (ds if cid == CO else real(db, cid))
    s.add(KpiPlan(company_id=CO, dataset_id=ds.id, row_index=1, kpi_name=KPI,
                  unit="%", ytd_plan=20.0, ytd_actual=19.4, full_year_target=22.0,
                  department_id=fin.id, direction="higher_better"))
    s.commit()
    try:
        yield s, fin, hr
    finally:
        A._active_company_dataset = real
        _clean(); s.close()


def _staff_token(s):
    """A platform-super token: the only identity these tests can mint without a
    membership row, and enough to reach the admin-gated reads via the operator
    bypass."""
    u = s.query(User).filter_by(email="sorx-super@t.local").first()
    if u is None:
        u = User(email="sorx-super@t.local", name="Op", status="active",
                 platform_role="super", password_hash="x")
        s.add(u); s.commit()
    return make_token(str(u.id)), u


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


# ── the three states, over HTTP ──────────────────────────────────────────────

def test_signoff_endpoint_reports_vacant_unsigned_and_signed(env, client):
    """§7.6 across the wire. `vacant` and `unsigned` are both "no signature" and
    mean opposite things; a client must not have to infer the difference."""
    s, fin, hr = env
    tok, _ = _staff_token(s)

    r = client.get(f"/companies/{CO}/departments/{hr.id}/signoff", headers=_auth(tok))
    assert r.status_code == 200
    assert r.json()["state"] == "vacant"
    # ⭐ ACROSS THE WIRE, THE DISTINCTION IS CARRIED BY FIELDS, not by a phrase.
    # This pinned "not an unsigned dashboard"; the copy changed on 4 Aug because
    # the sentence also denied the department had a head while the page showed
    # one. `authority` and `state` are what a client reads.
    assert r.json()["authority"] in ("vacant", "never_assigned")
    assert r.json()["signed"] is False
    assert "sign-off authority" in r.json()["note"]
    # the head travels as its own field so no client parses the sentence
    assert "head_name" in r.json()

    grant_department(s, CO, fin.id, user_id=CFO_UID, granted_by=ADMIN_UID,
                     role_label="CFO"); s.commit()
    r = client.get(f"/companies/{CO}/departments/{fin.id}/signoff", headers=_auth(tok))
    assert r.json()["state"] == "unsigned" and r.json()["signed"] is False

    sign_off(s, CO, fin.id, user=U(CFO_UID), signer_label="J. Chen",
             now=datetime(2026, 3, 14)); s.commit()
    body = client.get(f"/companies/{CO}/departments/{fin.id}/signoff",
                      headers=_auth(tok)).json()
    assert body["state"] == "signed" and body["signed"] is True
    assert body["attestation"] == "Signed off by J. Chen, then CFO, 14 Mar 2026"


def test_signoff_endpoint_404s_on_a_foreign_department(env, client):
    """Company scoping enforced AT THE ROUTE, not left to the service."""
    s, fin, _ = env
    tok, _ = _staff_token(s)
    r = client.get(f"/companies/999999/departments/{fin.id}/signoff", headers=_auth(tok))
    assert r.status_code == 404


def test_read_endpoints_require_authentication(env, client):
    s, fin, _ = env
    for path in (f"/companies/{CO}/departments/{fin.id}/signoff",
                 f"/companies/{CO}/departments/{fin.id}/signoff/diff",
                 f"/companies/{CO}/departments/{fin.id}/authority",
                 f"/companies/{CO}/authority",
                 f"/companies/{CO}/overrides/audit"):
        assert client.get(path).status_code in (401, 403), path


# ── the diff, over HTTP ──────────────────────────────────────────────────────

def test_diff_endpoint_reports_unchanged_then_stale(env, client):
    s, fin, _ = env
    tok, _ = _staff_token(s)
    grant_department(s, CO, fin.id, user_id=CFO_UID, granted_by=ADMIN_UID); s.commit()
    sign_off(s, CO, fin.id, user=U(CFO_UID), signer_label="J. Chen"); s.commit()

    d = client.get(f"/companies/{CO}/departments/{fin.id}/signoff/diff",
                   headers=_auth(tok)).json()
    assert d["stale"] is False and d["own_unchanged"] is True

    kpi = s.query(KpiPlan).filter_by(company_id=CO, kpi_name=KPI).one()
    kpi.ytd_actual = 24.1; s.commit()

    d = client.get(f"/companies/{CO}/departments/{fin.id}/signoff/diff",
                   headers=_auth(tok)).json()
    assert d["stale"] is True and d["state"] == "needs_resignoff"
    assert d["own_unchanged"] is False
    ch = next(c for c in d["own_changes"] if c["label"] == KPI)
    assert ch["fields"]["display"] == {"before": 19.4, "after": 24.1}


def test_diff_endpoint_on_an_unsigned_department(env, client):
    s, fin, _ = env
    tok, _ = _staff_token(s)
    d = client.get(f"/companies/{CO}/departments/{fin.id}/signoff/diff",
                   headers=_auth(tok)).json()
    assert d["signed"] is False and d["state"] == "unsigned"


# ── grant listing ────────────────────────────────────────────────────────────

def test_authority_endpoint_lists_holders_and_history(env, client):
    """§7.4 — revocation never erases the record, and the endpoint says so."""
    s, fin, _ = env
    tok, _ = _staff_token(s)
    grant_department(s, CO, fin.id, user_id=CFO_UID, granted_by=ADMIN_UID,
                     role_label="CFO"); s.commit()
    body = client.get(f"/companies/{CO}/departments/{fin.id}/authority",
                      headers=_auth(tok)).json()
    assert body["state"]["state"] == "assigned"
    assert len(body["holders"]) == 1
    assert body["holders"][0]["role_label"] == "CFO"

    revoke_department(s, CO, fin.id, user_id=CFO_UID, revoked_by=ADMIN_UID,
                      reason="departed"); s.commit()
    body = client.get(f"/companies/{CO}/departments/{fin.id}/authority",
                      headers=_auth(tok)).json()
    assert body["state"]["state"] == "vacant"
    assert body["holders"] == []
    assert len(body["history"]) == 1, "the revoked grant is still on the record"
    assert body["history"][0]["active"] is False
    assert body["history"][0]["revoke_reason"] == "departed"


def test_company_authority_lists_departments_with_no_holder(env, client):
    """A vacancy must appear as a row, not as an omission — an absent row reads
    as 'nothing to see', the opposite of what a vacancy means."""
    s, fin, hr = env
    tok, _ = _staff_token(s)
    grant_department(s, CO, fin.id, user_id=CFO_UID, granted_by=ADMIN_UID); s.commit()
    body = client.get(f"/companies/{CO}/authority", headers=_auth(tok)).json()
    names = {d["department"]: d for d in body["departments"]}
    assert "Human Resources" in names, "a department with no holder was omitted"
    assert names["Human Resources"]["state"]["state"] == "never_assigned"
    assert names["Finance and Accounting"]["state"]["state"] == "assigned"


def test_audit_endpoint_includes_superseded_by_default(env, client):
    """An audit trail that shows only current state is not an audit trail."""
    s, fin, _ = env
    tok, _ = _staff_token(s)
    grant_department(s, CO, fin.id, user_id=CFO_UID, granted_by=ADMIN_UID); s.commit()
    create_override(s, CO, fin.id, user=U(CFO_UID), author_label="CFO — J. Chen",
                    metric_ref=_kpi_scope_key(fin.id, KPI), metric_label=KPI,
                    override_value=21.8, computed_value=19.4,
                    reason_category="data_error"); s.commit()
    create_override(s, CO, fin.id, user=U(CFO_UID), author_label="CFO — J. Chen",
                    metric_ref=_kpi_scope_key(fin.id, KPI), metric_label=KPI,
                    override_value=23.0, computed_value=19.4,
                    reason_category="data_error"); s.commit()

    body = client.get(f"/companies/{CO}/overrides/audit", headers=_auth(tok)).json()
    assert len(body["overrides"]) == 2
    assert [o["active"] for o in body["overrides"]] == [False, True]

    body = client.get(f"/companies/{CO}/overrides/audit?include_superseded=false",
                      headers=_auth(tok)).json()
    assert len(body["overrides"]) == 1


# ── no write path exists yet ─────────────────────────────────────────────────

def test_every_write_endpoint_is_authority_gated(env, client):
    """SUPERSEDED PREMISE. This asserted the read lane added no write endpoint —
    true then, meaningless now that the write lane is authorised. Replaced with
    the property that still matters: every write endpoint on this surface
    refuses an unauthenticated caller, so a new one cannot be added ungated
    without failing here.
    """
    paths = app.openapi().get("paths", {})
    writes = [(m.upper(), p) for p, ops in paths.items() for m in ops
              if m.upper() in ("POST", "PUT", "PATCH", "DELETE")
              and ("signoff" in p or "/overrides" in p or "/authority" in p)]
    assert writes, "no write endpoints found — the enumeration is not reaching them"
    for method, path in writes:
        url = path.replace("{company_id}", str(CO)).replace("{department_id}", "1")
        r = client.request(method, url, json={})
        assert r.status_code in (401, 403), f"{method} {url} -> {r.status_code}"
