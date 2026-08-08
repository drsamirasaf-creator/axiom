"""The floor for external groups counts ORGANISATIONS, never persons.

## ⛔⭐⭐ THE RULING, AND WHY THE INTERNAL COUNTER WOULD GET IT WRONG

**FOUNDER RULING, 8 Aug: the floor counts DISTINCT ORGANISATIONS.**

`assessment_engine` keys every response on `participant_ref` and compares
`n = len(values)` to `KFLOOR` — **the unit is the individual**. Applied to an
external group that publishes exactly the case the floor exists to withhold:

> **Five respondents from one supplier is `n=5` by person and `n=1` by firm.**
> A person-count floor clears at 3 and publishes a result that describes **one
> nameable company**. A CEO knows their suppliers by name.

⭐⭐ **This is "KFLOOR follows the RESPONDENT, not the table" applied correctly:
for an external group the respondent IS the organisation.** Counting people
protects a respondent from their colleagues; counting firms protects the firm
from the company reading the result — and §16.7 asks for the second.

⛔ **`assessment_engine.KFLOOR` is untouched.** The internal path still counts
people, correctly: for employees the risk *is* identifying a colleague. This
module is the external mechanism, and the two coexist because the populations
differ — which is the whole content of the standing ruling.

## ⭐ ONE OR MORE RESPONDENTS PER PARTY — ONE IS THE COMMON CASE, NOT A CONSTRAINT

Several people at one firm produce **one party-level reading**, and the
aggregation happens **before** the floor is applied. Anything that floors first
is counting people again by another route.

## ⛔ AND THE SPREAD IS CARRIED, NEVER DISCARDED

Two contacts at one partner with opposite views is **not noise**. The party
reading carries `n_respondents`, `spread` and `dissent` so a surface can say
*"one reading, and the people behind it disagreed"* — which is a finding, not a
caveat. Averaging it away would delete the most interesting thing on the page.
"""
from statistics import mean, pstdev

# ⛔ PER POPULATION, NOT A GLOBAL — §16.7's asymmetry cannot be expressed by a
# constant, and a rule that could not differ would have been meaningless.
#
#   customers  — large, unnamed. A mean over hundreds identifies nobody.
#   suppliers  — small and NAMED. A CEO can enumerate them from memory.
#   partners   — as suppliers.
#   public     — see UNAFFILIATED below.
FLOOR_BY_KIND = {
    "customer": 0,
    "supplier": 3,
    "partner": 3,
    "public": 0,
}

# ⭐⭐ GROUPS WITH NO FIRM TO BE ONE OF. General Public, Local Communities and
# Media have no organisation behind the respondent — there is nothing to
# aggregate to, and the population is large and unnamed. ⛔ So the party-count
# rule DOES NOT APPLY to them: each respondent is their own party, and the floor
# is the customer rule (none), for the same reason.
UNAFFILIATED = {"public"}

# ⛔ A DISSENT THRESHOLD, STATED. Below this the contacts substantially agree;
# at or above it the surface must say they did not. Named so it is arguable
# rather than implicit.
DISSENT_SD = 1.5


def floor_for(kind):
    """The publication floor for one population. ⛔ Unknown kinds get the
    STRICTER rule, not the looser one — a population nobody classified is not
    evidence that it is safe to publish."""
    return FLOOR_BY_KIND.get(kind, 3)


def aggregate_party(scores):
    """Several respondents at one organisation -> ONE party-level reading.

    ⭐ THE MEAN, and the reason it is the mean rather than a median or a single
    nominated contact: every contact answered the same instrument about the same
    relationship, so each is an equally valid observation of it. A median would
    discard a genuine outlier at n=2 (where it IS the mean anyway), and a
    nominated contact would make the reading depend on who was asked first.

    ⛔ AND THE SPREAD TRAVELS. Two contacts with opposite views is a finding.
    """
    vals = [float(s) for s in scores if s is not None]
    if not vals:
        return None
    sd = pstdev(vals) if len(vals) > 1 else 0.0
    return {
        "value": round(mean(vals), 4),
        "n_respondents": len(vals),
        "spread": round(max(vals) - min(vals), 4) if len(vals) > 1 else 0.0,
        "sd": round(sd, 4),
        # ⛔ NOT a suppression — a LABEL. The reading still publishes; the
        # surface is told the people behind it disagreed.
        "dissent": bool(len(vals) > 1 and sd >= DISSENT_SD),
    }


def publishable(by_party, kind):
    """-> the group reading, or a stated withholding.

    `by_party` is {party_key: [scores...]}. ⛔ THE FLOOR IS APPLIED TO THE COUNT
    OF DISTINCT PARTIES, after aggregation — never to the count of people.
    """
    parties = {k: aggregate_party(v) for k, v in (by_party or {}).items()}
    parties = {k: v for k, v in parties.items() if v is not None}
    n_parties = len(parties)
    n_people = sum(p["n_respondents"] for p in parties.values())
    floor = floor_for(kind)

    base = {"kind": kind, "floor": floor, "counts": "organisations",
            "n_parties": n_parties, "n_respondents": n_people}
    if n_parties == 0:
        return {**base, "publishable": False, "state": "unrated", "value": None,
                "note": "No one has answered yet."}
    if n_parties < floor:
        # ⭐ THE COUNT IS ALWAYS SHOWN — it is what makes "withheld" credible
        # rather than indistinguishable from silence, and a bare count
        # identifies nobody.
        return {**base, "publishable": False, "state": "below_floor",
                "value": None,
                "note": (f"{n_people} response(s) from {n_parties} "
                         f"organisation(s) — withheld until {floor} "
                         f"organisations are in. Five people at one supplier "
                         f"still describe one nameable company.")}
    vals = [p["value"] for p in parties.values()]
    return {**base, "publishable": True, "state": "rated",
            "value": round(mean(vals), 4),
            "dissent_parties": sum(1 for p in parties.values() if p["dissent"]),
            "note": None}


def publish_set(groups):
    """Several sibling groups at once, with complement inference closed.

    ⛔⭐⭐ SUPPRESSION IS A PROPERTY OF THE SET, NOT A ROW. With three supplier
    firms, publishing two and withholding one reconstructs the third by
    subtraction whenever the total is also known. The internal engine already
    reasons this way — Meridian's HR sat AT n=3, not below, and was hidden only
    to cover Supply Chain's n=2.

    ⭐ So when exactly one member of a set is withheld, a second is withheld
    with it — the smallest of the publishable ones, because withholding the
    smallest costs the least information.
    """
    out = {name: publishable(by_party, kind)
           for name, (by_party, kind) in (groups or {}).items()}
    withheld = [n for n, r in out.items() if not r["publishable"]]
    if len(withheld) == 1 and len(out) > 1:
        others = sorted((n for n in out if n not in withheld),
                        key=lambda n: out[n]["n_parties"])
        victim = others[0]
        out[victim] = {**out[victim], "publishable": False, "value": None,
                       "state": "withheld_to_protect_sibling",
                       "note": ("withheld because one sibling group is below "
                                "the floor and publishing every other member "
                                "would reconstruct it by subtraction")}
    return out


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⭐⭐ ATTRIBUTION — EXTERNAL ONLY, AND THE BOUNDARY MUST NOT BLUR
# ═══════════════════════════════════════════════════════════════════════════
# FOUNDER RULING, 8 Aug: external stakeholders are ATTRIBUTED, not anonymous.
# External parties generally WANT to be named — a supplier flagging a problem
# wants management to know who is unhappy and about what, and anonymity defeats
# the purpose of the instrument.
#
# ⛔ INTERNAL GROUPS ARE UNCHANGED. Employees, Managers and Supervisors, Senior
# Executives and Board Members remain anonymous under §4u-c. The instruments
# already carry `orientation: internal|external`, and THAT FIELD IS THE
# BOUNDARY. An internal response can never become attributed, whatever consent
# is recorded against it — because the consent an employee gave was to an
# anonymous instrument, and a later flag cannot retroactively change what they
# agreed to.
INTERNAL = "internal"
EXTERNAL = "external"


class InternalAttributionRefused(Exception):
    """⛔ Raised, never silently ignored. Dropping the request would let a
    caller believe the attribution took effect — the same reasoning §4u-c gives
    for `assign()` RAISING on a comment kwarg rather than stripping it."""


def may_attribute(orientation, consented):
    """Can this response carry a name? -> bool. ⛔ Both conditions, never one.

    ⭐ Consent is necessary and NOT sufficient: an internal respondent who ticks
    a box is still internal, and §4u-c governs them.
    """
    if orientation != EXTERNAL:
        return False
    return bool(consented)


def attribute(orientation, consented, party_name):
    """The name to publish, or None. ⛔ REFUSES on an internal response rather
    than returning None, so a caller cannot read silence as 'no name available'
    when the truth is 'this may never be named'."""
    if orientation == INTERNAL:
        raise InternalAttributionRefused(
            "an internal response can never be attributed — §4u-c governs "
            "employees, managers, senior executives and board members, and the "
            "consent they gave was to an ANONYMOUS instrument")
    if orientation != EXTERNAL:
        raise InternalAttributionRefused(
            f"unknown orientation {orientation!r} — attribution requires an "
            f"explicitly EXTERNAL instrument, and an unclassified one is not it")
    return party_name if consented else None


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⭐⭐ THE DECLINING SUBSET — DECLINING DOES NOT ESCAPE THE FLOOR
# ═══════════════════════════════════════════════════════════════════════════
# Nine external parties consenting and one declining makes the tenth THE MOST
# IDENTIFIABLE PARTY IN THE SYSTEM: the group is named, the decliner is the one
# name absent from it, and the arithmetic below recovers their answer exactly.
#
# ⭐ THE ADVERSARY IS EXPLICIT, and it is not a clever attack — it is one
# subtraction. Given the published group mean over N parties and the individual
# values of the K consenting ones, the decliners' mean is
#
#     (N * mean - sum(consenting)) / (N - K)
#
# which is EXACT at N-K = 1 and narrowing for small N-K.


def decliner_derivable(n_parties, group_mean, consenting_values):
    """Can a reader recover the declining subset's reading? -> dict.

    ⭐ Stated as a MEASUREMENT rather than a policy, so a surface can decide what
    to publish and a test can assert the decision held.
    """
    k = len(consenting_values)
    n_declining = n_parties - k
    if n_parties <= 0 or n_declining <= 0 or group_mean is None:
        return {"derivable": False, "n_declining": max(n_declining, 0),
                "reason": "no declining party, or nothing published"}
    if k == 0:
        return {"derivable": False, "n_declining": n_declining,
                "reason": "no consenting values are published, so nothing "
                          "can be subtracted"}
    recovered = (n_parties * group_mean - sum(consenting_values)) / n_declining
    return {
        "derivable": True,
        "n_declining": n_declining,
        # ⛔ EXACT when one party declined; a mean over the subset otherwise —
        # and a mean over two is still close enough to name a view.
        "exact": n_declining == 1,
        "recovered": round(recovered, 4),
        "reason": (f"the group mean over {n_parties} parties minus the "
                   f"{k} published consenting values recovers the remaining "
                   f"{n_declining} by subtraction"),
    }


def safe_publication(n_parties, values_by_party, consented_parties):
    """What may be published so the declining subset is not recoverable.

    ⛔ THE OPTIONS ARE THE FOUNDER'S; this implements the one that is safe under
    the adversary above, and NAMES what it withheld so the choice is visible:
    ⭐ **the aggregate publishes; individual named values do not, whenever any
    party declined.** Publishing both is what makes the subtraction possible,
    and it is the combination — not either alone — that leaks.
    """
    parties = {k: v for k, v in (values_by_party or {}).items() if v is not None}
    declining = [p for p in parties if p not in set(consented_parties or ())]
    agg = round(sum(parties.values()) / len(parties), 4) if parties else None
    if not declining:
        return {"aggregate": agg, "named": dict(parties), "withheld": [],
                "why": None}
    # ⛔ the aggregate alone is safe; the named values alongside it are not
    return {
        "aggregate": agg,
        "named": {},
        "withheld": sorted(parties),
        "why": (f"{len(declining)} of {len(parties)} parties declined to be "
                f"named. Publishing the aggregate AND the consenting values "
                f"would recover the declining subset by subtraction, so the "
                f"named values are withheld and only the aggregate publishes."),
    }


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⭐⭐ CONSENT IS SCOPED — IT DOES NOT CARRY FORWARD
# ═══════════════════════════════════════════════════════════════════════════
# A party consents to be named ON A PARTICULAR INSTRUMENT, IN A PARTICULAR
# CYCLE. A re-fielded instrument next quarter is a NEW consent: the relationship
# may have changed, the contract may be up for renewal, and the answer they are
# about to give is not the one they agreed to publish.


def consent_valid_for(consent, instrument_key, cycle_id):
    """Does this stored consent authorise naming HERE? -> bool.

    ⛔ EVERY field must match. A consent with no scope recorded is NOT a
    wildcard — it is an unscoped record, and an unscoped record authorises
    nothing.
    """
    if not consent or not consent.get("consented"):
        return False
    scope_i = consent.get("instrument_key")
    scope_c = consent.get("cycle_id")
    if scope_i is None or scope_c is None:
        return False
    return scope_i == instrument_key and scope_c == cycle_id


def revoke_consent(consent, now=None, note=None):
    """⛔ REVOCABLE — but it does not rewrite what was already published.

    ⭐ A pack is immutable and a board saw what it saw; retracting a name from a
    published artefact is not possible and pretending otherwise would be the
    lie. Revocation stops FUTURE publication and is recorded with its time, so a
    reader of an old artefact can see that consent was later withdrawn.
    """
    from datetime import datetime
    out = dict(consent or {})
    out["consented"] = False
    out["revoked_at"] = (now or datetime.utcnow()).isoformat()
    out["revoked_note"] = note
    out["already_published_unaffected"] = True
    return out
