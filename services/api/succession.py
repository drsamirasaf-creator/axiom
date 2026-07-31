"""Admin ranking, client-side succession, and accountable support grant.

⭐⭐ THE PROBLEM MEASURED AT `cc88e9d`: nothing distinguished one admin from
another — no primary, owner, creator or ordering — and ALL SIX live companies held
exactly ONE active admin. `revoke` handles viewers only, so an admin could not be
revoked at all. ⭐ For the client, lockout was total.

⭐⭐ SUCCESSION IS THE FIX; SUPPORT RECOVERY IS THE FALLBACK. The primary leaving
is the COMMON case and must not require a support ticket — a recovery path used
routinely stops being a recovery path and becomes an access channel.

⭐⭐ AND SUPPORT GRANTS ROLES, NEVER DATA. Ruled 31 Jul. Support can name a user
and make them an admin; it does not read client data and it never will. There is
NO credential reset here — resetting a password would let one person continue
another's authored history, and the newer models denormalise `actor_label`
precisely so that promoting a new admin does not make anyone inherit an identity.
"""
from datetime import datetime

PRIMARY = 0


def ranked_admins(db, company_id):
    """Active admins, PRIMARY first, then deputies in order, then unranked.

    ⭐ UNRANKED SORTS LAST AND IS NOT SILENTLY TREATED AS A DEPUTY. Every admin
    predating this feature is unranked, and calling one of them "next in line"
    would assert a client decision nobody made.
    """
    from .accounts import Membership
    rows = (db.query(Membership)
              .filter_by(company_id=company_id, role="admin", status="active")
              .all())
    return sorted(rows, key=lambda m: (m.admin_rank is None,
                                       m.admin_rank if m.admin_rank is not None else 0,
                                       m.id))


def primary_admin(db, company_id):
    """⭐ The rank-0 admin, or None. NEVER "the first row we found"."""
    return next((m for m in ranked_admins(db, company_id)
                 if m.admin_rank == PRIMARY), None)


def successor(db, company_id, *, excluding_user_id=None):
    """The lowest-ranked deputy who is not the departing admin.

    ⭐ Returns None rather than falling back to an unranked admin — **a
    succession that guesses is the behaviour `transfer_admin` already refuses.**
    """
    for m in ranked_admins(db, company_id):
        if m.user_id == excluding_user_id or m.admin_rank is None:
            continue
        if m.admin_rank != PRIMARY:
            return m
    return None


def set_ranks(db, company_id, order, *, actor=None, now=None):
    """Client-set ranking. `order` is a list of user_ids, primary first.

    ⭐ EVERY NAMED USER MUST ALREADY BE AN ACTIVE ADMIN. Ranking is not a grant:
    conflating them would make an ordering call a privilege escalation.
    """
    from fastapi import HTTPException

    from .accounts import Membership, audit
    now = now or datetime.utcnow()
    admins = {m.user_id: m for m in ranked_admins(db, company_id)}
    unknown = [u for u in order if u not in admins]
    if unknown:
        raise HTTPException(422, f"not active administrators: {unknown}")
    if len(set(order)) != len(order):
        raise HTTPException(422, "the ranking repeats a user")
    for rank, uid in enumerate(order):
        admins[uid].admin_rank = rank
    # ⭐ admins left out of the order become UNRANKED again rather than being
    # appended in whatever sequence the query returned.
    for uid, m in admins.items():
        if uid not in order:
            m.admin_rank = None
    audit(db, getattr(actor, "id", None), "admin_ranking_set", "company",
          company_id, detail=f"order={order}")
    db.flush()
    return [{"user_id": u, "admin_rank": i} for i, u in enumerate(order)]


def step_down(db, company_id, *, actor, to_user_id=None, now=None):
    """⭐⭐ THE COMMON CASE, AND IT NEEDS NO SUPPORT TICKET.

    The acting admin hands the seat to a named deputy (or, if unnamed, to the
    ranked successor) and becomes a viewer.

    ⭐ IT REFUSES TO LEAVE A COMPANY WITH NO ADMIN. That is the one outcome no
    client can undo, and it is the state this whole lane exists to prevent.
    """
    from fastapi import HTTPException

    from .accounts import Membership, audit
    now = now or datetime.utcnow()
    admins = ranked_admins(db, company_id)
    me = next((m for m in admins if m.user_id == actor.id), None)
    if me is None:
        raise HTTPException(403, "only an active administrator may step down")

    if to_user_id is not None:
        target = next((m for m in admins if m.user_id == to_user_id), None)
        if target is None:
            # ⭐ PROMOTING A NON-ADMIN IS A GRANT, and a grant is a different act
            # with a different authority. Refused here deliberately.
            raise HTTPException(422, f"user {to_user_id} is not an active "
                                     f"administrator; rank them first")
    else:
        target = successor(db, company_id, excluding_user_id=actor.id)
        if target is None:
            raise HTTPException(409,
                                "no ranked deputy to succeed you. Rank a deputy "
                                "first, or name one explicitly — refusing to "
                                "choose an unranked administrator.")
    if target.user_id == me.user_id:
        raise HTTPException(422, "you cannot hand the seat to yourself")

    remaining = [m for m in admins if m.user_id != me.user_id]
    if not remaining:
        raise HTTPException(409, "you are the only administrator; stepping down "
                                 "would leave the company with none")

    target.admin_rank = PRIMARY
    me.role = "viewer"
    me.admin_rank = None
    audit(db, actor.id, "admin_stepped_down", "company", company_id,
          detail=f"{actor.id} -> {target.user_id}")
    db.flush()
    return {"new_primary_user_id": target.user_id, "former_admin": actor.id}


def revoke_admin(db, company_id, membership_id, *, actor, now=None):
    """⭐⭐ THE REVOKE GAP, CLOSED. `revoke` reads `_get_viewer_row`, so an admin
    could not be revoked through it — which is HALF of why lockout was total.

    ⭐ THE LAST ADMIN CANNOT BE REVOKED. Not by another admin, not by the same
    admin, not by anyone: it is the one action with no client-side undo.
    """
    from fastapi import HTTPException

    from .accounts import Membership, audit
    now = now or datetime.utcnow()
    m = db.get(Membership, membership_id)
    if m is None or m.company_id != company_id or m.role != "admin":
        raise HTTPException(404, "not an administrator of this company")
    if m.status != "active":
        return {"ok": True, "status": m.status, "note": "already inactive"}
    if len([x for x in ranked_admins(db, company_id) if x.id != m.id]) == 0:
        raise HTTPException(409, "this is the only administrator; revoking it "
                                 "would lock the company out")
    m.status = "revoked"
    m.admin_rank = None
    audit(db, getattr(actor, "id", None), "admin_revoked", "membership", m.id)
    db.flush()
    return {"ok": True, "status": "revoked"}


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ SUPPORT-SIDE GRANT — ROLES, NEVER DATA
# ═══════════════════════════════════════════════════════════════════════════

VERIFICATION_ENFORCED = [
    "the caller holds platform_role staff or super (server-side)",
    "the target is an existing user account, named by id",
    "the company exists",
    "the act is audited with the actor, the target and the company",
    "the client's remaining admins are notified",
]

# ⭐⭐ RECORDED AS PROCEDURAL RATHER THAN ASSUMED. The whole capability is a way
# into an account, so SOCIAL ENGINEERING IS THE ATTACK — and no code here can
# tell a genuine request from a convincing one.
VERIFICATION_PROCEDURAL = [
    "that the requester is who they claim to be",
    "that the requester is entitled to administer THAT company",
    "that the departing admin is genuinely unavailable",
    "that the request did not originate from a compromised mailbox",
]


def support_grant_admin(db, company_id, target_user_id, *, actor, reason,
                        now=None):
    """Support grants ADMIN to a named user. It reads no client data.

    ⭐ NO CREDENTIAL RESET, DELIBERATELY. Handing over a password would let one
    person continue another's authored history; the newer models denormalise
    `actor_label` precisely so a new admin inherits authority WITHOUT inheriting
    an identity.

    ⭐ A REASON IS REQUIRED. An unexplained support grant is indistinguishable
    from an unauthorised one after the fact.
    """
    from fastapi import HTTPException

    from .accounts import Membership, User, audit
    now = now or datetime.utcnow()
    if getattr(actor, "platform_role", None) not in ("staff", "super"):
        raise HTTPException(403, "platform staff only")
    if not (reason or "").strip():
        raise HTTPException(422, "a reason is required for a support grant")
    target = db.get(User, target_user_id)
    if target is None:
        raise HTTPException(404, "no such user")

    m = (db.query(Membership)
           .filter_by(company_id=company_id, user_id=target_user_id).first())
    if m is None:
        m = Membership(user_id=target_user_id, company_id=company_id,
                       role="admin", status="active", approved_at=now)
        db.add(m)
    else:
        m.role, m.status = "admin", "active"
    # ⭐ RANK IS NOT SET. Support restores ACCESS; the client decides ORDER.
    m.admin_rank = None
    audit(db, getattr(actor, "id", None), "support_granted_admin", "company",
          company_id,
          detail=f"target_user={target_user_id}; reason={reason.strip()[:400]}")
    db.flush()
    return {"granted": True, "company_id": company_id,
            "user_id": target_user_id,
            "note": ("access restored; ranking is the client's to set. No "
                     "credentials were changed and no client data was read.")}
