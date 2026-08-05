"""§5a — seat caps are struck entirely. Unlimited users, both tiers.

⭐⭐ RULED 1 Aug. No caps of any kind — not on full members, not on assessment
participants per cycle, not on viewers — and therefore NO OVERAGE, because
⭐ AN OVERAGE PRICE IS A CAP WEARING A DIFFERENT NAME.

⭐ THE CAPS WERE LIVE AND REFUSING INVITES. `_enforce_seat_cap` raised HTTP 402
`assessor_cap_reached` from both assessor-invite paths, and the purchase flow
provisioned `assessor_cap` from the Stripe plan line.
"""
import ast
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ACCOUNTS = os.path.join(ROOT, "services/api/accounts.py")
_SCRIPT = os.path.join(ROOT, "scripts/check-no-seat-caps.py")
SRC = open(ACCOUNTS, encoding="utf-8").read()
FE = "/Users/samirasaf/dev/optimization-anchor"


def _fe(rel):
    p = os.path.join(FE, rel)
    if not os.path.exists(p):
        pytest.skip("frontend checkout not present")
    return open(p, encoding="utf-8").read()


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 1 · THE ACCEPTANCE TEST — an invite beyond the old limit succeeds
# ═══════════════════════════════════════════════════════════════════════════

def test_AN_INVITE_BEYOND_THE_OLD_LIMIT_SUCCEEDS():
    """⭐⭐ THE ACCEPTANCE TEST FOR THE WHOLE LANE. The old cap was 50 assessors
    per cycle; the 51st raised 402. It must now be ordinary.

    ⭐ Driven through the REAL invite path, not a helper — the refusal lived in
    the endpoint, so only the endpoint can prove it is gone.
    """
    from fastapi.testclient import TestClient

    from services.api.accounts import (Account, AssessmentInvite, SessionLocal,
                                       User, make_token)
    from services.api.main import app
    from services.api.modules.enterprise_state.models import Enterprise

    with TestClient(app) as c:
        db = SessionLocal()
        from services.api.core.db import SessionLocal as CoreSession
        with CoreSession() as core:
            ent = Enterprise(tenant="t-nocap", name="No Cap Co",
                             sector="industrials", reporting_currency="USD",
                             statement_units="thousands", ownership="private")
            core.add(ent)
            core.commit()
            core.refresh(ent)
            cid = ent.id

        u = db.query(User).filter_by(email="nocap-admin@test.local").first()
        if u is None:
            u = User(email="nocap-admin@test.local", name="Admin",
                     status="active", password_hash="x")
            db.add(u)
            db.commit()
            db.refresh(u)
        from services.api.accounts import CompanyAccess, Membership
        acct = db.query(Account).filter_by(owner_user_id=u.id).first()
        if acct is None:
            # ⭐ cap column left at the OLD default on purpose — if enforcement
            # were still reachable by any path, this row would trip it.
            acct = Account(owner_user_id=u.id, status="active",
                           company_slots=5, assessor_cap=50, assessor_overage=0)
            db.add(acct)
            db.commit()          # ⭐ commit BEFORE the row that references it
            db.refresh(acct)
        if not db.query(Membership).filter_by(user_id=u.id, company_id=cid).first():
            db.add(Membership(user_id=u.id, company_id=cid, role="admin",
                              status="active"))
        if not db.query(CompanyAccess).filter_by(company_id=cid).first():
            db.add(CompanyAccess(company_id=cid, account_id=acct.id,
                                 cid=f"AX-NOCP-{cid:04d}"))
        db.commit()

        tok = make_token(str(u.id), purpose="access", ttl=3600)
        h = {"Authorization": f"Bearer {tok}"}

        OLD_CAP = 50
        codes = []
        for i in range(OLD_CAP + 3):          # ⭐ 53 — three past the old ceiling
            r = c.post(f"/companies/{cid}/assessment/invites",
                       # ⭐ a REAL-LOOKING domain: `.test` is a reserved TLD and the email
            # validator 422s it — which reads as a refusal but is not a cap.
            json={"email": f"a{i}@nocap-example.com", "name": f"A{i}"},
                       headers=h)
            codes.append(r.status_code)

        refused = [i for i, code in enumerate(codes) if code == 402]
        assert not refused, (
            f"a cap still refuses: 402 at invite index {refused[:3]} "
            f"(old ceiling was {OLD_CAP})")

        # ⭐ MY FIRST VERSION POSTED TO /assessment/invite (singular) and got 404
        # for all 53. It recorded "no 402s" and would have PASSED as proof the
        # cap was gone — the coverage assertion below is the only reason it did
        # not. A guard that counts refusals must also count successes.
        ok = sum(1 for code in codes if 200 <= code < 300)
        # ⭐ COVERAGE, NOT ACTIVITY. "no 402s" is vacuous if nothing was invited.
        assert ok > OLD_CAP, (
            f"only {ok} invites succeeded; the test never reached the old "
            f"ceiling of {OLD_CAP}, so it proves nothing (III.4)")


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 2 · THE MACHINERY IS GONE, NOT DISABLED
# ═══════════════════════════════════════════════════════════════════════════

def test_the_enforcer_and_its_constants_are_REMOVED():
    """⭐ A disabled gate is a gate someone re-enables."""
    tree = ast.parse(SRC)
    names = {n.name for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    for gone in ("_enforce_seat_cap", "_seat_status", "_assessor_cap"):
        assert gone not in names, f"{gone} still exists"

    assigned = {t.id for n in ast.walk(tree) if isinstance(n, ast.Assign)
                for t in n.targets if isinstance(t, ast.Name)}
    for const in ("ASSESSOR_PLAN_CAPS", "ASSESSOR_CAP_DEFAULT",
                  "ASSESSOR_OVERAGE_BLOCK", "ASSESSOR_OVERAGE_PRICE"):
        assert const not in assigned, f"{const} is still defined"


def test_the_seats_ROUTES_are_no_longer_served():
    """⭐ The counter route and the overage door. Asserted against the real
    route table, not the file."""
    from fastapi.testclient import TestClient

    from services.api.main import app
    with TestClient(app) as c:
        paths = c.get("/openapi.json").json()["paths"]
    assert not [p for p in paths if "seats" in p], \
        "a seats route is still served"


def test_THE_PURCHASE_FLOW_NO_LONGER_PROVISIONS_A_CAP():
    """⭐⭐ A purchase buys the tier's CAPABILITY, never a headcount."""
    tree = ast.parse(SRC)
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Attribute) and t.attr in (
                        "assessor_cap", "assessor_overage"):
                    raise AssertionError(
                        f"line {n.lineno}: the webhook still writes {t.attr}")
        if isinstance(n, ast.Call):
            for kw in n.keywords:
                if kw.arg in ("assessor_cap", "assessor_overage"):
                    raise AssertionError(
                        f"line {n.lineno}: an Account is constructed with {kw.arg}")


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 3 · company_slots STANDS — the sweep must not be over-broad
# ═══════════════════════════════════════════════════════════════════════════

def test_COMPANY_SLOTS_SURVIVES():
    """⭐⭐ ONE COMPANY PER WORKSPACE IS STILL THE MODEL, and a company slot is
    NOT a user seat. Striking it would be a different ruling nobody made —
    a sweep that removes an adjacent quantity because it shares a word is the
    same substring error in a bigger blast radius."""
    from services.api.accounts import Account
    assert "company_slots" in {c.name for c in Account.__table__.columns}
    tree = ast.parse(SRC)
    fns = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert "_slots_used" in fns, "the company-slot counter was removed"
    assert "company_slots" in SRC


def test_the_slot_refusal_still_exists():
    """⭐ Its 402 is a DIFFERENT refusal and must remain."""
    assert "company license(s)" in SRC or "purchased company" in SRC


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 4 · THE COLUMNS ARE RETAINED, AND THE REASON IS STATED
# ═══════════════════════════════════════════════════════════════════════════

def test_the_cap_COLUMNS_are_retained_with_a_stated_reason():
    """⭐⭐ MEASURED 1 Aug: every account holds cap=50 and overage=0, so nothing
    was ever charged for overage. ⭐ But a column recording what a customer was
    PROVISIONED is not dropped on the strength of today's rows being clean —
    dropping it destroys the ability to answer the question later."""
    from services.api.accounts import Account
    cols = {c.name for c in Account.__table__.columns}
    assert "assessor_cap" in cols and "assessor_overage" in cols
    assert "REMAIN AS COLUMNS" in SRC or "not dropped" in SRC


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 5 · THE CUSTOMER-FACING SURFACES ARE GONE
# ═══════════════════════════════════════════════════════════════════════════

def test_the_cap_UI_is_removed():
    """⭐ The counter, the at-cap message and the overage price contradicted the
    comparison matrix's strongest row on the same product."""
    src = _fe("src/routes/stakeholder-engagement.tsx")
    for banned in ("at_cap", "overage_price", "overage_block", "AddAssessorsDoor",
                   "assessor invitations for this cycle", "assessment/seats"):
        assert banned not in src, f"a cap surface remains: {banned}"


def test_viewer_seats_included_is_gone():
    src = _fe("src/components/AboutBar.tsx")
    assert "viewer seats included" not in src


def test_the_matrix_still_says_unlimited():
    """⭐ The row this ruling aligns everything else to."""
    from services.api.comparison_matrix import USERS_INCLUDED
    assert "Unlimited" in USERS_INCLUDED["AXIOM"]


# ── the third shape: a cap in PROSE (added 5 Aug) ──────────────────────────

def test_the_guard_reaches_commercial_copy():
    """⛔⭐ THE GUARD WATCHED ONE PYTHON FILE AND READ ITS AST. The pricing page
    carried a member cap, a viewer cap, a per-cycle participant cap for BOTH
    tiers, and a per-seat add-on table — the exact MONETISATION shape this guard
    already refuses in code. It survived the 1 Aug consequence sweep and this
    gate, because neither looked at copy.

    ⭐ A cap in prose is the same claim where the guard does not look, and it is
    the one a customer actually reads.
    """
    src = open(_SCRIPT, encoding="utf-8").read()
    assert "_copy_half" in src, "the guard cannot reach commercial copy"
    assert "CAP_PROSE" in src


def test_the_copy_scan_strips_comments_before_matching():
    """⭐⭐ §III.9, THE EIGHTH OCCURRENCE — and it fired inside this very guard
    while it was being written. The corrected copy quotes the struck text in a
    comment so the strike is legible in the diff, and stakeholder-engagement.tsx
    records the removed $495-per-50 door in a `//` comment. A scan that reads
    comments fails the file for documenting its own fix.

    ⛔ BOTH COMMENT FORMS, and a URL's `//` must survive.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("nsc", _SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert "10 full members" not in m._strip_comments("{/* 10 full members */}")
    assert "10 full members" not in m._strip_comments("// 10 full members")
    assert "10 full members" not in m._strip_comments("/* 10 full members */")
    # ⭐ a URL is not a comment
    assert "example.com" in m._strip_comments('href="https://example.com/x"')
    # ⭐ and live copy still matches
    assert "10 full members" in m._strip_comments("<div>10 full members</div>")


def test_the_copy_half_states_a_non_run_rather_than_passing_quietly():
    """⭐ The ruled shape (94a7ce0, eb89ee8): this gate guards seat caps, not
    whether a sibling repo is checked out beside it."""
    src = open(_SCRIPT, encoding="utf-8").read()
    assert "COPY HALF NOT RUN" in src
    assert "asserts" in src
