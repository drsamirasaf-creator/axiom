"""Which surfaces are AXIOM Prescience and not AXIOM Business — and the mark.

⭐⭐ THE GAP THIS CLOSES (§4z, self-reported at 66b457a). §4z requires the tier
difference to be visible in three places: the results call, the viewer
experience, and the pricing page. §4y's viewer surface marked nothing.

⭐⭐ THE VIEWER IS WHERE IT MATTERS MOST. Viewers never attend the results call,
and they drive the step-8 decision. A director who spends 30 days in a forward
engine the company will not be buying is exactly the person who feels the loss as
a switch.

⭐⭐ STATED UP FRONT THIS IS AN UPSELL; DISCOVERED AT CHECKOUT IT IS A BAIT. The
same fact — only the timing decides which.

⭐ THE VIEWER IS NOT THE BUYER. The mark states what it MEANS and stops: no
upgrade prompt, no price, no call to action. A viewer who cannot buy being sold
to is an irritation, and it would also leak the commercial motion to the board.

⭐⭐ DERIVED FROM THE TIER DEFINITION, NOT FROM A HAND LIST. CORE's tier
definition is the source: Business includes ALL core product plus **Ask AXIOM
only** from the Prescience layer; Prescience-only is Multiverse, Resilience
Field, Causal Map, Radar/Sentinel and Prescience Brief.

⭐⭐ AND A MARK IS ONLY EMITTED FOR SHIPPED CAPABILITY. Four of the five have no
routes (measured, §7j). ⭐ MARKING A PLACEHOLDER WOULD ADVERTISE, IN A CUSTOMER'S
OWN DATA, A FEATURE THAT DOES NOT EXIST — which is the admissibility failure this
codebase keeps having to withdraw, in the one place a prospect would test it.
"""

# ── the tier definition, encoded once ──────────────────────────────────────
# ⭐ `klass` is the pack INPUT CLASS the feature feeds — the join between a
# commercial tier and a rendered block. `route_marker` is what proves it ships.
#
# ⭐ Ask AXIOM is DELIBERATELY ABSENT: the tier definition puts it in Business as
# a taster, so marking it Prescience-only would be wrong in the expensive
# direction — telling a Business buyer they lose something they keep.
PRESCIENCE_ONLY = {
    "radar_sentinel": {
        "label": "Radar / Sentinel",
        "klass": "sentinel_state",
        "route_marker": "/radar/events",
    },
    "multiverse": {
        "label": "Multiverse",
        "klass": None,
        "route_marker": "/multiverse",
    },
    "resilience_field": {
        "label": "Resilience Field",
        # ⭐⭐ BUILT 1 Aug (§7j.3) — `built()` now measures it True from the
        # route table, as it should.
        #
        # ⭐ `klass` STAYS None DELIBERATELY. The Field renders from
        # `sentinel_state`, which is ALREADY marked under Radar/Sentinel. Naming
        # the same input class twice would collide in `mark_pack` — one label
        # would silently overwrite the other — and would tell a reader the block
        # is Prescience-only twice rather than once.
        "klass": None,
        "route_marker": "/resilience",
    },
    "causal_map": {
        "label": "Causal Map",
        "klass": None,
        "route_marker": "/causal",
    },
    "prescience_brief": {
        "label": "Prescience Brief",
        "klass": None,
        "route_marker": "/prescience/brief",
    },
}

# ⭐ THE SENTENCE, IN ONE PLACE. Repeated at call sites it drifts, and a tier
# statement that differs between two surfaces is worse than one that is absent.
MARK = ("This surface is included in AXIOM Prescience and not in AXIOM Business.")


def built(served_paths):
    """-> {key: bool} measured against the SERVED ROUTE TABLE.

    ⭐ NOT from a status column. §7j measured four of five as having zero
    backend files, and a hand-maintained "built" flag is exactly the record that
    goes stale without anyone noticing.

    ⭐ SUBSTRING MATCHING IS NOT IDENTITY. `route_marker` is a PATH FRAGMENT
    chosen to be unambiguous — searching for "brief" alone matches
    `/initiatives/lead-briefing` and `/api/v1/intelligence/executive-brief`,
    neither of which is the Prescience Brief.
    """
    out = {}
    for key, spec in PRESCIENCE_ONLY.items():
        marker = spec["route_marker"]
        out[key] = any(marker in p for p in served_paths)
    return out


def markable(served_paths):
    """The features that may carry a mark: Prescience-only AND shipped AND
    reaching a rendered block.

    ⭐ THREE CONDITIONS, ALL REQUIRED. A feature that is unbuilt has nothing to
    mark; one with no `klass` reaches no block a viewer opens, so a mark would
    float free of anything on the page.
    """
    b = built(served_paths)
    return {k: v for k, v in PRESCIENCE_ONLY.items()
            if b.get(k) and v["klass"]}


def unmarkable(served_paths):
    """-> [(key, reason)] — ⭐ NAMED, NOT DROPPED. A feature silently omitted
    from the marks is indistinguishable from one nobody considered."""
    b = built(served_paths)
    out = []
    for k, v in PRESCIENCE_ONLY.items():
        if not b.get(k):
            out.append((k, "not built — no route serves it, so there is no "
                           "surface to mark and marking it would advertise a "
                           "feature that does not exist"))
        elif not v["klass"]:
            out.append((k, "built, but the pack block it renders from is already "
                           "marked under another feature — marking it twice would "
                           "collide, not clarify"))
    return out


def mark_pack(payload, served_paths):
    """Annotate a rendered pack with the tier marks. Returns the payload.

    ⭐⭐ THE MARK LANDS ON THE PORTION, NOT THE SECTION. `what is at risk`
    bundles the viability kernel and the Watch — both CORE — with Sentinel.
    Marking the whole section would tell a Business buyer they lose the viability
    kernel, which they do not. Over-marking is not the safe direction: it is a
    different false statement.
    """
    marks = markable(served_paths)
    if not marks:
        return payload
    klasses = {v["klass"]: v["label"] for v in marks.values()}
    sections = (payload or {}).get("sections")
    if not isinstance(sections, list):
        return payload
    for sec in sections:
        if not isinstance(sec, dict):
            continue
        body = sec.get("body")
        if not isinstance(body, dict):
            continue
        hit = []
        for field, blk in body.items():
            # the rendered block keeps its input class under `klass`, or the
            # field is named for it (`sentinel_raw` <- `sentinel_state`)
            name = (blk or {}).get("klass") if isinstance(blk, dict) else None
            for kl, label in klasses.items():
                if name == kl or field.startswith(kl.split("_")[0]):
                    hit.append({"field": field, "feature": label, "note": MARK})
        if hit:
            sec["tier_marks"] = hit
    return payload
