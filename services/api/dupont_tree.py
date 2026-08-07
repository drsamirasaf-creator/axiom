"""DuPont as a NODE TREE. Pure shaping — it computes nothing.

⭐⭐ IT COMPUTES NOTHING, AND THAT IS THE POINT (§7r-O). Every value comes from
`ratio_registry.evaluate_period` — the production path — or is read straight off
the stored statements. A lane wrote `tiers.py` last turn and deleted it for
exactly this reason: a second owner of a quantity is worse than an absent
surface, because the two drift and nobody is told.

⛔ DEFINITIONS ARE NOT AUTHORED HERE. Each node's `definition` is the registry
row's own `definition:` field. **No new definition text is written in this
module**, and if a row has none the node reports absence rather than inventing a
sentence.

⛔ IMPLICATIONS ARE ABSENT, DELIBERATELY. Measured 7 Aug: **nothing in the
codebase owns "what this means"** for a ratio — the only `interpretation` hits
are period-format notes in `ingest.py`. Writing per-node prose here would create
an owner nobody ruled on, so every node carries `implication: None` and the
payload says why. **The surface must render that as absent, not as blank.**

## ⭐ THE SHAPE

    ROE
     ├─ net_margin          → pat / revenue
     │    ├─ pat
     │    └─ revenue
     ├─ asset_turnover      → revenue / avg(total assets)
     │    ├─ revenue
     │    └─ avg(total assets)
     └─ financial_leverage  → avg(total assets) / period-end equity
          ├─ avg(total assets)
          └─ equity

⛔ ABSENCE PROPAGATES PER NODE. A node whose input is missing renders **absent**,
never zero — and a parent whose child is absent is absent too, because the
product of an absent factor is not a number.
"""
import math

from .modules.financials import engines as FE
from .modules.financials import ratio_registry as RR

# the three states a node's value can be in
OBSERVED = "observed"
ABSENT = "absent"
DERIVED = "derived"

ROOT = "axiom.roe"
FACTORS = ("axiom.net_margin", "axiom.asset_turnover",
           "axiom.financial_leverage")

# ⛔⭐⭐ THE OPERAND TOKENS ONLY. NO LABELS HERE — I AUTHORED A LABEL MAP IN THIS
# TUPLE LAST LANE AND IT WAS A SECOND OWNER OF DISPLAY TEXT, which is exactly
# what the label ruling forbids: the payload carries the display string and the
# KEY stays the identifier, from the owner that already holds it.
#
# ⭐ THE RESOLUTION IS TWO HOPS, and neither is invented here: the vocabulary
# maps a token to its stored `field:`, and `templates.LABELS` maps that field to
# a caption in the dataset's own framework. `bs.equity` -> field `total_equity`
# -> "Total Stockholders' Equity". Looking the token's own suffix up in LABELS —
# what a first version did — finds nothing, because `equity` is not the stored
# name.
_OPERANDS = {
    "axiom.net_margin": (("is.pat", "period"),
                         ("is.revenue", "period")),
    "axiom.asset_turnover": (("is.revenue", "period"),
                             ("bs.total_assets", "average")),
    "axiom.financial_leverage": (("bs.total_assets", "average"),
                                 ("bs.equity", "period_end")),
}


def _framework(data):
    fw = ((data or {}).get("company") or {}).get("framework") \
        or (data or {}).get("standard") or "us_gaap"
    return fw if fw in ("us_gaap", "ifrs") else "us_gaap"


def operand_label(data, token):
    """The caption for an operand token, from the OWNERS. `None` is a GAP.

    ⛔ Returns None rather than the token or a guess. Measured 7 Aug: of the
    four operand tokens, `is.revenue` and `bs.equity` resolve to a caption and
    **`is.pat` and `bs.total_assets` have none anywhere** — both are
    `source: derived` with an `expr:` and no `field:`, so there is no stored
    line for `templates.LABELS` to caption. That is a gap to report, not a
    place to invent text.
    """
    from .modules.financials import templates as T
    vocab, _g, _r = RR._index()
    field = (vocab.get(token) or {}).get("field")
    if not field:
        return None
    lines = (T.LABELS.get(_framework(data)) or {}).get("lines") or {}
    return lines.get(field)


_BLOCK = {"is": "income_statement", "bs": "balance_sheet", "cf": "cash_flow"}


def _row(qid):
    for r in RR.load()["ratios"]:
        if r["id"] == qid:
            return r
    return {}


def _value(data, years, i, qid):
    """(value, status) from the PRODUCTION path. Absence is a state, not a zero."""
    try:
        v = RR.evaluate_period(data, years, i, qid)
    except Exception:                                        # noqa: BLE001
        return None, ABSENT
    if isinstance(v, RR.Absent):
        return None, ABSENT
    return v, OBSERVED


def _operand(data, years, i, token, basis):
    """A leaf node, resolved by THE REGISTRY'S OWN RESOLVER.

    ⛔⭐⭐ A FIRST VERSION READ THE STORED BLOCKS DIRECTLY AND EVERY LEAF CAME BACK
    ABSENT — because the registry's tokens are not the stored field names:
    `is.pat` is derived as `net_income`, `bs.equity` is stored as `total_equity`,
    and `bs.total_assets` **is not stored at all**. The ratios computed fine
    while their own operands showed as missing.

    ⭐ The mapping has an owner — `ratio_registry._resolve` takes a token OR a
    ratio id and returns a number or an `Absent` with its reason. Re-deriving it
    here would have been a second resolver in the very lane that opened by
    warning against a second owner. Same shape as the completeness lane's
    `is.ebit`: the question is "can it be OBTAINED", never "was it typed".
    """
    label = operand_label(data, token)
    ctx = RR._Ctx(data, years, i)
    reason = None
    if basis == "average":
        # ⛔⭐⭐ THE FIRST PERIOD HAS NO AVERAGE, AND IT MUST SAY SO. An earlier
        # version wrote `if basis == "average" and i > 0`, so at i=0 it FELL
        # THROUGH to the point-value branch and returned a period-end number
        # still labelled `basis: "average"` — OBSERVED, while its own parent
        # ratio was ABSENT for exactly the missing opening balance. Measured on
        # the showcase: 2021 asset_turnover=absent, leaf=observed. A leaf that
        # disagrees with its parent about whether a period exists is the §III.15
        # shape — the label is a PROXY for the basis, and it failed silently.
        if i <= 0:
            return {"id": token, "label": f"avg({label.lower()})" if label else None,
                    "value": None, "status": ABSENT, "basis": basis,
                    "absence_reason": ("an average basis needs an opening "
                                       "balance, and this is the first period"),
                    "period": years[i], "formula": None, "definition": None,
                    "implication": None, "children": []}
        a, b = RR._resolve(ctx, token, -1), RR._resolve(ctx, token, 0)
        ok = not isinstance(a, RR.Absent) and not isinstance(b, RR.Absent)
        val = (a + b) / 2.0 if ok else None
        if not ok:
            reason = getattr(a if isinstance(a, RR.Absent) else b, "reason", None)
        shown = f"avg({label.lower()})" if label else None
    else:
        raw = RR._resolve(ctx, token, 0)
        val = None if isinstance(raw, RR.Absent) else raw
        reason = getattr(raw, "reason", None) if val is None else None
        shown = label
    return {
        "id": token, "label": shown, "value": val,
        "status": OBSERVED if val is not None else ABSENT,
        "absence_reason": reason,
        "basis": basis, "period": years[i],
        "formula": None,            # a stored line has no formula
        "definition": None,         # ⛔ no owner; see the module docstring
        "implication": None,
        "children": [],
    }


def _node(data, years, i, qid, *, children=()):
    row = _row(qid)
    val, status = _value(data, years, i, qid)
    kids = list(children)
    # ⛔ ABSENCE PROPAGATES UPWARD. A parent whose child is absent cannot be
    # observed, whatever the evaluator returned — the product of an absent
    # factor is not a number.
    if any(k["status"] == ABSENT for k in kids):
        val, status = (val, status) if status == ABSENT else (None, ABSENT)
    return {
        "id": qid,
        "label": row.get("name") or qid,
        "value": val,
        "status": status,
        "unit": row.get("unit"),
        "period": years[i],
        "basis": row.get("basis"),
        # ⭐ MIXED BASIS TRAVELS AS DATA, NOT AS COPY. `financial_leverage` is
        # average assets over PERIOD-END equity — the only mixed-basis figure
        # among the average-basis ratios — and a surface must not have to infer
        # that from a sentence.
        "basis_note": ("average total assets over period-end equity"
                       if row.get("basis") == "mixed" else None),
        "formula": row.get("formula"),
        "definition": row.get("definition"),
        # ⛔ NO OWNER EXISTS. See the module docstring.
        "implication": None,
        "children": kids,
    }


def build_tree(data, period_index=None):
    """The DuPont tree for one period. Shapes; never computes."""
    derived = FE.derive_series(data)
    years = derived["years"]
    i = derived["n_historical"] - 1 if period_index is None else period_index

    factors = []
    for qid in FACTORS:
        ops = _OPERANDS.get(qid, ())
        kids = [_operand(data, years, i, t, b) for t, b in ops]
        factors.append(_node(data, years, i, qid, children=kids))

    root = _node(data, years, i, ROOT, children=factors)

    # ⭐⭐ THE RECONCILIATION IS STRUCTURAL, NOT EMPIRICAL. Under ruling A2 the
    # assets cancel — (PAT/Rev)·(Rev/avgA)·(avgA/E) = PAT/E — so the product IS
    # ROE by algebra, and the residual is float noise rather than a variance to
    # watch. The payload says so, so the surface renders a reconciliation that
    # HOLDS instead of a difference to monitor.
    prod, prod_status = _value(data, years, i, "axiom.dupont_three_step")
    residual = None
    if prod is not None and root["value"] is not None:
        residual = prod - root["value"]

    return {
        "period": years[i],
        "root": root,
        "product": {"id": "axiom.dupont_three_step", "value": prod,
                    "status": prod_status,
                    "definition": _row("axiom.dupont_three_step").get("definition")},
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

    def val(i, q):
        v = RR.evaluate_period(data, years, i, q)
        return None if isinstance(v, RR.Absent) else v

    roe_a, roe_b = val(i_from, ROOT), val(i_to, ROOT)
    fa = [val(i_from, f) for f in FACTORS]
    fb = [val(i_to, f) for f in FACTORS]
    if roe_a is None or roe_b is None or any(x is None for x in fa + fb):
        return {"available": False, "reason": "a factor is absent in one period"}
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
            for f, x, z, c in zip(FACTORS, fa, fb, contrib)
        ],
        # ⛔ STATED, NOT ASSUMED. If this ever stops being ~0 the contributions
        # are not an attribution and the surface must not present them as one.
        "residual": resid,
        "sums_to_change": abs(resid) < 1e-9,
    }
