"""§7e behavioural proof — a NON-ADMIN LEADER actually reaches the three writes.

⭐⭐ WHY THIS EXISTS AND THE BROWSER PROOF DOES NOT COVER IT. The dev server talks
to the DEPLOYED backend, so a browser run measures the code that is live, not the
code in this working tree. It establishes the admin read path is intact and
nothing more. ⛔ THE CLAIM OF THIS LANE — "a leader may now edit milestones,
actions and blockers" — is only provable by a request through THIS app object.

⭐ AND IT IS THE PRODUCTION PATH, NOT A REIMPLEMENTATION. The requests go through
the real router and the real dependency, so a resolver that silently stopped being
consulted would fail here; calling `_leader_or_admin` directly would only measure
my own restatement of the wiring.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="leadwrite-", suffix=".db"))

import pytest
from fastapi.testclient import TestClient

from services.api.accounts import (Initiative, InitiativeAssignment, Membership,
                                   SessionLocal, User, make_token)
from services.api.main import app
from services.api.modules.enterprise_state.models import Enterprise

CID = 910011


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _seat(db, email, platform_role="user"):
    """⭐ `ax_users`, NOT `users`. They are two tables with 16 and 11 rows and no
    1:1 mapping — `/auth/register` writes the identity table, and
    `get_current_user` resolves `sub` against THIS one. A fixture that registered
    got a token whose subject did not exist here."""
    u = db.query(User).filter_by(email=email).first()
    if u is None:
        u = User(email=email, name=email.split("@")[0], status="active",
                 platform_role=platform_role)
        db.add(u)
        db.flush()
    return u


@pytest.fixture(scope="module")
def world(client):
    """One company · one initiative · an admin, an active leader, and a bystander.

    ⭐ THE BYSTANDER IS THE POINT. Without a member who is neither admin nor
    leader, "the leader may write" is indistinguishable from "anyone may write".
    """
    db = SessionLocal()
    if db.get(Enterprise, CID) is None:
        db.add(Enterprise(id=CID, tenant="t-7e-fixture", name="§7e Fixture Co"))
    ids, toks = {}, {}
    for k in ("admin", "leader", "bystander"):
        u = _seat(db, f"{k}-7e@example.test")
        ids[k] = u.id
        toks[k] = make_token(str(u.id), "access")
        if not db.query(Membership).filter_by(user_id=u.id, company_id=CID).first():
            db.add(Membership(user_id=u.id, company_id=CID,
                              role="admin" if k == "admin" else "viewer",
                              status="active"))
    ini = db.query(Initiative).filter_by(company_id=CID, ref_code="L1").first()
    if ini is None:
        ini = Initiative(company_id=CID, ref_code="L1", title="Leader-writable",
                         status="active", importance=3, urgency=3,
                         current_priority="A", created_by=ids["admin"])
        db.add(ini)
        db.flush()
    if not db.query(InitiativeAssignment).filter_by(initiative_id=ini.id).first():
        db.add(InitiativeAssignment(
            initiative_id=ini.id, company_id=CID, leader_user_id=ids["leader"],
            invited_email="leader-7e@example.test", invited_name="Leader",
            status="active", jti="jti-7e-fixture"))
    db.commit()
    out = {"iid": ini.id, "ids": ids, "toks": toks}
    db.close()
    return out


def _h(world, who):
    return {"Authorization": f"Bearer {world['toks'][who]}"}


def _url(world, tail):
    return f"/companies/{CID}/initiatives/{world['iid']}/{tail}"


BODIES = {
    # ⭐ A NEW MILESTONE MUST CARRY ITS ACCEPTANCE CRITERION — the §4z.4 rule,
    # which correctly refused a fixture that tried `predates_criterion` instead.
    # That flag is for rows that pre-date the rule, not a way around it.
    "milestones": {"milestones": [{"title": "M1", "target_date": "2026-09-30",
                                   "criterion": "Signed off by the sponsor"}]},
    "actions": {"actions": [{"title": "A1"}]},
    "blockers": {"blockers": [{"title": "B1"}]},
}


@pytest.mark.parametrize("tail", list(BODIES))
def test_the_leader_may_write_all_three(client, world, tail):
    """⭐⭐ THE CLAIM OF THIS LANE. Before it, each of these was 403 for a leader."""
    r = client.put(_url(world, tail), json=BODIES[tail], headers=_h(world, "leader"))
    assert r.status_code == 200, f"{tail}: leader refused — {r.status_code} {r.text[:200]}"


@pytest.mark.parametrize("tail", list(BODIES))
def test_the_admin_still_may(client, world, tail):
    """⛔ THE REGRESSION THE SWAP RISKED. Widening a gate must not narrow it."""
    r = client.put(_url(world, tail), json=BODIES[tail], headers=_h(world, "admin"))
    assert r.status_code == 200, f"{tail}: admin refused — {r.status_code} {r.text[:200]}"


@pytest.mark.parametrize("tail", list(BODIES))
def test_a_plain_member_still_may_not(client, world, tail):
    """⭐⭐ THE KNOWN-NEGATIVE. If these passed, the three tests above would be
    proving that authentication alone is sufficient — which is not a grant."""
    r = client.put(_url(world, tail), json=BODIES[tail], headers=_h(world, "bystander"))
    assert r.status_code == 403, f"{tail}: a non-leader wrote — {r.status_code}"


def test_the_grant_does_not_reach_a_second_initiative(client, world):
    """⭐⭐ PER-INITIATIVE IS THE RULING, AND THIS IS WHERE IT IS PROVED. A leader
    who could edit any initiative in the company would be a weaker admin."""
    db = SessionLocal()
    other = db.query(Initiative).filter_by(company_id=CID, ref_code="L2").first()
    admin_id = world["ids"]["admin"]
    if other is None:
        other = Initiative(company_id=CID, ref_code="L2", title="Not theirs",
                           status="active", importance=3, urgency=3,
                           current_priority="A", created_by=admin_id)
        db.add(other)
        db.commit()
    oid = other.id
    db.close()
    r = client.put(f"/companies/{CID}/initiatives/{oid}/actions",
                   json=BODIES["actions"], headers=_h(world, "leader"))
    assert r.status_code == 403, \
        f"the leader reached an initiative they do not lead — {r.status_code}"


# ── the standalone revoke, end to end ─────────────────────────────────────

def test_a_leader_steps_down_and_the_initiative_is_left_vacant(client, world):
    """⭐⭐ THE STATE THAT WAS PREVIOUSLY UNRECORDABLE. `reassign-leader` demanded
    a successor, so a company whose leader left had to invite a placeholder."""
    r = client.post(_url(world, "revoke-leader"), json={"note": "stepping down"},
                    headers=_h(world, "leader"))
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["vacant"] is True and b["leader"] is None
    assert b["stepped_down"] is True, "a self-revoke was not recorded as one"

    db = SessionLocal()
    row = (db.query(InitiativeAssignment)
             .filter_by(initiative_id=world["iid"]).order_by(
                 InitiativeAssignment.id.desc()).first())
    # ⭐ §4v.1 — the row survives, carrying who ended it and when.
    assert row.status == "revoked" and row.revoked_at is not None
    assert row.revoked_by == world["ids"]["leader"], "the actor was not stamped"
    # ⛔ AND NO SUCCESSOR WAS MINTED.
    live = db.query(InitiativeAssignment).filter(
        InitiativeAssignment.initiative_id == world["iid"],
        InitiativeAssignment.status != "revoked").count()
    db.close()
    assert live == 0, "the revoke created a replacement — that is reassign"


def test_the_former_leader_can_no_longer_write(client, world):
    """⭐⭐ REVOCATION THAT DOES NOT REMOVE ACCESS IS A LABEL. Ordered after the
    step-down deliberately: this asserts the resolver reads the CURRENT state."""
    r = client.put(_url(world, "actions"), json=BODIES["actions"],
                   headers=_h(world, "leader"))
    assert r.status_code == 403, f"a revoked leader still wrote — {r.status_code}"


def test_revoking_a_vacant_initiative_is_a_conflict_not_a_not_found(client, world):
    """⭐ 404 WOULD SEND THE CALLER LOOKING FOR A MISSING INITIATIVE. It exists;
    it simply has no leader."""
    r = client.post(_url(world, "revoke-leader"), json={},
                    headers=_h(world, "admin"))
    assert r.status_code == 409, r.status_code
