"""§4u.1 ruling 5 — the axis→objective edge, and the cycle it closes.

⭐⭐ WHAT THIS EDGE IS FOR. §7o's chain runs

    sentiment → initiative → key result → KPI → statement line

and stops. A low Operational Excellence score reaches an intervention, and
NOTHING REPORTS BACK whether the intervention moved the score. That is a chain,
not a cycle, and the return edge had no representation anywhere in the product.

⛔ DECLARED, NEVER INFERRED. Matching an axis title against objective text is the
obvious shortcut and it is refused: `KeyResult.kpi_key` was designed to be matched
by normalised text and is NULL ON ALL 82 ROWS. Inference-by-name has produced
nothing in this codebase, measured twice.
"""
from .causal_map import ATTRIBUTION, CAUSAL_EVIDENCE, HYPOTHESIS  # noqa: F401

# ⭐ THE WALK, NAMED IN ONE PLACE. A caller that enumerates hops itself will
# drift from this list, and a walk that silently skips a hop reports a closed
# cycle over a gap.
CYCLE_HOPS = [
    {"hop": "axis", "what": "an assessment axis carrying a score"},
    {"hop": "objective", "what": "the objective declared to address that axis"},
    {"hop": "initiative", "what": "the initiative raised against the objective"},
    {"hop": "key_result", "what": "the key result the initiative delivers"},
    {"hop": "kpi", "what": "the KPI measuring that key result"},
    {"hop": "statement_line", "what": "the statement line the initiative declares it moves"},
    # ⭐⭐ THE HOP THIS LANE ADDS. Without it the walk is a chain.
    {"hop": "axis_again", "what": "the axis score in the next cycle — did it move?"},
]


def live_only(rows):
    """Links that have not been revoked — §4v.1 ruling 1."""
    return [r for r in rows if getattr(r, "revoked_at", None) is None]


def label_for(*, declared_by, delta):
    """-> (label, basis). ⭐⭐ THE HONEST LABEL, AND IT IS NEVER CAUSAL EVIDENCE.

    A cycle-over-cycle change in an axis score is NOT evidence that the linked
    initiative caused it. The Causal Map's promotion threshold needs FOUR things:
    a declarer, exclusive linkage, precedence, and no unexplained remainder.

    ⛔ AN AXIS SCORE CAN SATISFY AT MOST THE FIRST TWO. It carries no declared
    SHARE and therefore no residual, so exclusivity of CAUSE cannot be
    established from exclusivity of LINKAGE — which is the exact condition B11's
    ruling warns about. The ceiling here is `attribution`, permanently, and that
    is a property of the quantity rather than of today's data.
    """
    if not declared_by:
        return HYPOTHESIS, ("no declarer is recorded, so nobody asserted that "
                            "this objective addresses this axis")
    if delta is None:
        return ATTRIBUTION, ("a declared relationship; the axis has no second "
                             "cycle yet, so no movement can be reported")
    if abs(delta) < 1e-9:
        return ATTRIBUTION, ("a declared relationship; the axis score did not "
                             "move between cycles")
    direction = "rose" if delta > 0 else "fell"
    return ATTRIBUTION, (
        f"a declared relationship; the axis score {direction} by "
        f"{abs(round(delta, 2))} between cycles. This is ATTRIBUTION, not causal "
        f"evidence: an axis score carries no declared share and no residual, so "
        f"exclusivity of cause cannot be established from exclusivity of linkage.")


def may_declare(db, company_id, user, *, department_id):
    """⭐ §4v.1 ruling 3 — declaring a link is a DISTINCT permission from
    overriding a figure.

    ⭐⭐ THE SEAM HAS NOW DIVERGED, WHICH IS WHAT IT WAS FOR. This read
    `department_authority` and carried the note *"same holder today, recorded
    separately so the two can diverge without a migration."* When
    `department_authority` narrowed to ENDORSING_ROLES, declaration inherited the
    narrowing and a steward could no longer draw an edge — the wrong answer under
    the R&R, which has strategy-map edges MAINTAINED by the steward and APPROVED
    by the CXO.

    ⛔ It now reads `department_declare_authority`, which accepts any live grant.
    Endorsement is untouched: gaining declare authority confers no sign-off, and
    a test mutation-proves it rather than trusting that the two calls stay apart.

    ⛔ PLATFORM STAFF REFUSED. We must never declare a customer's causal claim
    about their own business, whatever the operator bypass grants elsewhere.
    """
    from .overrides import _is_platform_staff, department_declare_authority
    if _is_platform_staff(user):
        return False
    if department_id is None or db is None:
        return False
    return department_declare_authority(db, company_id, user.id, department_id)


def walk(counts: dict) -> dict:
    """Report each hop and where the cycle breaks.

    ⭐ EVERY HOP IS REPORTED, INCLUDING THE ZERO ONES. A walker that omits a
    broken hop reports a closed cycle over a gap — the shape `causal_map.build`
    already refuses by listing isolated nodes rather than dropping them.
    """
    hops, breaks = [], []
    for h in CYCLE_HOPS:
        n = int(counts.get(h["hop"], 0) or 0)
        hops.append({**h, "n": n, "resolves": n > 0})
        if n <= 0:
            breaks.append(h["hop"])
    return {"hops": hops, "closes": not breaks, "breaks_at": breaks}
