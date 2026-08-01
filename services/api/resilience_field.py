"""Resilience Field — the region of parameter space in which the company remains
viable.

⭐⭐ RULED 1 Aug (§7j.2 ruling 3): the Field is `breakeven_radius` plus shocks
over the viability kernel — **rendering over existing computation, not a new
engine.** ⭐ MEASURED BEFORE BUILDING AND THE RULING HOLDS: `sentinel._nearest_t`
already bisects along each shock ray to the failure surface, and all seven
distances are persisted in `ax_viability.payload["distances"]`.

⭐⭐ THE FIELD IS THE REGION, NOT A NUMBER. A single distance figure is a weaker
claim than a boundary a reader can see themselves against: *"revenue can fall 47%
before the band breaks, and you are here"* is checkable; *"resilience 0.63"* is
not.

⭐⭐ NO NEW CALCULATION. This module reads a STORED payload and converts to
natural units. It never recomputes, never calls a detector, and never opens a
dataset. ⭐ If a number is not already computed it is ABSENT AND STATED — the
standing §7s discipline applied to Prescience: the layer publishes what exists.

⭐⭐ AND THE CENSORING IS THE FINDING THIS MODULE EXISTS TO GET RIGHT.
`_nearest_t` returns `T_MAX` when a ray does NOT fail. So a distance of exactly
`T_MAX` means **"did not break within the tested range"**, NOT "breaks here".
Rendering it as a boundary would tell a CEO their revenue can fall exactly 50%
when the truth is *it was never made to fail*. ⭐ FOUR OF MERIDIAN'S SEVEN RAYS
ARE CENSORED, so this is the common case, not an edge.
"""

# ⭐ The natural-unit label for each dimension, and how a distance t converts.
# `SHOCK_REF` lives in sentinel and is carried IN THE PAYLOAD, so a stored result
# renders against the reference it was computed with — never today's constant.
DIM_LABEL = {
    "revenue": ("revenue decline", "fraction"),
    "margin": ("margin compression", "pp of revenue"),
    "rate": ("rate rise", "pp on cost of debt"),
    "wc": ("working-capital build", "fraction"),
}

# ⭐ Which rays are single parameters (the axes of the field) and which are named
# combinations (points inside it). Both are rendered; conflating them would
# suggest the company has seven independent dimensions of room.
COMBO_RAYS = ("recession", "stagflation", "credit_crunch")


def _natural(dims, t, shock_ref):
    """t -> the magnitude on each dimension it represents, in natural units.

    ⭐ Returns absent rather than guessing when the reference is missing: a
    magnitude computed against the wrong reference is a wrong number that looks
    right.
    """
    out = {}
    for d, w in (dims or {}).items():
        ref = (shock_ref or {}).get(d)
        if ref is None:
            out[d] = {"absent": f"no shock reference for '{d}' in the stored payload"}
            continue
        label, unit = DIM_LABEL.get(d, (d, ""))
        out[d] = {"label": label, "unit": unit, "magnitude": round(t * w * ref, 4)}
    return out


def field(payload, *, rays=None):
    """-> the Field, rendered from a STORED viability payload. Pure.

    `payload` is `ax_viability.payload` (or the frozen copy of it). `rays` is the
    ray definition map; when absent the combos cannot be distinguished from the
    axes and that is stated rather than assumed.
    """
    if not payload:
        return {"has_data": False,
                "absent": "no viability result has been computed for this company",
                "dimensions": [], "band": None}

    distances = payload.get("distances") or {}
    shock_ref = payload.get("shock_reference") or {}
    thresholds = payload.get("thresholds") or {}
    # ⭐ T_MAX is not in the payload; it is the value the kernel returns for a
    # ray that never failed. The maximum observed distance IS that ceiling when
    # any ray reached it, and we say so rather than importing today's constant —
    # a stored result must render against its own run.
    ceiling = max(distances.values()) if distances else None

    dims = []
    for name in sorted(distances):
        t = distances[name]
        direction = (rays or {}).get(name)
        entry = {
            "ray": name,
            "kind": "combination" if name in COMBO_RAYS else "axis",
            "distance": t,
        }
        if direction is None:
            # ⭐ ABSENCE DECLARES, PER PARAMETER. Never zero, never omitted — a
            # field with a silently missing dimension misstates how much room
            # the company has, and that is the expensive direction.
            entry["state"] = "absent"
            entry["absent"] = ("the ray's composition is not recorded, so the "
                               "distance cannot be expressed in natural units")
        elif ceiling is not None and t >= ceiling - 1e-9 and t >= 1.0 - 1e-9:
            # ⭐⭐ RIGHT-CENSORED. The ray did not fail within the tested range.
            entry["state"] = "censored"
            entry["at_least"] = _natural(direction, t, shock_ref)
            entry["absent"] = ("no breach within the tested range — the boundary "
                               "is beyond this, not at it")
        elif t <= 1e-6:
            entry["state"] = "breached"
            entry["absent"] = "already in breach at current conditions"
        else:
            entry["state"] = "measured"
            entry["boundary"] = _natural(direction, t, shock_ref)
        dims.append(entry)

    measured = [d for d in dims if d["state"] == "measured"]
    censored = [d for d in dims if d["state"] == "censored"]
    return {
        "has_data": bool(dims),
        "band": payload.get("band"),
        "overall_distance": payload.get("overall_distance"),
        "thresholds": thresholds,
        # ⭐ WHERE THE COMPANY SITS INSIDE THE REGION, not just how big it is.
        "position": payload.get("nearest_breach"),
        "dimensions": dims,
        # ⭐ COVERAGE, ON THE SURFACE ITSELF. "4 of 7 measured" is the difference
        # between a field and a field with holes in it, and a reader cannot infer
        # it from the dots.
        "coverage": {"total": len(dims), "measured": len(measured),
                     "censored": len(censored),
                     "absent": len(dims) - len(measured) - len(censored)},
        "reverse_stress": REVERSE_STRESS_ABSENT,
    }


# ⭐⭐ REVERSE-STRESS — MEASURED AND ABSENT, NOT BUILT (item 4). CORE's clause
# names "stress/reverse-stress". Nothing computes a reverse-stress test: the
# kernel bisects FORWARD from today to the failure surface. `_prescribe` searches
# the lever library for the minimum intervention that RESTORES stability, which
# is adjacent but is not the same question — it asks what fixes a breach, not
# what magnitude of adverse move would cause one from a stated loss.
REVERSE_STRESS_ABSENT = {
    "present": False,
    "absent": ("reverse-stress is not computed. The kernel bisects forward to "
               "the nearest failure surface; it does not solve for the shock "
               "that produces a stated loss."),
}


def from_viability_row(row, rays=None):
    """The Field for a stored `Viability` row. ⭐ Reads the row, never the data."""
    return field(getattr(row, "payload", None), rays=rays)


def include(app, get_db, require_company_member):
    """⭐ WIRED, and the wiring is asserted. Ten built-but-not-wired instances."""
    from fastapi import APIRouter, Depends

    r = APIRouter(tags=["prescience"])

    @r.get("/companies/{company_id}/resilience-field")
    def resilience_field(company_id: int, db=Depends(get_db),
                         _m=Depends(require_company_member)):
        """⭐⭐ READS THE STORED VIABILITY ROW. It never recomputes: a surface
        that recomputes on read would drift from the pack that froze it, and the
        whole point of the Field is that a reader can hold it against a number
        someone else quoted.
        """
        from .sentinel import RAYS, Viability
        row = (db.query(Viability).filter_by(company_id=company_id)
                 .order_by(Viability.dataset_version.desc(),
                           Viability.computed_at.desc()).first())
        if row is None:
            # ⭐ ABSENCE DECLARES. An empty field reads as "there is no room".
            return {"has_data": False, "dimensions": [], "band": None,
                    "absent": ("the viability kernel has not run for this company "
                               "yet, so no boundary has been measured"),
                    "reverse_stress": REVERSE_STRESS_ABSENT}
        out = from_viability_row(row, rays=RAYS)
        out["computed_at"] = row.computed_at.isoformat() if row.computed_at else None
        out["dataset_version"] = row.dataset_version
        return out

    app.include_router(r)
