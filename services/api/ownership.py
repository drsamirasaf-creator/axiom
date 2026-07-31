"""Ownership: ONE VALUE, ONE OWNER — the dataset payload.

⭐⭐ WHY THE PAYLOAD AND NOT THE ENTERPRISE ROW. It is what the valuation engine
reads, it is VERSIONED, it is FROZEN INTO THE PACK, and it carries upload
provenance. `enterprises.ownership` has none of those properties: no `updated_at`,
no `updated_by`, no audit row — it is written once at company creation from a
checkbox and nothing records who set it or whether it ever changed.

⭐ THE ENTERPRISE ROW BECOMES DERIVED, NEVER AUTHORITATIVE. It may be read as a
cache; it must not decide anything.

⭐⭐ AND A DEFAULT HERE SILENTLY PICKS A COST-OF-EQUITY MODEL. A company with no
dataset has NO ownership — not "private", not "public". `UNDETERMINED` is a value
this module returns and callers must handle; coercing it to either branch would
choose a valuation method on no evidence, which is the fabricated-zero class
applied to a model selection.
"""
from datetime import datetime

PRIVATE = "private"
PUBLIC = "public"
UNDETERMINED = "undetermined"

# ⭐ The reason is carried WITH the verdict. "undetermined" alone tells a reader
# nothing about whether to wait, upload, or ask someone.
NO_DATASET = ("this company has no financial dataset, so its ownership — and "
              "therefore which cost-of-equity model applies — is not yet "
              "determined")
NOT_STATED = ("the active dataset does not state an ownership, so which "
              "cost-of-equity model applies cannot be determined")


def resolve(db, company_id):
    """The single answer. -> {"ownership", "source", "reason", "dataset_id"}.

    ⭐ NEVER RAISES AND NEVER GUESSES. An absent answer is a reported state.
    """
    from .accounts import _active_company_dataset
    ds = None
    try:
        ds = _active_company_dataset(db, company_id)
    except Exception:
        ds = None
    if ds is None:
        return {"ownership": UNDETERMINED, "source": None,
                "reason": NO_DATASET, "dataset_id": None}
    own = ((ds.data or {}).get("company") or {}).get("ownership")
    if own not in (PRIVATE, PUBLIC):
        return {"ownership": UNDETERMINED, "source": "payload",
                "reason": NOT_STATED, "dataset_id": ds.id}
    return {"ownership": own, "source": "payload", "reason": None,
            "dataset_id": ds.id}


def dlom_permitted(ownership):
    """⭐⭐ A COMPANY PRICED ON THE PUBLIC BRANCH CANNOT CARRY A DLOM.

    A discount for non-marketability on a publicly traded company is
    self-contradictory, and it is the first thing a valuation professional
    checks. The engine already forces DLOM to 0.0 off the payload; this states
    the rule so it cannot return through the RECORD.

    ⭐ UNDETERMINED permits nothing — we do not know it is private.
    """
    return ownership == PRIVATE


def disagreements(db):
    """Every company whose stored row contradicts its active dataset.

    ⭐ THE GUARD'S DATA SOURCE. Returned rather than raised so a caller can
    report all of them rather than the first.
    """
    from .modules.enterprise_state.models import Enterprise
    out = []
    for e in db.query(Enterprise).all():
        r = resolve(db, e.id)
        stored = (e.ownership or None)
        if r["ownership"] == UNDETERMINED:
            # ⭐⭐ PENDING IS NOT A CONTRADICTION, AND CONFLATING THEM WOULD MAKE
            # THIS GATE UNPASSABLE. A company created but not yet uploaded holds
            # the creation checkbox's answer and NOTHING CONTRADICTS IT — there
            # is simply no payload yet. A gate that cannot pass is a gate nobody
            # runs, and the four such companies live today are ordinary.
            #
            # ⭐ It is still REPORTED, because a stored value with no evidence
            # behind it must not read as confirmed.
            if stored:
                out.append({"company_id": e.id, "stored": stored,
                            "derived": UNDETERMINED, "kind": "pending",
                            "reason": r["reason"]})
            continue
        if stored != r["ownership"]:
            out.append({"company_id": e.id, "stored": stored,
                        "derived": r["ownership"], "kind": "contradiction",
                        "dataset_id": r["dataset_id"],
                        "reason": "the stored row contradicts the active dataset"})
    return out


def contradictions(db):
    """⭐ ONLY the rows a payload actively refutes — what the gate fails on."""
    return [d for d in disagreements(db) if d.get("kind") == "contradiction"]


def pending(db):
    """⭐ Rows awaiting their first dataset. Reported, never failed on."""
    return [d for d in disagreements(db) if d.get("kind") == "pending"]


def reconcile(db, company_id, *, user=None, now=None, reason=None):
    """Point the derived row at the payload, and RECORD THE CHANGE.

    ⭐ FIELD-LEVEL PROVENANCE. The provenance law: a field that selects which
    cost-of-equity model runs, with no record of who set it, is the law's shape
    again. This writes the trail `enterprises.ownership` never had.
    """
    from .assumptions_api import AssumptionEdit
    from .modules.enterprise_state.models import Enterprise
    now = now or datetime.utcnow()
    ent = db.get(Enterprise, company_id)
    if ent is None:
        return None
    r = resolve(db, company_id)
    if r["ownership"] == UNDETERMINED:
        # ⭐ NOTHING IS WRITTEN. We will not clear a stored value on the strength
        # of an absence, and we will not invent one.
        return {"changed": False, "ownership": UNDETERMINED,
                "reason": r["reason"], "stored": ent.ownership}
    prior = ent.ownership
    if prior == r["ownership"]:
        return {"changed": False, "ownership": prior, "reason": "already agrees"}
    ent.ownership = r["ownership"]
    db.add(AssumptionEdit(
        company_id=company_id, occurred_at=now,
        actor_user_id=getattr(user, "id", None),
        actor_label=(getattr(user, "name", None)
                     or getattr(user, "email", "") or ""),
        dataset_id=r["dataset_id"], field="ownership",
        prior_value=None, new_value=None, prior_absent=0 if prior else 1,
        bound_state="derived",
        bound_note=(f"ownership derived from the active dataset payload: "
                    f"{prior!r} -> {r['ownership']!r}"),
        reason=reason or "reconciled to the payload, the single owner"))
    db.flush()
    return {"changed": True, "ownership": r["ownership"], "prior": prior,
            "dataset_id": r["dataset_id"]}
