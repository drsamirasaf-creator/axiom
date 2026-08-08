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
