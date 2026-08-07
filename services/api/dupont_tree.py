"""DuPont as a NODE TREE. It holds the STRUCTURE and nothing else.

⭐⭐ IT COMPUTES NOTHING, AND IT NO LONGER READS ANYTHING EITHER. Every value,
label, operand, basis and absence reason on this payload comes from
`ratio_registry.explain` — the same call the ratios surface has used since R7.
This module owns only what nothing else does: **which node is whose child**,
how absence travels upward, the reconciliation, and the attribution.

## ⛔⭐⭐ IT WAS A SECOND PRODUCER, AND IT LOST (§7r-O)

The first version resolved its own operands, looked up its own registry rows and
captioned its own leaves. Measured this lane, `explain` already returned every
one of those — **better in three places**:

| | this module's first version | `explain` |
|---|---|---|
| which operands a factor has | a hand-written `_OPERANDS` map | **parsed from the formula** |
| the caption | `templates.LABELS` via the vocabulary's `field:` | `display_name(token, standard)` — **the client's own standard** |
| `avg(bs.total_assets)` in the first period | ⛔ returned a period-end number still labelled `basis: "average"` until I fixed it by hand last lane | **already absent, "no opening balance for an average"** |

⭐⭐ THE THIRD ROW IS THE ONE THAT MATTERS. I found that defect by measuring,
wrote a regression test for it, and shipped the fix — and the correct behaviour
had been sitting in the owner the whole time. **A second producer does not just
duplicate an owner; it re-earns the owner's bug fixes one incident at a time.**

⛔ AND THE FACTOR LIST IS NOT HAND-WRITTEN EITHER. `axiom.dupont_three_step`'s
formula IS `net_margin * asset_turnover * financial_leverage`, so the three
children are read from the registry. A tuple here would have been a fourth
place to edit when the identity changes.

## ⭐ THE SHAPE

    ROE                            ← axiom.roe
     ├─ net_margin                 ← the three leaves of the identity's formula
     │    ├─ is.pat                ← each factor's own operands, from ITS formula
     │    └─ is.revenue
     ├─ asset_turnover
     │    ├─ is.revenue
     │    └─ avg(bs.total_assets)
     └─ financial_leverage
          ├─ avg(bs.total_assets)
          └─ bs.equity

⛔ ABSENCE PROPAGATES PER NODE, AND EVERY POINT CARRIES ITS OWN STATE. A node
whose input is missing renders **absent with the reason**, never zero — and a
parent whose child is absent is absent too, because the product of an absent
factor is not a number. A 4-of-5 series ships four observed points and one
absent one; it must never become a 5-point line with an invented value.

⛔ IMPLICATIONS ARE ABSENT, DELIBERATELY. Measured 7 Aug: nothing in the
codebase owns "what this means" for a ratio. Every node carries
`implication: None` and the payload says why, so a surface renders that as
absent rather than as blank.
"""
import math

from .modules.financials import engines as FE
from .modules.financials import ratio_registry as RR

# the states a node's value can be in
OBSERVED = "observed"
ABSENT = "absent"
DERIVED = "derived"

ROOT = "axiom.roe"
IDENTITY = "axiom.dupont_three_step"


def factors():
    """The three factors, READ OFF THE IDENTITY'S FORMULA (§7r-O).

    ⛔ Not a tuple in this file. If the registry ever restates the identity —
    a five-step DuPont splits net margin into tax burden, interest burden and
    operating margin — the tree follows without an edit here.
    """
    _v, _g, ratios = RR._index()
    row = ratios.get(IDENTITY) or {}
    toks = RR._leaf_tokens(RR._parse(row["formula"]))
    # ⭐ ORDER IS THE FORMULA'S ORDER, so the tree reads left-to-right the way
    # the identity is written. `_leaf_tokens` may return a set; sort by where
    # each token appears in the formula text rather than alphabetically.
    return tuple(sorted((t for t in toks if t in ratios),
                        key=lambda t: row["formula"].index(t)))


def _explained(data, years, i, qid, supplied):
    """One node from THE OWNER. No second reader, no second caption."""
    return RR.explain(data, years, i, qid, supplied=supplied)


def _leaf(op, period):
    """An operand, as `explain` already reported it.

    ⭐ THE BASIS IS IN THE OPERAND'S OWN TEXT. `avg(bs.total_assets)` and
    `bs.equity` state structurally which term is averaged and which is
    period-end — no note has to say it in prose.
    """
    text = op.get("text") or ""
    return {
        "id": text,
        "label": op.get("text_display") or text,
        "role": op.get("role"),
        "value": op.get("value"),
        "status": ABSENT if op.get("value") is None else OBSERVED,
        # ⛔ THE REASON TRAVELS. An absent leaf with no reason is a blank cell
        # the reader cannot act on.
        "absence_reason": op.get("absent"),
        "period": period,
        "basis": "average" if text.startswith("avg(") else "period_end",
        # a stored line has no formula, and no definition this module may write
        "formula": None,
        "definition": None,
        "unit": None,
        "needs": None,
        "needs_display": None,
        "implication": None,
        "children": [],
    }


def _node(data, years, i, qid, supplied, *, children=None):
    e = _explained(data, years, i, qid, supplied)
    kids = children if children is not None else [
        _leaf(o, years[i]) for o in (e.get("operands") or [])]
    value, reason = e.get("value"), e.get("absent")
    status = ABSENT if value is None else OBSERVED
    # ⛔ ABSENCE PROPAGATES UPWARD. A parent whose child is absent cannot be
    # observed, whatever the evaluator returned.
    if any(k["status"] == ABSENT for k in kids) and status == OBSERVED:
        value, status = None, ABSENT
        reason = reason or next(
            (k["absence_reason"] for k in kids if k["absence_reason"]), None)
    return {
        "id": qid,
        "label": e.get("name") or qid,
        "value": value,
        "status": status,
        "absence_reason": reason,
        "needs": e.get("needs"),
        "needs_display": e.get("needs_display"),
        "unit": e.get("unit"),
        "period": years[i],
        # ⭐ THE BASIS IS THE REGISTRY'S OWN FIELD, not a regex over the
        # formula. The frontend derived it by matching `avg(` and asking
        # whether a `bs.` token sat outside the wrapper — a third statement of
        # a fact the row already carries.
        #
        # ⛔⭐⭐ AND THERE IS NO `basis_note`. This module used to compose one
        # ("average total assets over period-end equity") and the registry row
        # for `financial_leverage` says in as many words why that was wrong:
        # *"The precision lives in `definition`, which a reader actually
        # sees."* The note was a SECOND STATEMENT of the definition, drifting
        # the moment ruling A2 was reworded. `basis: "mixed"` is the datum; the
        # definition is the prose; the operand texts show it structurally.
        "basis": e.get("basis"),
        "formula": e.get("formula_display") or e.get("formula"),
        "definition": e.get("definition_display") or e.get("definition"),
        # ⛔ NO OWNER EXISTS. See the module docstring.
        "implication": None,
        "children": kids,
    }


def _supplied(data):
    """WACC, because the registry delegates it to `ratios.wacc_at`."""
    try:
        return {"wacc_at": FE.wacc(dict(data.get("company") or {},
                                        _debt_book=None))["wacc"]}
    except Exception:                                        # noqa: BLE001
        return {}


def series_for(data, qid, supplied=None, *, historical_only=True):
    """One node's value across periods — A LOOP, NOT A FETCH.

    ⛔⭐⭐ EVERY POINT CARRIES ITS OWN STATE. Measured on the showcase:
    `asset_turnover` and `financial_leverage` are 4-of-5, both from the single
    missing 2021 opening balance. A surface that drew a 5-point line would be
    inventing the fifth value; a surface that drew a 4-point line silently
    would be hiding that a period exists and could not be computed. The
    absent point ships, with its reason, and `observed`/`n` ships beside it so
    the denominator is never inferred from the length of the array.
    """
    der = FE.derive_series(data)
    years, n = der["years"], der["n_historical"]
    supplied = _supplied(data) if supplied is None else supplied
    span = range(n) if historical_only else range(len(years))
    points = []
    for i in span:
        e = _explained(data, years, i, qid, supplied)
        points.append({
            "period": years[i],
            "value": e.get("value"),
            "status": ABSENT if e.get("value") is None else OBSERVED,
            "absence_reason": e.get("absent"),
            "projection": i >= n,
        })
    return {
        "id": qid,
        "points": points,
        "observed": sum(1 for p in points if p["status"] == OBSERVED),
        "n": len(points),
        "historical_only": historical_only,
    }


def build_tree(data, period_index=None, *, with_series=True):
    """The DuPont tree for one period, and each node's history beside it."""
    der = FE.derive_series(data)
    years, n = der["years"], der["n_historical"]
    i = n - 1 if period_index is None else period_index
    supplied = _supplied(data)

    facs = factors()
    factor_nodes = [_node(data, years, i, q, supplied) for q in facs]
    root = _node(data, years, i, ROOT, supplied, children=factor_nodes)

    # ⭐⭐ THE RECONCILIATION IS STRUCTURAL, NOT EMPIRICAL. Under ruling A2 the
    # assets cancel — (PAT/Rev)·(Rev/avgA)·(avgA/E) = PAT/E — so the product IS
    # ROE by algebra, and the residual is float noise rather than a variance to
    # watch. The payload says so, so the surface renders a reconciliation that
    # HOLDS instead of a difference to monitor.
    ident = _explained(data, years, i, IDENTITY, supplied)
    prod = ident.get("value")
    residual = None
    if prod is not None and root["value"] is not None:
        residual = prod - root["value"]

    out = {
        "period": years[i],
        "period_index": i,
        "periods": [{"period": y, "projection": k >= n}
                    for k, y in enumerate(years)],
        "n_historical": n,
        "root": root,
        "product": {"id": IDENTITY, "value": prod,
                    "status": ABSENT if prod is None else OBSERVED,
                    "absence_reason": ident.get("absent"),
                    "definition": (ident.get("definition_display")
                                   or ident.get("definition"))},
        "reconciliation": {
            "holds": residual is not None and abs(residual) < 1e-9,
            "residual": residual,
            "kind": "structural",
            "why": ("the average-assets terms cancel between turnover and "
                    "leverage, so the product equals ROE by algebra under "
                    "ruling A2 — any residual is floating-point noise, not a "
                    "variance"),
        },
        # ⛔ Stated on the payload so no surface has to discover it.
        "implications_available": False,
        "implications_note": ("no owner exists for per-quantity implications; "
                              "nothing in the product answers 'what this "
                              "means' for a ratio, and this lane did not "
                              "invent one"),
        "states": (OBSERVED, ABSENT, DERIVED),
    }
    if with_series:
        out["series"] = {q: series_for(data, q, supplied)
                         for q in (ROOT,) + facs}
    return out


# ═══════════════════════════════════════════════════════════════════════════
# PERIOD ATTRIBUTION — which factor moved ROE, and by how much
# ═══════════════════════════════════════════════════════════════════════════
# ⛔⭐⭐ THE METHOD IS LOGARITHMIC, AND THE ALTERNATIVES ARE REAL. A multiplicative
# decomposition has an INTERACTION TERM, and the standard treatments disagree:
#
#   · SEQUENTIAL substitution — change one factor at a time, holding the others
#     at their old (or new) values. ⛔ The answer DEPENDS ON THE ORDER, and there
#     are six orders for three factors. Presenting one as "the" attribution is
#     what §8a forbids.
#   · SHAPLEY — average over all orders. Order-free and defensible, but it costs
#     an explanation nobody asked for and returns the same answer as the log
#     method to within rounding for small moves.
#   · LOGARITHMIC (Törnqvist) — ⭐ CHOSEN. Because ROE = m x t x l EXACTLY,
#     log ROE = log m + log t + log l EXACTLY: the interaction term does not
#     exist in log space, so nothing is allocated and nothing is left over.
#
# ⭐ WHAT IT HOLDS CONSTANT: nothing. It is symmetric in the three factors — no
# factor is privileged by being "first", which is the whole defect of sequential
# substitution. Measured on the showcase 2024→2025: contributions sum to the
# observed −0.1970 with a residual of 4.3e-15.
#
# ⛔ AND IT REFUSES RATHER THAN ALLOCATING. The logarithm is undefined at or
# below zero, so a factor or an ROE that is non-positive, or an ROE that did not
# move, returns ABSENT with the reason. A residual is never silently spread.
ATTRIBUTION_METHOD = "logarithmic"


def attribute(data, i_from, i_to):
    """How much of the ROE change each factor explains, between two periods.

    ⛔ REAL PERIODS ONLY. An interpolated grain divides a flow evenly across
    sub-periods, so attributing a move computed from it measures the ESTIMATOR,
    not the business. The caller passes indices into the historical series.
    """
    derived = FE.derive_series(data)
    years, n = derived["years"], derived["n_historical"]
    if not (0 <= i_from < i_to < n):
        return {"available": False,
                "reason": (f"attribution needs two periods of real data inside "
                           f"the {n} historical periods; got {i_from}->{i_to}")}

    # ⭐ THE SAME OWNER THE TREE READS. `explain` and `evaluate_period` agree
    # today, but two readers is how they stop agreeing.
    supplied = _supplied(data)
    facs = factors()

    def val(i, q):
        return _explained(data, years, i, q, supplied).get("value")

    roe_a, roe_b = val(i_from, ROOT), val(i_to, ROOT)
    fa = [val(i_from, f) for f in facs]
    fb = [val(i_to, f) for f in facs]
    if roe_a is None or roe_b is None or any(x is None for x in fa + fb):
        # ⛔ NAME WHICH ONE. "a factor is absent" sends the reader hunting; the
        # 2021 refusal on this dataset is one missing opening balance and the
        # payload can say so.
        missing = [q for q, x, z in zip(facs, fa, fb) if x is None or z is None]
        return {"available": False,
                "reason": ("attribution needs every factor in both periods; "
                           + (", ".join(missing) or ROOT) + " is absent"),
                "absent_factors": missing}
    if roe_a <= 0 or roe_b <= 0 or any(x <= 0 for x in fa + fb):
        return {"available": False,
                "reason": ("the logarithmic method is undefined at or below "
                           "zero, and this lane refuses rather than switching "
                           "method silently")}
    change = roe_b - roe_a
    lr = math.log(roe_b / roe_a)
    if abs(lr) < 1e-15:
        return {"available": False, "reason": "ROE did not move; nothing to attribute"}

    parts = [math.log(z / x) for x, z in zip(fa, fb)]
    contrib = [(p / lr) * change for p in parts]
    resid = sum(contrib) - change
    return {
        "available": True,
        "method": ATTRIBUTION_METHOD,
        "holds_constant": "nothing — the method is symmetric in the three factors",
        "from_period": years[i_from], "to_period": years[i_to],
        "roe_from": roe_a, "roe_to": roe_b, "change": change,
        "factors": [
            {"id": f, "from": x, "to": z, "contribution": c,
             "share": (c / change) if change else None}
            for f, x, z, c in zip(facs, fa, fb, contrib)
        ],
        # ⛔ STATED, NOT ASSUMED. If this ever stops being ~0 the contributions
        # are not an attribution and the surface must not present them as one.
        "residual": resid,
        "sums_to_change": abs(resid) < 1e-9,
    }
