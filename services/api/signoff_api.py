"""HTTP surface for CXO sign-off and overrides (§4x Stage 2).

Built riskiest-last, matching Stage 1: reads first and verified, then writes.

TWO GUARDS ON EVERY WRITE, BOTH PROVEN SEPARATELY. Each write route calls
can_author() itself via _route_authority(), and the service beneath calls it
again. That duplication is deliberate and must not be optimised away: AN
ENDPOINT THAT RELIES ON A SERVICE CHECK IS ONE REFACTOR AWAY FROM BEING
UNGUARDED. The tests assert a refusal at the HTTP layer AND, separately, that the
service would also have refused — so it is never ambiguous which guard did the
work, and neither can rot behind the other.

GRANT AND REVOKE ARE ADMIN-ONLY (§7.1) and additionally refuse platform staff:
require_company_admin gives us an operator bypass everywhere else, and being
unable to AUTHOR is worthless if we can GRANT ourselves authority a moment
earlier.

WHY A SEPARATE MODULE. overrides.py is the service layer and carries no router,
so every HTTP-reachable capability is in this one file. The route guard
enumerates from app.openapi() — the app's real path list — after that guard was
found inspecting 7 of 292 paths and passing vacuously.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .accounts import (Department, _summary_access, get_db,
                       require_company_admin, get_current_user, User)
from .overrides import (signoff_state, signoff_diff, grants_for, audit_rows,
                        department_state, active_signoff, department_authority,
                        can_author, AuthorityError, GrantError, sign_off,
                        create_override, withdraw_override, retire_override,
                        grant_department, revoke_department, REASON_CATEGORIES)

signoff_router = APIRouter(tags=["cxo-signoff"])


# ── route-level authority (TWO GUARDS, BOTH PROVEN) ──────────────────────────

def _route_authority(db, company_id: int, department_id: int, user) -> None:
    """Enforce authority AT THE ROUTE, in addition to the service.

    The service also calls can_author(), and that is deliberate duplication
    rather than redundancy to be optimised away: AN ENDPOINT THAT RELIES ON A
    SERVICE CHECK IS ONE REFACTOR AWAY FROM BEING UNGUARDED. If someone later
    inlines, wraps or reorders the service call, the route still refuses.

    Both guards are proven separately in the tests — a refusal at the HTTP layer
    AND a control showing the service beneath would also have refused — so it is
    never ambiguous which one did the work.
    """
    try:
        can_author(db, company_id, user, "department", department_id)
    except AuthorityError as e:
        raise HTTPException(403, str(e))


def _refuse_platform_staff(user, what: str) -> None:
    """§7.1 + the fifth authority direction. require_company_admin grants
    platform staff an operator bypass everywhere else, so admin-gating alone
    would let us grant ourselves authority — and being unable to AUTHOR is
    worthless if we can GRANT a moment earlier."""
    if getattr(user, "platform_role", None) in ("staff", "super"):
        raise HTTPException(
            403, f"Platform staff cannot {what}. Authority over a customer's "
                 f"figures must originate with the customer.")


class SignOffIn(BaseModel):
    signer_label: str
    signer_role_label: str | None = None


class OverrideIn(BaseModel):
    metric_ref: str
    metric_label: str | None = None
    override_value: float | None = None
    computed_value: float | None = None
    reason_category: str | None = None
    reason_note: str | None = None
    author_label: str


class WithdrawIn(BaseModel):
    metric_ref: str
    kind: str = "withdrawn"


class GrantIn(BaseModel):
    user_id: int
    role: str = "cxo"
    role_label: str | None = None


class RevokeIn(BaseModel):
    user_id: int
    reason: str = "departed"


def _dept_or_404(db, company_id: int, department_id: int) -> Department:
    dep = db.get(Department, department_id)
    if dep is None or dep.company_id != company_id:
        raise HTTPException(404, "No such department in this company.")
    return dep


@signoff_router.get("/companies/{company_id}/departments/{department_id}/signoff")
def get_signoff_state(company_id: int, department_id: int,
                      member=Depends(_summary_access), db=Depends(get_db)):
    """The department's sign-off state: signed / unsigned / vacant.

    THREE STATES, NOT A BOOLEAN (§7.6). `vacant` and `unsigned` are both "no
    signature" and mean opposite things — nobody is accountable, versus the
    accountable person has not acted yet. A surface that renders them
    identically converts an organisational gap into an apparent individual
    failure, so the distinction is produced here rather than left to the client
    to infer from a null.

    `_summary_access` because this renders on the department dashboard alongside
    the figures it attests to, and the attestation line ("Signed off by J. Chen,
    then CFO, 14 Mar 2026") is BOARD-VISIBLE BY DESIGN — a signature nobody can
    see does not end any debate.
    """
    _dept_or_404(db, company_id, department_id)
    return signoff_state(db, company_id, department_id)


@signoff_router.get("/companies/{company_id}/departments/{department_id}/signoff/diff")
def get_signoff_diff(company_id: int, department_id: int,
                     member=Depends(_summary_access), db=Depends(get_db)):
    """§8.3 — what changed since the signature, grouped by cause.

    Not a bare "awaiting re-sign-off": a CXO who can see what moved will
    re-review it; one facing an unexplained prompt will just click, and the
    signature is only worth what the review behind it is worth.

    Carries `own_unchanged` explicitly so the cheap case is one field rather
    than an inference over two lists, and `retirement_candidates` (§8.4) so the
    absorbed-override prompt rides this surface rather than needing its own.
    """
    _dept_or_404(db, company_id, department_id)
    return signoff_diff(db, company_id, department_id)


@signoff_router.get("/companies/{company_id}/departments/{department_id}/authority")
def get_department_authority(company_id: int, department_id: int,
                             member=Depends(require_company_admin),
                             user: User = Depends(get_current_user),
                             db=Depends(get_db)):
    """Who holds authority over this department.

    ADMIN-GATED, unlike the two above. This NAMES PEOPLE and what they may do —
    the same reason /roster is admin-gated. The sign-off state deliberately
    exposes the SIGNER of an existing attestation (board-visible by design); it
    does not expose the roster of who COULD sign, which is governance
    configuration rather than a published fact.

    Revoked grants are included on request so an admin can answer "who used to
    hold this" — §7.4's history, which revocation never erases.
    """
    _dept_or_404(db, company_id, department_id)
    live = grants_for(db, company_id, department_id=department_id)
    every = grants_for(db, company_id, department_id=department_id,
                       include_revoked=True)
    return {
        "company_id": company_id,
        "department_id": department_id,
        "state": department_state(db, company_id, department_id),
        "holders": [_grant_out(g) for g in live],
        "history": [_grant_out(g) for g in every],
    }


@signoff_router.get("/companies/{company_id}/authority")
def list_company_authority(company_id: int,
                           member=Depends(require_company_admin),
                           user: User = Depends(get_current_user),
                           db=Depends(get_db)):
    """Every live grant in the company, plus each department's state.

    The admin's view of §7.1: who speaks for what. Departments with no holder
    appear as `vacant` / `never_assigned` rather than being omitted — an absent
    row would read as "nothing to see", which is the opposite of what a vacancy
    means.
    """
    deps = (db.query(Department).filter_by(company_id=company_id)
              .order_by(Department.name).all())
    return {
        "company_id": company_id,
        "departments": [{
            "department_id": d.id,
            "department": d.name,
            "state": department_state(db, company_id, d.id),
            "holders": [_grant_out(g) for g in
                        grants_for(db, company_id, department_id=d.id)],
            "signoff": signoff_state(db, company_id, d.id),
        } for d in deps],
    }


@signoff_router.get("/companies/{company_id}/overrides/audit")
def get_override_audit(company_id: int, include_superseded: bool = True,
                       member=Depends(require_company_admin),
                       user: User = Depends(get_current_user),
                       db=Depends(get_db)):
    """The board-defensibility record: every override that has ever existed.

    `include_superseded` defaults TRUE — an audit trail that shows only current
    state is not an audit trail.
    """
    return {"company_id": company_id,
            "overrides": audit_rows(db, company_id,
                                    include_superseded=include_superseded)}


def _grant_out(g) -> dict:
    return {
        "grant_id": g.id,
        "user_id": g.user_id,
        "role": g.role,
        # Frozen at grant time (§7.5) — a board reading a two-year-old sign-off
        # needs the role AS IT WAS, not as the org chart is now.
        "role_label": g.role_label,
        "granted_by": g.granted_by,
        "granted_at": g.granted_at.isoformat() if g.granted_at else None,
        "revoked_at": g.revoked_at.isoformat() if g.revoked_at else None,
        "revoked_by": g.revoked_by,
        "revoke_reason": g.revoke_reason,
        "active": g.revoked_at is None,
    }


# ── WRITE PATHS ──────────────────────────────────────────────────────────────
# Each is gated at the route by _route_authority() AND again inside the service.
# Grant and revoke are admin-only per §7.1 and additionally refuse platform
# staff, because require_company_admin grants us an operator bypass.

@signoff_router.post("/companies/{company_id}/departments/{department_id}/signoff",
                     status_code=201)
def post_signoff(company_id: int, department_id: int, body: SignOffIn,
                 member=Depends(require_company_admin),
                 user: User = Depends(get_current_user), db=Depends(get_db)):
    """Attest to the dashboard AS SHOWN. Review then attest, one act."""
    _dept_or_404(db, company_id, department_id)
    _route_authority(db, company_id, department_id, user)
    if not (body.signer_label or "").strip():
        raise HTTPException(422, "signer_label is required — a signature cannot be anonymous.")
    row = sign_off(db, company_id, department_id, user=user,
                   signer_label=body.signer_label.strip(),
                   signer_role_label=body.signer_role_label)
    db.commit()
    return signoff_state(db, company_id, department_id) | {"signoff_id": row.id}


@signoff_router.post("/companies/{company_id}/departments/{department_id}/overrides",
                     status_code=201)
def post_override(company_id: int, department_id: int, body: OverrideIn,
                  member=Depends(require_company_admin),
                  user: User = Depends(get_current_user), db=Depends(get_db)):
    """Author an attributed exception. THE RARE DELIBERATE ACT, not an edit —
    the dashboard is not a spreadsheet."""
    _dept_or_404(db, company_id, department_id)
    _route_authority(db, company_id, department_id, user)
    try:
        row = create_override(
            db, company_id, department_id, user=user,
            author_label=body.author_label, metric_ref=body.metric_ref,
            metric_label=body.metric_label or body.metric_ref,
            override_value=body.override_value,
            computed_value=body.computed_value,
            reason_category=body.reason_category,
            reason_note=body.reason_note)
    except AuthorityError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        # 422 rather than 400: these are content rules — a reason outside the
        # enum, a metric outside the resolver whitelist — not malformed syntax.
        raise HTTPException(422, str(e))
    db.commit()
    return {"override_id": row.id, "metric_ref": row.metric_ref,
            "displayed": row.override_value,
            "computed": row.computed_value_at_override,
            "reason_category": row.reason_category,
            "author": row.author_label}


@signoff_router.post("/companies/{company_id}/departments/{department_id}/overrides/withdraw")
def post_withdraw_override(company_id: int, department_id: int, body: WithdrawIn,
                           member=Depends(require_company_admin),
                           user: User = Depends(get_current_user),
                           db=Depends(get_db)):
    """Retract or retire. NEVER a delete — "adjusted and then un-adjusted" is
    itself board-relevant, and `kind` keeps a withdrawal (the CXO was wrong)
    distinct from an absorption (the source caught up)."""
    _dept_or_404(db, company_id, department_id)
    _route_authority(db, company_id, department_id, user)
    if body.kind not in ("withdrawn", "absorbed"):
        raise HTTPException(422, "kind must be 'withdrawn' or 'absorbed'.")
    try:
        row = retire_override(db, company_id, department_id, user=user,
                              metric_ref=body.metric_ref, kind=body.kind)
    except AuthorityError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))
    db.commit()
    return {"override_id": row.id, "supersession_kind": row.supersession_kind,
            "active": False}


@signoff_router.post("/companies/{company_id}/departments/{department_id}/authority",
                     status_code=201)
def post_grant(company_id: int, department_id: int, body: GrantIn,
               member=Depends(require_company_admin),
               user: User = Depends(get_current_user), db=Depends(get_db)):
    """§7.1 — THE COMPANY ADMIN GRANTS. Admin-gated, and platform staff refused:
    the admin decides who speaks for a department and can never speak for one,
    and we can do neither."""
    _dept_or_404(db, company_id, department_id)
    _refuse_platform_staff(user, "issue department authority")
    try:
        row = grant_department(db, company_id, department_id,
                               user_id=body.user_id, granted_by=user.id,
                               role=body.role, role_label=body.role_label,
                               actor=user)
    except GrantError as e:
        raise HTTPException(403, str(e))
    db.commit()
    return _grant_out(row)


@signoff_router.post("/companies/{company_id}/departments/{department_id}/authority/revoke")
def post_revoke(company_id: int, department_id: int, body: RevokeIn,
                member=Depends(require_company_admin),
                user: User = Depends(get_current_user), db=Depends(get_db)):
    """§7.4 — a TIMESTAMP, not a deletion. Touches the grant and nothing else:
    past sign-offs and overrides stand exactly as made."""
    _dept_or_404(db, company_id, department_id)
    _refuse_platform_staff(user, "revoke department authority")
    try:
        row = revoke_department(db, company_id, department_id,
                                user_id=body.user_id, revoked_by=user.id,
                                reason=body.reason)
    except GrantError as e:
        raise HTTPException(404, str(e))
    db.commit()
    return _grant_out(row)
