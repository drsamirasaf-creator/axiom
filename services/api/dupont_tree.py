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
from .modules.financials import engines as FE
from .modules.financials import ratio_registry as RR

# the three states a node's value can be in
OBSERVED = "observed"
ABSENT = "absent"
DERIVED = "derived"

ROOT = "axiom.roe"
FACTORS = ("axiom.net_margin", "axiom.asset_turnover",
           "axiom.financial_leverage")

# ⛔ THE OPERAND LABELS ARE THE FORMULA'S OWN TERMS, not new prose. Each entry
# names the two operands a factor divides, and how each is read — so a node can
# say "average total assets" rather than "total_assets" without a second
# vocabulary being invented for it.
_OPERANDS = {
    "axiom.net_margin": (("is.pat", "Profit after tax", "period"),
                         ("is.revenue", "Revenue", "period")),
    "axiom.asset_turnover": (("is.revenue", "Revenue", "period"),
                             ("bs.total_assets", "Total assets", "average")),
    "axiom.financial_leverage": (("bs.total_assets", "Total assets", "average"),
                                 ("bs.equity", "Equity", "period_end")),
}

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


def _operand(data, years, i, token, label, basis):
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
    ctx = RR._Ctx(data, years, i)
    if basis == "average" and i > 0:
        a, b = RR._resolve(ctx, token, -1), RR._resolve(ctx, token, 0)
        ok = not isinstance(a, RR.Absent) and not isinstance(b, RR.Absent)
        val = (a + b) / 2.0 if ok else None
        shown = f"avg({label.lower()})"
    else:
        raw = RR._resolve(ctx, token, 0)
        val = None if isinstance(raw, RR.Absent) else raw
        shown = label
    return {
        "id": token, "label": shown, "value": val,
        "status": OBSERVED if val is not None else ABSENT,
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
        kids = [_operand(data, years, i, t, lab, b) for t, lab, b in ops]
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
