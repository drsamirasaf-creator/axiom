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

def require_prescience(get_current_user):
    """FastAPI dependency factory — refuses below Prescience with 402.

    ⭐ 402 (payment required), not 403: the caller is authenticated and
    permitted, and the only thing missing is the tier. A 403 would tell them
    they are not allowed, which is a different and wrong statement.
    """
    from fastapi import Depends, HTTPException

    def dep(user=Depends(get_current_user)):
        from ...core.config import require_plan
        # ⭐ the same env switch the other plan gates honour, so a dev/sandbox
        # environment does not become the one place tiering is untested.
        if require_plan() and not at_least(getattr(user, "plan", None), "prescience"):
            raise HTTPException(
                402, detail={"error": "prescience_required",
                             "message": ("This surface is included in AXIOM "
                                         "Prescience."),
                             "required_plan": "prescience"})
        return user
    return dep
