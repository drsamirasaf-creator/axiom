"""Participant role → capability matrix (Participant Role Enforcement lane).

ONE source of truth. Endpoints declare a required CAPABILITY; the accounts.py
`require_capability(...)` dependency resolves the caller's role set (admin membership
+ participant roles by email, union) and grants/denies. No scattered inline role
checks.

Roles (as stored on ax_participants.roles + the admin Membership role):
  admin           — existing account-admin; superset, never restricted by this module
  decision_maker  — Viewer + disposition on Recommendations & Proposals
  viewer          — read-only viewer-class surfaces
  assessor        — take the instrument + submit ideas + viewer-class reads

Role UNION is additive (a CEO who is decision_maker + assessor gets both sets).
"""

# ── capabilities ──────────────────────────────────────────────────────────────
CAP_VIEW = "view"                              # viewer-class reads (dashboards, cockpit, org, SWOT, aggregates)
CAP_TAKE_INSTRUMENT = "take_instrument"        # submit the assessment instrument (also gated by assess_session)
CAP_SUBMIT_IDEA = "submit_idea"                # submit an Innovation Hub idea
CAP_DISPOSE = "dispose_recommendations"        # accept/reject/status on Recommendations & Proposals
CAP_ADMIN = "admin"                            # participant mgmt, uploads, template/data-input, all other writes

ALL_CAPS = frozenset({CAP_VIEW, CAP_TAKE_INSTRUMENT, CAP_SUBMIT_IDEA, CAP_DISPOSE, CAP_ADMIN})

ROLE_CAPABILITIES = {
    "admin":          set(ALL_CAPS),                                   # superset
    "decision_maker": {CAP_VIEW, CAP_DISPOSE},                         # Viewer + disposition
    "viewer":         {CAP_VIEW},
    "assessor":       {CAP_VIEW, CAP_TAKE_INSTRUMENT, CAP_SUBMIT_IDEA},
}


def capabilities_for(roles) -> set:
    """Union of the capabilities granted by a role set (additive)."""
    caps = set()
    for r in roles or ():
        caps |= ROLE_CAPABILITIES.get(r, set())
    return caps


def has_capability(roles, cap: str) -> bool:
    """True if any role in the set grants `cap` (admin implies everything)."""
    if "admin" in (roles or ()):
        return True
    return cap in capabilities_for(roles)
