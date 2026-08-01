"""The plan tier, as an ORDERING rather than a string.

⭐⭐ THE DEFECT THIS EXISTS FOR. `PLANS` was `("free", "business")` and two gates
tested `plan != "business"` and returned **402**. Adding a tier ABOVE Business
would therefore have locked the **highest-paying customer out of every write and
out of company creation** — because `"prescience" != "business"` is true.

⭐ EQUALITY CANNOT EXPRESS "AT LEAST". A gate that means *"you must have bought
at least Business"* written as `== "business"` is correct only while Business is
the top tier, and silently inverts the moment it is not.

⭐⭐ SO THE RANK IS THE SINGLE OWNER OF TIER ORDER. Adding a tier is one entry
here; no gate changes. A gate that spells a tier name is a gate that has to be
found again next time.
"""

# ⭐ Ascending. The NUMBERS are private; every caller asks a question instead.
_RANK = {
    "free": 0,
    "business": 1,
    "prescience": 2,
}

# ⭐ The wire vocabulary, derived from the rank so the two cannot disagree.
PLANS = tuple(sorted(_RANK, key=_RANK.get))

DEFAULT_PLAN = "free"


def rank(plan) -> int:
    """⭐ An unknown plan ranks BELOW free, never above. A typo must not grant
    entitlement — the failure direction matters more than the value."""
    return _RANK.get((plan or "").strip().lower(), -1)


def at_least(plan, minimum) -> bool:
    """⭐⭐ THE ONLY QUESTION A GATE SHOULD ASK. `at_least(p, "business")` is true
    for Business AND Prescience, which is what every existing `== "business"`
    gate meant."""
    return rank(plan) >= rank(minimum)


def is_known(plan) -> bool:
    return rank(plan) >= 0


def highest(*plans):
    """The strongest of several — used where a tier is resolved from more than
    one source and the answer must not depend on argument order."""
    known = [p for p in plans if is_known(p)]
    return max(known, key=rank) if known else DEFAULT_PLAN


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE PRESCIENCE GATE (§7j.6, ruled 1 Aug — option (a))
# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE ENGINE AND ITS TABS ARE GATED. THE PACK KEEPS ITS INPUTS.
#
# ⭐⭐ WHY THE PACK IS EXEMPT, recorded where the gate is written so nobody
# "completes" it later: `pack.py` reads the same cached tables into
# `strategic_move_library` and `computed_caches`, and two RENDERED sections —
# "What is at risk" and "What to do next" — consume them. Gating those would
# empty two sections of the BUSINESS DELIVERABLE for every Business customer.
#
# ⭐ AND IT IS NOT A LEAK: Business gets the CONCLUSION, Prescience gets the
# REASONING you can push on. Same engine, different question.

def require_prescience(get_current_user=None):
    """FastAPI dependency factory — refuses below Prescience with 402.

    ⭐ 402 (payment required), not 403: the caller is authenticated and
    permitted, and the only thing missing is the tier.

    ⭐⭐ THE SHOWCASE IS EXEMPT (ruled 1 Aug), and the exemption is checked
    BEFORE any user is resolved. The first version depended on
    `get_current_user`, which raises 401 for an anonymous caller — so FastAPI
    refused the request before the exemption could run, and ⭐⭐ EVERY ONE OF
    THE FOUR SURFACES RETURNED 401 TO EXACTLY THE PROSPECT THE LANE EXISTS FOR.
    Measured against the served backend, not assumed.

    ⭐⭐ SCOPED TO THE SHOWCASE FLAG, NEVER TO A COMPANY ID.
    """
    from fastapi import Header, HTTPException

    def dep(company_id: int, authorization: str = Header(None)):
        # ⭐⭐ core.db's session: BOTH `enterprises` (the showcase flag) and
        # `users` (which carries `plan`) live there. My first version read
        # `accounts.User` — that is `ax_users`, which HAS NO plan COLUMN, so the
        # gate would have refused every caller including a genuine Prescience
        # customer. CORE records the two User tables; this is what that costs.
        from ....api.core.db import SessionLocal as CoreSession
        from ...accounts import _is_showcase_company
        from ...core.config import require_plan
        from .deps import _session_user
        s = CoreSession()
        try:
            if _is_showcase_company(s, company_id):
                return None            # ⭐ demonstration, not entitlement
            if not require_plan():
                return None
            # ⭐ resolve the caller only once the exemption has not applied —
            # `_session_user` accepts BOTH auth systems (ADR-007).
            user, _sess = _session_user(s, authorization)
            if user is None:
                raise HTTPException(401, "Missing or invalid session token")
            if not at_least(getattr(user, "plan", None), "prescience"):
                raise HTTPException(
                    402, detail={"error": "prescience_required",
                                 "message": ("This surface is included in AXIOM "
                                             "Prescience."),
                                 "required_plan": "prescience"})
            return user
        finally:
            s.close()
    return dep


def showcase_tier_notice(db, company_id):
    """The marker an exempted surface carries, or None.

    ⭐⭐ IT STATES THE TIER, NOT THE EXEMPTION. A reader told they are seeing
    something "because it is a demo" is being told a trick was played; a reader
    told WHICH TIER INCLUDES IT has learnt the product. ⭐ Same sentence as the
    viewer surface's mark — defined once in `tier_marks`, never restated.
    """
    from ...accounts import _is_showcase_company
    if not _is_showcase_company(db, company_id):
        return None
    from ...tier_marks import MARK
    return {"note": MARK, "tier": "AXIOM Prescience"}
