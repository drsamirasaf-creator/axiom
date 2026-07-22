"""AXIOM Assessment Framework — pure taxonomy + CEI computation (Phase 7d-1).

Content-agnostic: the taxonomy JSON (13 L1 / 78 L2 / L3 in production, a small
sample in the repo) is loaded and flattened into items; the CEI math is
independent of the specific content so the canonical framework drops in with no
code change.
"""
import json
import os
import statistics


def load_taxonomy() -> dict:
    """The canonical taxonomy (versioned platform content)."""
    from .core.refassessment import taxonomy
    return taxonomy()


def taxonomy_to_items(tax: dict) -> list[dict]:
    """Flatten to item dicts: {level, code, title, definition, parent_code,
    orientation}. L2 nests under 'items' (canonical) or 'subcategories'; L3
    under 'children'. orientation ("internal"|"external", v2+) is present on
    L2/L3 and None on L1."""
    items = []
    for cat in tax["categories"]:
        items.append({"level": 1, "code": cat["code"], "title": cat["title"],
                      "definition": cat.get("definition", ""), "parent_code": None,
                      "orientation": None})
        for sub in (cat.get("items") or cat.get("subcategories") or []):
            items.append({"level": 2, "code": sub["code"], "title": sub["title"],
                          "definition": sub.get("definition", ""),
                          "parent_code": cat["code"],
                          "orientation": sub.get("orientation")})
            for ch in sub.get("children", []):
                items.append({"level": 3, "code": ch["code"], "title": ch["title"],
                              "definition": ch.get("definition", ""),
                              "parent_code": sub["code"],
                              "orientation": ch.get("orientation")})
    return items


def orientation_by_code(tax: dict) -> dict:
    """{code: orientation} for every L2/L3 in the taxonomy — used to backfill
    orientation onto existing per-company framework items by code."""
    return {it["code"]: it["orientation"]
            for it in taxonomy_to_items(tax) if it["orientation"]}


def score_rag(mean) -> str | None:
    """Deterministic band from a mean score: green >=7.5, amber 5-7.5, red <5."""
    if mean is None:
        return None
    if mean >= 7.5:
        return "green"
    if mean >= 5.0:
        return "amber"
    return "red"


_RAG_LEVEL = {"red": 0, "amber": 1, "green": 2}
_SENTIMENT_RAG = {"positive": "green", "neutral": "amber", "mixed": "amber",
                  "negative": "red"}


def rag_divergence(srag, text_sentiment) -> bool:
    """Material divergence between the score RAG and text sentiment: >=2 RAG
    levels apart (which is exactly green-score vs negative/red-text)."""
    if not srag or not text_sentiment:
        return False
    trag = _SENTIMENT_RAG.get(text_sentiment)
    if trag is None:
        return False
    return abs(_RAG_LEVEL[srag] - _RAG_LEVEL[trag]) >= 2


def default_weights(l1_codes: list[str], provided: dict | None = None) -> dict:
    """Equal-weight default over the L1 categories (summing to 100), unless the
    taxonomy supplies a full valid weight set."""
    if provided and all(provided.get(c) is not None for c in l1_codes) \
            and abs(sum(provided[c] for c in l1_codes) - 100.0) < 0.01:
        return {c: float(provided[c]) for c in l1_codes}
    eq = round(100.0 / len(l1_codes), 6) if l1_codes else 0.0
    return {c: eq for c in l1_codes}


def renormalize(weights: dict) -> dict:
    """Rescale a weight map so the remaining categories sum to 100 (used when a
    category is removed)."""
    total = sum(weights.values())
    if total <= 0:
        n = len(weights)
        return {c: round(100.0 / n, 6) for c in weights} if n else {}
    return {c: round(w * 100.0 / total, 6) for c, w in weights.items()}


def _disp(values: list[float]) -> dict:
    vals = [v for v in values if v is not None]
    if not vals:
        return {"n": 0, "mean": None, "std": None, "min": None, "max": None}
    return {"n": len(vals), "mean": round(statistics.mean(vals), 4),
            "std": round(statistics.pstdev(vals), 4) if len(vals) > 1 else 0.0,
            "min": round(min(vals), 4), "max": round(max(vals), 4)}


def _aggregate_core(items: list[dict], weights: dict, responses: list[dict]) -> dict:
    """Single-slice CEI aggregate (company-wide OR one department subset).

    responses: [{participant_ref, code, score, department?}]. A response with
    score None is an ABSTENTION: the respondent explicitly declined to score that
    item. Abstentions are EXCLUDED from every mean (never counted as zero) but DO
    count the person as a respondent, and feed the abstention meta-signal.

    L2 score = mean of scored selected L3 children (children override) else the
    direct L2 score; L1 = mean of its selected L2 scores; participant CEI =
    weight-renormalized L1 mean; the slice CEI/subscores are the participant
    means, with per-item and per-L1 dispersion across participants.
    """
    sel = [i for i in items if i.get("selected", True)]
    title = {i["code"]: i["title"] for i in items}
    l1 = [i["code"] for i in sel if i["level"] == 1]
    l2_by_l1 = {c: [i["code"] for i in sel if i["level"] == 2 and i["parent_code"] == c] for c in l1}
    l3_by_l2 = {i["code"]: [j["code"] for j in sel if j["level"] == 3 and j["parent_code"] == i["code"]]
                for i in sel if i["level"] == 2}

    # group by participant, separating scored items from abstentions
    parts: dict = {}                 # ref -> {code: float score}  (scored only)
    abst: dict = {}                  # ref -> set(codes abstained)
    for r in responses:
        ref, code, sc = r["participant_ref"], r["code"], r.get("score")
        if sc is None:
            abst.setdefault(ref, set()).add(code)
        else:
            parts.setdefault(ref, {})[code] = float(sc)
    all_refs = set(parts) | set(abst)     # everyone who submitted (incl. all-abstain)

    per_part_cei, per_part_l1 = [], {c: [] for c in l1}
    for ref in all_refs:
        sc = parts.get(ref, {})
        l1_scores = {}
        for c in l1:
            l2_vals = []
            for l2 in l2_by_l1[c]:
                kids = [k for k in l3_by_l2.get(l2, []) if k in sc]   # abstained L3s absent from sc
                if kids:
                    l2_vals.append(statistics.mean(sc[k] for k in kids))   # children override
                elif l2 in sc:
                    l2_vals.append(sc[l2])
            if l2_vals:
                l1_scores[c] = statistics.mean(l2_vals)
        for c, v in l1_scores.items():
            per_part_l1[c].append(v)
        if l1_scores:
            wsum = sum(weights.get(c, 0.0) for c in l1_scores) or 1.0
            per_part_cei.append(sum(weights.get(c, 0.0) * v for c, v in l1_scores.items()) / wsum)

    # per-item scored values + abstention counts across participants
    scored_by_code: dict = {}
    abst_by_code: dict = {}
    for ref in all_refs:
        for code, v in parts.get(ref, {}).items():
            scored_by_code.setdefault(code, []).append(v)
        for code in abst.get(ref, set()):
            abst_by_code[code] = abst_by_code.get(code, 0) + 1

    item_disp, abst_rate_item, no_signal_items = {}, {}, []
    for code in set(scored_by_code) | set(abst_by_code):
        vals = scored_by_code.get(code, [])
        ab = abst_by_code.get(code, 0)
        addressed = len(vals) + ab
        d = {"title": title.get(code, code), **_disp(vals),
             "abstained_n": ab, "addressed_n": addressed,
             "no_signal": len(vals) == 0 and ab > 0}
        item_disp[code] = d
        abst_rate_item[code] = round(ab / addressed, 4) if addressed else None
        if d["no_signal"]:
            no_signal_items.append(code)

    # per-axis (L1) abstention rate over the axis's L2+L3 items
    abst_rate_axis = {}
    for c in l1:
        codes = set()
        for l2 in l2_by_l1[c]:
            codes.add(l2); codes.update(l3_by_l2.get(l2, []))
        tot_ab = sum(abst_by_code.get(k, 0) for k in codes)
        tot_addr = sum(len(scored_by_code.get(k, [])) + abst_by_code.get(k, 0) for k in codes)
        abst_rate_axis[c] = round(tot_ab / tot_addr, 4) if tot_addr else None

    l1_out = [{"code": c, "title": title.get(c, c), "weight": round(weights.get(c, 0.0), 4),
               "score": round(statistics.mean(per_part_l1[c]), 4) if per_part_l1[c] else None,
               "dispersion": _disp(per_part_l1[c]),
               "abstention_rate": abst_rate_axis.get(c)} for c in l1]

    return {
        "cei": round(statistics.mean(per_part_cei), 4) if per_part_cei else None,
        "n_participants": len(all_refs),
        "l1_subscores": l1_out,
        "radar": [{"axis": o["title"], "code": o["code"], "score": o["score"],
                   "weight": o["weight"]} for o in l1_out],
        "item_dispersion": item_disp,
        "abstention_rates": {"item": abst_rate_item, "axis": abst_rate_axis},
        "no_signal_items": no_signal_items,
    }


def compute_cei(items: list[dict], weights: dict, responses: list[dict]) -> dict:
    """Company-wide CEI aggregate + per-department slices (§4i-b layer 1).

    A response may carry an optional `department` (inherited from the participant).
    When any real department tag is present the aggregate gains a `departments`
    map — each value the SAME shape as the company-wide aggregate, computed over
    that department's respondents. Respondents with no tag form an "(unassigned)"
    slice so the department slices remain an exact partition of respondents (this
    is what makes the k-anonymity complement math well-defined downstream).
    Storage-level output is RAW; k-anonymity suppression is applied at
    serialization by `apply_kfloor`, never here.
    """
    agg = _aggregate_core(items, weights, responses)
    by_dept: dict = {}
    for r in responses:
        by_dept.setdefault(r.get("department") or "(unassigned)", []).append(r)
    real = [d for d in by_dept if d != "(unassigned)"]
    agg["departments"] = ({d: _aggregate_core(items, weights, rs) for d, rs in by_dept.items()}
                          if real else {})
    return agg


# ---------------------------------------------------------------- k-anonymity
KFLOOR = 3                       # minimum respondents per serialized slice


def _suppressed(n: int, extra: dict | None = None) -> dict:
    out = {"suppressed": True, "n": n, "reason": "below_anonymity_floor"}
    if extra:
        out.update(extra)
    return out


def _floor_items(item_disp: dict) -> dict:
    """Per-item display gate: an item scored by fewer than KFLOOR respondents is
    replaced by a suppression marker (its all-abstain no-signal flag survives, as
    that reveals no individual score)."""
    out = {}
    for code, d in (item_disp or {}).items():
        if not isinstance(d, dict) or (d.get("n") or 0) < KFLOOR:
            out[code] = _suppressed((d or {}).get("n") or 0,
                                    {"no_signal": True} if (d or {}).get("no_signal") else None)
        else:
            out[code] = d
    return out


def _show_slice(a: dict) -> dict:
    """A department slice that clears the floor: shown, but its own items are still
    floored, and it carries no nested departments."""
    out = dict(a)
    out["item_dispersion"] = _floor_items(a.get("item_dispersion") or {})
    out["suppression"] = None
    out.pop("departments", None)
    return out


def _apply_dept_kfloor(depts: dict) -> dict:
    """Department slices are an exact partition of respondents, so a suppressed
    slice can be reconstructed by subtracting the shown slices from the whole.

    COMPLEMENT-INFERENCE RULE (as implemented): after the primary n<KFLOOR floor
    marks small slices for suppression, if EXACTLY ONE slice is suppressed it is
    the unique arithmetic complement of the shown slices (total − shown) and its
    aggregate is derivable — so we additionally suppress the smallest shown slice.
    We repeat until the number of hidden slices is 0 or ≥2; with ≥2 unknowns
    against the single total-equation, no individual hidden slice is derivable.
    """
    if not depts:
        return {}
    status = {d: ("suppress" if (a.get("n_participants", 0) < KFLOOR) else "show")
              for d, a in depts.items()}
    # complement guard: never leave exactly one hidden slice
    while sum(1 for s in status.values() if s == "suppress") == 1:
        shown = [d for d, s in status.items() if s == "show"]
        if not shown:
            break
        status[min(shown, key=lambda d: depts[d].get("n_participants", 0))] = "suppress"
    return {d: (_suppressed(a.get("n_participants", 0)) if status[d] == "suppress"
                else _show_slice(a))
            for d, a in depts.items()}


def apply_kfloor(agg: dict) -> dict:
    """Display-safe view of a raw aggregate (storage untouched). Company-wide n<
    KFLOOR suppresses every value (cei, subscores, radar, dispersion, department
    slices, abstention rates) while keeping the respondent count; above the floor,
    per-item and per-department slices are gated individually."""
    if not agg:
        return {}
    n = agg.get("n_participants", 0)
    out = dict(agg)
    if n < KFLOOR:
        out["cei"] = None
        out["l1_subscores"] = []
        out["radar"] = []
        out["item_dispersion"] = {}
        out["departments"] = {}
        out["abstention_rates"] = {"item": {}, "axis": {}}
        out["no_signal_items"] = []
        out["suppression"] = _suppressed(n)
        return out
    out["suppression"] = None
    out["item_dispersion"] = _floor_items(agg.get("item_dispersion") or {})
    out["departments"] = _apply_dept_kfloor(agg.get("departments") or {})
    return out
