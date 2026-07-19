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


def compute_cei(items: list[dict], weights: dict, responses: list[dict]) -> dict:
    """Composite Excellence Index across a cycle's participants.

    items: [{level, code, title, parent_code, selected}]
    weights: {l1_code: weight}  (over selected L1, ~sum 100)
    responses: [{participant_ref, code, score}]

    L2 score = mean of scored selected L3 children (children override) else the
    direct L2 score; L1 = mean of its selected L2 scores; participant CEI =
    weight-renormalized L1 mean; the cycle CEI/subscores are the participant
    means, with per-item and per-L1 dispersion across participants.
    """
    sel = [i for i in items if i.get("selected", True)]
    title = {i["code"]: i["title"] for i in items}
    l1 = [i["code"] for i in sel if i["level"] == 1]
    l2_by_l1 = {c: [i["code"] for i in sel if i["level"] == 2 and i["parent_code"] == c] for c in l1}
    l3_by_l2 = {i["code"]: [j["code"] for j in sel if j["level"] == 3 and j["parent_code"] == i["code"]]
                for i in sel if i["level"] == 2}

    # responses grouped by participant -> {code: score}
    parts: dict = {}
    for r in responses:
        parts.setdefault(r["participant_ref"], {})[r["code"]] = float(r["score"])

    per_part_cei, per_part_l1 = [], {c: [] for c in l1}
    for pr, sc in parts.items():
        l1_scores = {}
        for c in l1:
            l2_vals = []
            for l2 in l2_by_l1[c]:
                kids = [k for k in l3_by_l2.get(l2, []) if k in sc]
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

    l1_out = [{"code": c, "title": title.get(c, c), "weight": round(weights.get(c, 0.0), 4),
               "score": round(statistics.mean(per_part_l1[c]), 4) if per_part_l1[c] else None,
               "dispersion": _disp(per_part_l1[c])} for c in l1]

    # per-item dispersion across participants (only items actually scored)
    item_disp = {}
    scored_codes = {code for sc in parts.values() for code in sc}
    for code in scored_codes:
        item_disp[code] = {"title": title.get(code, code),
                           **_disp([sc[code] for sc in parts.values() if code in sc])}

    return {
        "cei": round(statistics.mean(per_part_cei), 4) if per_part_cei else None,
        "n_participants": len(parts),
        "l1_subscores": l1_out,
        "radar": [{"axis": o["title"], "code": o["code"], "score": o["score"],
                   "weight": o["weight"]} for o in l1_out],
        "item_dispersion": item_disp,
    }
