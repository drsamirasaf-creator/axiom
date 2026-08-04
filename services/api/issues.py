"""§4u.1 ruling 4 — an ISSUE, distinct from a recommendation.

⭐⭐ THE DECISIVE ASYMMETRY: A RECOMMENDATION CAN BE DECLINED AND AN ISSUE CANNOT.
"Approvals take three weeks" asserts a state of the world. Routed into the
initiative queue it inherits `approve` / `reject`, and rejecting it does not make
approvals faster — it records inaction under a label that reads as "considered
and dismissed". ⛔ A `type` COLUMN WOULD LEAVE ISSUES SHARING `reject`, WHICH IS
THE DEFECT ITSELF, so this is a separate object with a separate vocabulary.

⭐⭐ FREQUENCY IS THE FINDING. Ten comments naming one friction are ONE issue with
weight ten — not ten items competing for a slot, each looking minor. Weight is
what the current model destroys.

⛔ AND THE GROUPING IS DECLARED, NEVER DERIVED. Clustering free text would be
inference, and this codebase has exactly one inference-by-name mechanism —
`KeyResult.kpi_key`, matched by normalised text — which is NULL ON ALL 82 ROWS
because nothing ever wrote it. A human attaches a comment to an issue and the
attachment carries their name and the date, exactly as B10 requires.
"""
from .assessment_engine import KFLOOR      # ⭐ read, never restated (§7u)

# ⭐⭐ THREE STATES, AND NONE OF THEM MEANS "DECLINED".
#   open      — true, and nobody has acted
#   addressed — an initiative exists against it and is answering it
#   accepted  — the company has decided to live with it. STILL TRUE.
ISSUE_STATES = ("open", "addressed", "accepted")

STATE_NOTE = {
    "open": "Raised and unaddressed. Nobody has yet decided what to do about it.",
    "addressed": "An initiative has been raised against this. The issue stays "
                 "open as a fact until the initiative changes it.",
    # ⭐ THE STATE THAT LOOKS LIKE A REFUSAL AND IS NOT. A company may knowingly
    # live with a true thing; saying so is a decision, and a defensible one.
    # What it must never read as is "we considered this and dismissed it".
    "accepted": "Acknowledged, and the company has chosen to live with it. This "
                "is still true — it has been accepted, not dismissed.",
}

# ⭐ The recommendation vocabulary, named here ONLY so the separation is
# assertable. Nothing in this module may return one of these.
RECOMMENDATION_DISPOSITIONS = ("none", "adopted", "parked", "dismissed")


def live_only(rows):
    """Attachments that have not been revoked — §4v.1 ruling 1.

    ⭐ A RETRACTED GROUPING MUST STOP COUNTING. Otherwise weight overstates the
    finding permanently, and weight is the whole argument for resourcing it.
    """
    return [r for r in rows if getattr(r, "revoked_at", None) is None]


def weight(attachments) -> int:
    """How many comments were DECLARED to be this same finding.

    ⭐⭐ THIS IS THE NUMBER THE CURRENT MODEL DESTROYS. Ten comments naming one
    friction become ten competing minor items; here they are one item carrying
    the number ten, which is the argument for acting.
    """
    return len(attachments or [])


def weight_block(*, n: int, department_scoped: bool) -> dict:
    """Whether an issue's weight may be published, and why not.

    ⭐⭐ A COUNT DISCLOSES NOTHING ON ITS OWN, AND THE ENGINE ALREADY SAYS SO.
    `assessment_engine.suppression_block` publishes `n` even for a hidden slice,
    deliberately — it is what makes "withheld" credible rather than
    indistinguishable from silence. So an ENTERPRISE-WIDE weight of 2 is
    publishable: "two people raised this" identifies nobody.

    ⛔ THE SLICE IS WHERE THE FLOOR BITES. "Two of the three people in Quality
    raised this", sitting beside a verbatim, narrows to a person — the same
    reasoning that already refuses department AND seniority together on the
    verbatim list, because the floor sees a compliant participant count while
    the CELL identifies the author.

    ⭐ THE COUNT IS RETURNED EITHER WAY. It is the SLICE that is withheld.
    """
    if department_scoped and n < KFLOOR:
        return {"n": n, "publishable": False,
                "reason": "below_anonymity_floor",
                "note": "Withheld for anonymity — this issue's weight within a "
                        "single department is below the confidentiality floor."}
    return {"n": n, "publishable": True, "reason": None, "note": None}


def rank_key(row: dict):
    """Order for the Issues list — ⭐ AND A RANK IS A PUBLICATION.

    ⛔ A SUB-FLOOR ITEM IS RANKED AS UNRATED, NOT BY ITS HIDDEN NUMBER. If a
    withheld weight still ordered the list, the ORDER would leak it: a reader who
    knows the neighbours can bound the hidden value, and over a short list often
    recover it. Ranking by a number you are refusing to show is showing it.

    ⭐ RATINGS ARE RULED (§4u.1) BUT NOT BUILT, so the primary sort is the
    issue's WEIGHT — the frequency signal this object exists to carry. The rating
    slot is reserved and stated rather than silently occupied.
    """
    publishable = bool((row.get("weight_block") or {}).get("publishable", True))
    return (
        0 if publishable else 1,                 # unrated sink to the bottom
        -(row.get("weight") or 0) if publishable else 0,
        row.get("title") or "",
    )


def queue_row(issue, *, n_comments: int, department_scoped: bool = False) -> dict:
    """One issue, shaped for the queue that already carries proposals.

    ⭐⭐ SHARING A QUEUE MUST NOT MEAN SHARING A VOCABULARY. `kind` and `states`
    travel with the row so a surface cannot reach for the proposal dispositions
    by default — which would be the `type` column by another route.
    """
    wb = weight_block(n=n_comments, department_scoped=department_scoped)
    return {
        "kind": "issue",
        "issue_id": getattr(issue, "id", None),
        "title": getattr(issue, "title", None),
        "status": getattr(issue, "status", "open"),
        "states": list(ISSUE_STATES),
        "state_note": STATE_NOTE.get(getattr(issue, "status", "open")),
        "department_id": getattr(issue, "department_id", None),
        "created_at": getattr(issue, "created_at", None),
        "weight": n_comments,
        "weight_block": wb,
        # ⭐ RESERVED, NOT SILENTLY OCCUPIED. Ratings are ruled and unbuilt; a
        # surface must be able to tell "not rated yet" from "rated zero".
        "rating": None,
    }
