"""§4x Stage 2 — the WRITE endpoints, over HTTP.

STANDING SHAPE, adopted this lane: every refusal is proven at the HTTP layer AND
paired with a control showing the service beneath would also have refused. Two
guards, both proven, so it is never ambiguous which did the work — and neither
can rot behind the other.
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.accounts import (SessionLocal, Department, KpiPlan, User,
                                   Membership, Account, CompanyAccess,
                                   make_token, _kpi_scope_key)
from services.api import accounts as A
from services.api.overrides import (
    DashboardSignoff, DepartmentAuthority, MetricOverride, AuthorityError,
    can_author, grant_department, revoke_department, grants_for, audit_rows,
)

CO = 776006
KPI = "EBITDA margin %"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _user(s, email, role=None):
    u = s.query(User).filter_by(email=email).first()
    if u is None:
        u = User(email=email, name=email.split("@")[0], status="active",
                 platform_role=role, password_hash="x")
        s.add(u); s.commit()
    return u


@pytest.fixture()
def env(client):
    s = SessionLocal()

    def _clean():
        for m in (DashboardSignoff, MetricOverride, DepartmentAuthority, KpiPlan, Department):
            s.query(m).filter_by(company_id=CO).delete()
        s.query(Membership).filter_by(company_id=CO).delete()
        s.query(CompanyAccess).filter_by(company_id=CO).delete()
        s.query(User).filter(User.email.like("wep-%@t.local")).delete()
        s.commit()
    _clean()
    fin = Department(company_id=CO, dept_key="wep-fin", name="Finance and Accounting")
    hr = Department(company_id=CO, dept_key="wep-hr", name="Human Resources")
    s.add_all([fin, hr]); s.flush()
    ds = type("DS", (), {"id": 88805, "original_filename": "w.xlsx",
                         "uploaded_at": datetime(2026, 7, 1), "data": {},
                         "version": 1, "is_active": True})()
    real = A._active_company_dataset
    A._active_company_dataset = lambda db, cid: (ds if cid == CO else real(db, cid))
    s.add(KpiPlan(company_id=CO, dataset_id=ds.id, row_index=1, kpi_name=KPI,
                  unit="%", ytd_plan=20.0, ytd_actual=19.4, full_year_target=22.0,
                  department_id=fin.id, direction="higher_better"))
    # CXO and ADMIN are ordinary company members; STAFF is platform-super.
    cxo = _user(s, "wep-cxo@t.local")
    adm = _user(s, "wep-admin@t.local")
    stf = _user(s, "wep-staff@t.local", role="super")
    for u, role in ((cxo, "admin"), (adm, "admin")):
        s.add(Membership(user_id=u.id, company_id=CO, role=role, status="active"))
    # require_company_admin runs _gate_account, which needs the company to be
    # provisioned — without this every write 404s on "not provisioned" and the
    # authority assertions below would pass for the wrong reason.
    acct = s.query(Account).filter_by(owner_user_id=adm.id).first()
    if acct is None:
        acct = Account(owner_user_id=adm.id, status="active", company_slots=5)
        s.add(acct); s.flush()
    s.add(CompanyAccess(company_id=CO, account_id=acct.id, cid=f"AX-T{CO}"[:16]))
    s.commit()
    try:
        yield s, fin, hr, cxo, adm, stf
    finally:
        A._active_company_dataset = real
        _clean(); s.close()


def _h(u):
    return {"Authorization": f"Bearer {make_token(str(u.id))}"}


def _ov_body(dep, **kw):
    b = dict(metric_ref=_kpi_scope_key(dep.id, KPI), metric_label=KPI,
             override_value=21.8, computed_value=19.4,
             reason_category="data_error", author_label="CFO — J. Chen")
    b.update(kw)
    return b


class _Svc:
    """Minimal stand-in for the service-layer control."""
    def __init__(self, uid, staff=False):
        self.id = uid; self.is_staff = staff


# ── PERMITS, over HTTP ───────────────────────────────────────────────────────

def test_a_granted_cxo_can_sign_and_override_over_http(env, client):
    s, fin, _, cxo, adm, _ = env
    grant_department(s, CO, fin.id, user_id=cxo.id, granted_by=adm.id,
                     role_label="CFO"); s.commit()

    r = client.post(f"/companies/{CO}/departments/{fin.id}/signoff",
                    json={"signer_label": "J. Chen"}, headers=_h(cxo))
    assert r.status_code == 201, r.text
    assert r.json()["state"] in ("signed", "signed_with_adjustments")

    r = client.post(f"/companies/{CO}/departments/{fin.id}/overrides",
                    json=_ov_body(fin), headers=_h(cxo))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["displayed"] == 21.8 and body["computed"] == 19.4
    assert body["author"] == "CFO — J. Chen"

    # The source row is untouched — the write is an overlay.
    kpi = s.query(KpiPlan).filter_by(company_id=CO, kpi_name=KPI).one()
    s.refresh(kpi)
    assert kpi.ytd_actual == 19.4


def test_withdraw_over_http_records_rather_than_deletes(env, client):
    s, fin, _, cxo, adm, _ = env
    grant_department(s, CO, fin.id, user_id=cxo.id, granted_by=adm.id); s.commit()
    client.post(f"/companies/{CO}/departments/{fin.id}/overrides",
                json=_ov_body(fin), headers=_h(cxo))
    r = client.post(f"/companies/{CO}/departments/{fin.id}/overrides/withdraw",
                    json={"metric_ref": _kpi_scope_key(fin.id, KPI),
                          "kind": "absorbed"}, headers=_h(cxo))
    assert r.status_code == 200 and r.json()["supersession_kind"] == "absorbed"
    rows = audit_rows(s, CO)
    assert len(rows) == 1 and rows[0]["active"] is False
    assert rows[0]["displayed_value"] == 21.8, "the retired figure stays on record"


def test_admin_can_grant_and_revoke_over_http(env, client):
    s, fin, _, cxo, adm, _ = env
    r = client.post(f"/companies/{CO}/departments/{fin.id}/authority",
                    json={"user_id": cxo.id, "role_label": "CFO"}, headers=_h(adm))
    assert r.status_code == 201 and r.json()["active"] is True
    r = client.post(f"/companies/{CO}/departments/{fin.id}/authority/revoke",
                    json={"user_id": cxo.id, "reason": "departed"}, headers=_h(adm))
    assert r.status_code == 200 and r.json()["active"] is False
    assert r.json()["revoke_reason"] == "departed"
    assert len(grants_for(s, CO, department_id=fin.id, include_revoked=True)) == 1


# ── THE FIVE REFUSAL DIRECTIONS — HTTP refusal + service control ─────────────

def test_1_no_live_grant(env, client):
    s, fin, _, cxo, _, _ = env
    r = client.post(f"/companies/{CO}/departments/{fin.id}/overrides",
                    json=_ov_body(fin), headers=_h(cxo))
    assert r.status_code == 403, "HTTP guard did not refuse"
    with pytest.raises(AuthorityError):
        can_author(s, CO, _Svc(cxo.id), "department", fin.id)   # service control


def test_2_revoked_grant(env, client):
    s, fin, _, cxo, adm, _ = env
    grant_department(s, CO, fin.id, user_id=cxo.id, granted_by=adm.id); s.commit()
    revoke_department(s, CO, fin.id, user_id=cxo.id, revoked_by=adm.id); s.commit()
    r = client.post(f"/companies/{CO}/departments/{fin.id}/signoff",
                    json={"signer_label": "J. Chen"}, headers=_h(cxo))
    assert r.status_code == 403
    with pytest.raises(AuthorityError):
        can_author(s, CO, _Svc(cxo.id), "department", fin.id)


def test_3_cross_department(env, client):
    """A CFO must not be able to override HR's numbers."""
    s, fin, hr, cxo, adm, _ = env
    grant_department(s, CO, fin.id, user_id=cxo.id, granted_by=adm.id); s.commit()
    r = client.post(f"/companies/{CO}/departments/{hr.id}/overrides",
                    json=_ov_body(hr), headers=_h(cxo))
    assert r.status_code == 403
    assert can_author(s, CO, _Svc(cxo.id), "department", fin.id) is True
    with pytest.raises(AuthorityError):
        can_author(s, CO, _Svc(cxo.id), "department", hr.id)


def test_4_admin_exercising_a_grant_they_issued(env, client):
    """§7.1 spine: the admin decides who speaks for a department and can never
    speak for one."""
    s, fin, _, cxo, adm, _ = env
    grant_department(s, CO, fin.id, user_id=cxo.id, granted_by=adm.id); s.commit()
    for path, body in ((f"/companies/{CO}/departments/{fin.id}/signoff",
                        {"signer_label": "Admin"}),
                       (f"/companies/{CO}/departments/{fin.id}/overrides",
                        _ov_body(fin))):
        assert client.post(path, json=body, headers=_h(adm)).status_code == 403
    with pytest.raises(AuthorityError):
        can_author(s, CO, _Svc(adm.id), "department", fin.id)


def test_5_platform_staff_cannot_author(env, client):
    s, fin, _, cxo, adm, stf = env
    grant_department(s, CO, fin.id, user_id=stf.id, granted_by=adm.id); s.commit()
    r = client.post(f"/companies/{CO}/departments/{fin.id}/overrides",
                    json=_ov_body(fin), headers=_h(stf))
    assert r.status_code == 403
    with pytest.raises(AuthorityError, match="Platform staff"):
        can_author(s, CO, _Svc(stf.id, staff=True), "department", fin.id)


def test_5b_platform_staff_cannot_GRANT(env, client):
    """The fifth direction from the authority stage, at the route. Being unable
    to author is worthless if we can grant ourselves authority a moment
    earlier — and require_company_admin gives us an operator bypass."""
    s, fin, _, cxo, _, stf = env
    r = client.post(f"/companies/{CO}/departments/{fin.id}/authority",
                    json={"user_id": cxo.id}, headers=_h(stf))
    assert r.status_code == 403, "platform staff issued a grant over HTTP"
    assert "Platform staff cannot" in r.json()["detail"]
    assert grants_for(s, CO, department_id=fin.id) == []


def test_5c_platform_staff_cannot_REVOKE(env, client):
    s, fin, _, cxo, adm, stf = env
    grant_department(s, CO, fin.id, user_id=cxo.id, granted_by=adm.id); s.commit()
    r = client.post(f"/companies/{CO}/departments/{fin.id}/authority/revoke",
                    json={"user_id": cxo.id}, headers=_h(stf))
    assert r.status_code == 403
    assert len(grants_for(s, CO, department_id=fin.id)) == 1, "the grant survived"


# ── content rules refused at the route ───────────────────────────────────────

def test_a_metric_outside_the_whitelist_is_refused_422(env, client):
    s, fin, _, cxo, adm, _ = env
    grant_department(s, CO, fin.id, user_id=cxo.id, granted_by=adm.id); s.commit()
    r = client.post(f"/companies/{CO}/departments/{fin.id}/overrides",
                    json=_ov_body(fin, metric_ref="diagnostic.kpi.revenue_growth"),
                    headers=_h(cxo))
    assert r.status_code == 422
    assert "not a resolver-covered metric" in r.json()["detail"]


def test_private_info_and_missing_reason_are_refused(env, client):
    s, fin, _, cxo, adm, _ = env
    grant_department(s, CO, fin.id, user_id=cxo.id, granted_by=adm.id); s.commit()
    for cat in ("private_info", None, "nonsense"):
        r = client.post(f"/companies/{CO}/departments/{fin.id}/overrides",
                        json=_ov_body(fin, reason_category=cat), headers=_h(cxo))
        assert r.status_code == 422, cat


def test_an_anonymous_signature_is_refused(env, client):
    s, fin, _, cxo, adm, _ = env
    grant_department(s, CO, fin.id, user_id=cxo.id, granted_by=adm.id); s.commit()
    r = client.post(f"/companies/{CO}/departments/{fin.id}/signoff",
                    json={"signer_label": "   "}, headers=_h(cxo))
    assert r.status_code == 422


def test_write_endpoints_require_authentication(env, client):
    s, fin, _, _, _, _ = env
    for path, body in (
        (f"/companies/{CO}/departments/{fin.id}/signoff", {"signer_label": "X"}),
        (f"/companies/{CO}/departments/{fin.id}/overrides", _ov_body(fin)),
        (f"/companies/{CO}/departments/{fin.id}/authority", {"user_id": 1}),
    ):
        assert client.post(path, json=body).status_code in (401, 403), path


def test_a_foreign_department_404s_at_the_route(env, client):
    s, fin, _, cxo, _, _ = env
    r = client.post(f"/companies/999999/departments/{fin.id}/signoff",
                    json={"signer_label": "X"}, headers=_h(cxo))
    assert r.status_code == 404


# ── the surface is exactly what was authorised ───────────────────────────────

def test_the_write_surface_is_exactly_the_five_authorised_endpoints(env, client):
    """Enumerated from app.openapi(), with the completeness control the vacuous
    version lacked."""
    paths = app.openapi().get("paths", {})
    assert len(paths) > 100, "enumeration narrowed — this guard would pass vacuously"
    writes = sorted(f"{m.upper()} {p}" for p, ops in paths.items() for m in ops
                    if m.upper() in ("POST", "PUT", "PATCH", "DELETE")
                    and ("signoff" in p or "/overrides" in p
                         or p.endswith("/authority") or p.endswith("/authority/revoke")))
    assert writes == [
        "POST /companies/{company_id}/departments/{department_id}/authority",
        "POST /companies/{company_id}/departments/{department_id}/authority/revoke",
        "POST /companies/{company_id}/departments/{department_id}/overrides",
        "POST /companies/{company_id}/departments/{department_id}/overrides/withdraw",
        "POST /companies/{company_id}/departments/{department_id}/signoff",
    ], writes
