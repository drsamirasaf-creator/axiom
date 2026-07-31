"""Admin ranking, succession, the revoke gap, and accountable platform access.

⭐⭐ MEASURED AT `cc88e9d`: nothing distinguished one admin from another, ALL SIX
live companies held exactly ONE active admin, and `revoke` could not touch an
admin row. For the client, lockout was total.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest
from fastapi import HTTPException

from services.api import succession as S


class _M:
    def __init__(self, i, uid, rank=None, role="admin", status="active", cid=1):
        self.id, self.user_id, self.admin_rank = i, uid, rank
        self.role, self.status, self.company_id = role, status, cid


class _U:
    def __init__(self, i, pr="user"):
        self.id, self.platform_role, self.name, self.email = i, pr, f"u{i}", f"u{i}@x"


class _DB:
    def __init__(self, rows):
        self.rows, self.added, self.audits = rows, [], []

    def query(self, _m):
        return self

    def filter_by(self, **kw):
        self._f = kw
        return self

    def all(self):
        return [r for r in self.rows
                if all(getattr(r, k, None) == v for k, v in self._f.items())]

    def first(self):
        r = self.all()
        return r[0] if r else None

    def get(self, _m, i):
        return next((r for r in self.rows if getattr(r, "id", None) == i), None)

    def add(self, o):
        self.added.append(o); self.rows.append(o)

    def flush(self):
        pass


@pytest.fixture(autouse=True)
def _no_audit(monkeypatch):
    import services.api.accounts as A
    monkeypatch.setattr(A, "audit", lambda *a, **k: None)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ RANKING
# ═══════════════════════════════════════════════════════════════════════════

def test_ranked_admins_orders_primary_first_and_UNRANKED_LAST():
    """⭐⭐ UNRANKED IS NOT "LAST IN LINE". Every admin predating this feature is
    unranked, and calling one of them "next" asserts a client decision nobody
    made."""
    db = _DB([_M(1, 10, None), _M(2, 11, 1), _M(3, 12, 0)])
    order = [m.user_id for m in S.ranked_admins(db, 1)]
    assert order == [12, 11, 10]
    assert S.primary_admin(db, 1).user_id == 12


def test_successor_REFUSES_to_fall_back_to_an_unranked_admin():
    """⭐ A succession that guesses is the behaviour transfer_admin refuses."""
    db = _DB([_M(1, 10, 0), _M(2, 11, None)])
    assert S.successor(db, 1, excluding_user_id=10) is None


def test_ranking_is_not_a_GRANT():
    """⭐ Conflating ordering with granting would make an ordering call a
    privilege escalation."""
    db = _DB([_M(1, 10, None)])
    with pytest.raises(HTTPException) as e:
        S.set_ranks(db, 1, [10, 99], actor=_U(10))
    assert e.value.status_code == 422


def test_admins_left_out_of_an_order_become_UNRANKED_not_appended():
    db = _DB([_M(1, 10, 0), _M(2, 11, 1), _M(3, 12, 2)])
    S.set_ranks(db, 1, [11, 10], actor=_U(10))
    by = {m.user_id: m.admin_rank for m in db.rows}
    assert by == {11: 0, 10: 1, 12: None}


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ SUCCESSION WITHOUT AXIOM
# ═══════════════════════════════════════════════════════════════════════════

def test_a_client_can_promote_a_deputy_with_no_support_involvement():
    db = _DB([_M(1, 10, 0), _M(2, 11, 1)])
    out = S.step_down(db, 1, actor=_U(10))
    assert out["new_primary_user_id"] == 11
    assert db.rows[1].admin_rank == S.PRIMARY
    assert db.rows[0].role == "viewer" and db.rows[0].admin_rank is None


def test_stepping_down_REFUSES_to_leave_a_company_with_no_admin():
    """⭐⭐ THE ONE OUTCOME NO CLIENT CAN UNDO."""
    db = _DB([_M(1, 10, 0)])
    with pytest.raises(HTTPException) as e:
        S.step_down(db, 1, actor=_U(10))
    assert e.value.status_code == 409


def test_stepping_down_with_no_ranked_deputy_REFUSES_rather_than_guessing():
    db = _DB([_M(1, 10, 0), _M(2, 11, None)])
    with pytest.raises(HTTPException) as e:
        S.step_down(db, 1, actor=_U(10))
    assert e.value.status_code == 409
    assert "refusing to choose" in e.value.detail


def test_you_cannot_promote_a_NON_admin_by_stepping_down():
    """⭐ Promoting a non-admin is a GRANT — a different act with a different
    authority."""
    db = _DB([_M(1, 10, 0), _M(2, 11, 1)])
    with pytest.raises(HTTPException) as e:
        S.step_down(db, 1, actor=_U(10), to_user_id=99)
    assert e.value.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE REVOKE GAP
# ═══════════════════════════════════════════════════════════════════════════

def test_an_admin_CAN_now_be_revoked():
    """⭐ `revoke` reads _get_viewer_row and cannot touch an admin — half of why
    lockout was total."""
    db = _DB([_M(1, 10, 0), _M(2, 11, 1)])
    out = S.revoke_admin(db, 1, 2, actor=_U(10))
    assert out["status"] == "revoked"
    assert db.rows[1].admin_rank is None


def test_the_LAST_admin_cannot_be_revoked_by_anyone():
    db = _DB([_M(1, 10, 0)])
    with pytest.raises(HTTPException) as e:
        S.revoke_admin(db, 1, 1, actor=_U(10))
    assert e.value.status_code == 409
    assert "lock the company out" in e.value.detail


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ SUPPORT GRANT — ROLES, NEVER DATA
# ═══════════════════════════════════════════════════════════════════════════

def test_support_grant_requires_platform_staff():
    db = _DB([])
    with pytest.raises(HTTPException) as e:
        S.support_grant_admin(db, 1, 11, actor=_U(10), reason="x")
    assert e.value.status_code == 403


def test_support_grant_REQUIRES_A_REASON():
    """⭐ An unexplained support grant is indistinguishable from an unauthorised
    one after the fact."""
    db = _DB([_U(11)])
    with pytest.raises(HTTPException) as e:
        S.support_grant_admin(db, 1, 11, actor=_U(1, "super"), reason="  ")
    assert e.value.status_code == 422


def test_support_grant_does_NOT_set_a_rank():
    """⭐ Support restores ACCESS; the client decides ORDER."""
    db = _DB([_U(11)])
    out = S.support_grant_admin(db, 1, 11, actor=_U(1, "super"),
                                reason="admin left the business")
    assert out["granted"] is True
    assert db.added[0].admin_rank is None
    assert db.added[0].role == "admin"


def test_there_is_NO_credential_reset_anywhere_in_this_module():
    """⭐⭐ Handing over a password would let one person continue another's
    authored history. The models denormalise actor_label precisely so a new
    admin inherits AUTHORITY without inheriting an IDENTITY.

    ⭐ NARROWED: the first version banned the WORD "credential" and failed on the
    module's own client-facing reassurance ("no credentials were changed"). A
    guard that forbids the word rather than the CAPABILITY punishes saying the
    right thing. It now looks for credential MUTATION.
    """
    import ast

    from tests.codeonly import code_only
    src = code_only(S)
    tree = ast.parse(src)
    banned_calls = {"set_password", "hash_password", "make_reset_token",
                    "send_password_reset", "issue_token"}
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            name = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
            assert name not in banned_calls, f"the module calls {name}"
        if isinstance(n, ast.Attribute) and isinstance(n.ctx, ast.Store):
            assert n.attr not in ("password_hash", "password", "oauth_provider"), \
                f"the module assigns {n.attr}"


def test_the_verification_split_is_RECORDED_not_assumed():
    """⭐⭐ The capability is a way into an account, so SOCIAL ENGINEERING is the
    attack — and no code can tell a genuine request from a convincing one."""
    assert len(S.VERIFICATION_ENFORCED) >= 4
    assert len(S.VERIFICATION_PROCEDURAL) >= 3
    joined = " ".join(S.VERIFICATION_PROCEDURAL).lower()
    assert "who they claim to be" in joined


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ PLATFORM ACCESS IS MARKED AND VISIBLE
# ═══════════════════════════════════════════════════════════════════════════

def test_the_bypass_marks_the_act_at_its_own_site():
    import inspect

    from services.api import accounts as A
    src = inspect.getsource(A._operator_bypass_ok)
    assert "_mark_platform_access" in src, \
        "the bypass does not mark the act; an endpoint that forgot would produce " \
        "an audit row indistinguishable from a client admin's"


def test_marking_can_never_break_the_act_it_marks():
    import inspect

    from services.api import accounts as A
    src = inspect.getsource(A._mark_platform_access)
    assert "except Exception" in src, \
        "a marking failure would turn an audit gap into an outage"


def test_the_client_surface_reports_platform_access():
    import inspect

    from services.api import accounts as A
    src = inspect.getsource(A.list_admins)
    assert "platform_access" in src
    assert "PLATFORM_BYPASS_ACTION" in src
    assert "never reads your" in src, "the client is not told what support cannot do"


def test_the_pilot_asymmetry_is_RULED_not_left_as_an_omission():
    """⭐⭐ transfer_admin's staff check does not consult _pilot_transferred_away.
    That was an omission left in place because it happened to be useful; it is
    now a recovery path on purpose."""
    import inspect

    from services.api import accounts as A
    src = inspect.getsource(A.transfer_admin)
    assert "SURVIVES A PILOT" in src or "survives a pilot" in src.lower()
    assert "OMISSION LEFT IN PLACE" in src
    assert "_mark_platform_access" in src


def test_admin_rank_is_nullable_with_no_default():
    """⭐ A default of 0 would silently make every existing admin a primary."""
    from services.api.accounts import Membership
    c = Membership.__table__.c.admin_rank
    assert c.nullable is True and c.default is None and c.server_default is None


def test_the_ax_table_column_uses_the_runtime_bootstrap_not_alembic():
    """⭐ ax_* tables belong to accounts.Base — create_all plus _add(). This seam
    has produced eight bugs."""
    src = open("services/api/accounts.py", encoding="utf-8").read()
    assert '_add("ax_memberships", "admin_rank", "admin_rank INTEGER")' in src
