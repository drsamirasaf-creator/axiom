"""HTTP surface for CXO sign-off and overrides — READ PATHS ONLY (§4x Stage 2).

Riskiest-last, matching Stage 1's discipline. These endpoints expose NO NEW
CAPABILITY: every one renders state that already exists and that the service
layer already computes. Nothing here can create, change or retire anything.

The write endpoints are deliberately absent, and
`test_no_write_endpoint_resolves_to_an_override_path` asserts against the app's
REAL route table that no POST/PATCH/PUT/DELETE resolves to an override path —
so this file cannot quietly grow one.

WHY A SEPARATE MODULE. overrides.py is the service layer and has no router. That
separation is what lets the route-table guard mean something: a write path would
have to be added HERE, visibly, rather than appearing as one more function among
the service helpers.
"""
from fastapi import APIRouter, Depends, HTTPException

from .accounts import (Department, _summary_access, get_db,
                       require_company_admin, get_current_user, User)
from .overrides import (signoff_state, signoff_diff, grants_for, audit_rows,
                        department_state, active_signoff, department_authority)

signoff_router = APIRouter(tags=["cxo-signoff"])


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
