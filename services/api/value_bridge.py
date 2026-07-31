"""§7s.5 — the Value Bridge. Equity value between two packs, decomposed.

⭐ NOT A NEW VALUATION. Equity value at each pack date comes from the frozen
inputs of that pack, through the production valuation engine. This lane
decomposes the MOVEMENT; it does not compute a new number.

⭐ THE RESIDUAL IS SHOWN, NEVER ABSORBED. A bridge that always reconciles exactly
has been fudged, and the product's credibility rests on not doing that. The
residual here is a SUBTRACTION, not a plug: it is whatever the named drivers did
not explain, and it is rendered whatever its size.

⭐ IT READS TWO FROZEN SNAPSHOTS, NEVER LIVE. A bridge that read live state would
restate the prior pack every month — the movement would change after the fact,
which is the one thing a bridge cannot do.
"""
from datetime import datetime

SCHEMA = "7s5.1"


def _driver(key, label, *, amount=None, absent=None, basis=None, detail=None,
            traceable=True):
    """One driver of the movement.

    ⭐ `amount` AND `absent` ARE MUTUALLY EXCLUSIVE, exactly one always set —
    the same contract the Decision Record uses. A driver carrying neither reads
    as "moved nothing", which is the claim a zero makes and an absence does not.
    """
    if amount is None and absent is None:
        absent = "not computable"
    return {"key": key, "label": label, "amount": amount,
            "absent": absent, "basis": basis, "detail": detail,
            "traceable": traceable}


# ═══════════════════════════════════════════════════════════════════════════
# EQUITY VALUE AT A PACK DATE — through the production path, sole-owned parts
# ═══════════════════════════════════════════════════════════════════════════

def equity_value(frozen):
    """(equity_value, enterprise_value, net_debt, absent_reason).

    ⭐ NET DEBT COMES FROM THE SOLE OWNER, `ratios.net_debt(debt, cash)`. A bridge
    that recomputed it inline would pin a second owner of the quantity the
    programme spent a lane making single-site.
    """
    ds = ((frozen or {}).get("classes") or {}).get("active_financial_dataset") or {}
    if not ds.get("present"):
        return None, None, None, (ds.get("reason")
                                  or "this pack froze no active dataset")
    payload = ds.get("payload")
    from .modules.financials import engines as fin
    from .modules.financials.ratios import net_debt
    from .modules.valuation import engines as val
    mode = "proforma" if (payload.get("periods") or {}).get("forecast") \
        else "auto_forecast"
    try:
        out = val.run(payload, mode)
    except Exception as exc:
        return None, None, None, f"valuation did not run: {type(exc).__name__}"
    ev = ((out or {}).get("deterministic") or {}).get("enterprise_value")
    if not isinstance(ev, (int, float)):
        return None, None, None, "the valuation returned no enterprise value"

    bs = payload.get("balance_sheet") or {}
    years = (payload.get("periods") or {}).get("historical") or []
    if not years:
        return None, float(ev), None, "no historical period, so net debt is absent"
    ys = str(max(years))
    debt = fin._n(lambda a, b: a + b,
                  (bs.get("short_term_debt") or {}).get(ys),
                  (bs.get("long_term_debt") or {}).get(ys))
    cash = (bs.get("cash") or {}).get(ys)
    nd = net_debt(debt, cash)
    if nd is None:
        # ⭐ ABSENCE PROPAGATES. `_n` returns None when an operand is missing, and
        # subtracting None would coerce an absence into a number.
        return None, float(ev), None, ("net debt is absent (a debt or cash "
                                       "operand is missing), so equity value "
                                       "cannot be derived from enterprise value")
    return float(ev) - float(nd), float(ev), float(nd), None


# ═══════════════════════════════════════════════════════════════════════════
# THE DRIVERS
# ═══════════════════════════════════════════════════════════════════════════

def _payload(frozen):
    ds = ((frozen or {}).get("classes") or {}).get("active_financial_dataset") or {}
    return ds.get("payload") if ds.get("present") else None


def _klass(frozen, name):
    return ((frozen or {}).get("classes") or {}).get(name) or {
        "present": False, "reason": f"'{name}' not in this frozen set"}


def d_net_debt(prior, current):
    """Net debt movement. ⭐ SOLE-OWNED, so this driver is exact rather than
    reconstructed: a fall in net debt raises equity value one-for-one."""
    _, _, nd0, r0 = equity_value(prior)
    _, _, nd1, r1 = equity_value(current)
    if nd0 is None or nd1 is None:
        return _driver("net_debt", "Net debt movement",
                       absent=(r0 or r1 or "net debt is absent in one pack"))
    return _driver("net_debt", "Net debt movement", amount=-(nd1 - nd0),
                   basis="ratios.net_debt(debt, cash) — sole owner",
                   detail={"from": nd0, "to": nd1})


def d_trading(prior, current):
    """Trading versus plan — line-level movement in the latest actual year."""
    p0, p1 = _payload(prior), _payload(current)
    if not p0 or not p1:
        return _driver("trading", "Trading versus plan",
                       absent="one pack froze no dataset")
    def _latest(p, line):
        is_ = (p.get("income_statement") or {}).get(line) or {}
        years = (p.get("periods") or {}).get("historical") or []
        return is_.get(str(max(years))) if years else None
    moved = {}
    for line in ("revenue", "ebitda", "operating_income", "net_income"):
        a, b = _latest(p0, line), _latest(p1, line)
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            moved[line] = b - a
    if not moved:
        return _driver("trading", "Trading versus plan",
                       absent="no comparable income-statement line in both packs")
    return _driver("trading", "Trading versus plan", amount=None,
                   absent=("line movement is measured but its equity-value "
                           "translation requires a re-valuation attributable to "
                           "the line alone, which is not separable from the "
                           "other drivers here"),
                   basis="income-statement lines, latest historical year",
                   detail=moved)


def d_forecast_revision(prior, current):
    """Forecast revision — the primary set changing between packs."""
    f0, f1 = _klass(prior, "forecast_sets"), _klass(current, "forecast_sets")
    if not f0.get("present") or not f1.get("present"):
        return _driver("forecast_revision", "Forecast revision",
                       absent=(f0.get("reason") or f1.get("reason")
                               or "no forecast sets in one pack"))
    def _primary(b):
        return next((s for s in (b.get("sets") or []) if s.get("is_primary")), None)
    a, b = _primary(f0), _primary(f1)
    if a is None or b is None:
        return _driver("forecast_revision", "Forecast revision",
                       absent="neither pack marks a primary forecast set")
    if a.get("id") == b.get("id"):
        return _driver("forecast_revision", "Forecast revision", amount=0.0,
                       basis="the primary forecast set is unchanged between packs",
                       detail={"set_id": a.get("id")})
    return _driver("forecast_revision", "Forecast revision",
                   absent=("the primary forecast set changed, and the equity "
                           "value of that revision alone is not separable from "
                           "the dataset movement it arrived with"),
                   basis="forecast_sets.is_primary",
                   detail={"from_set": a.get("id"), "to_set": b.get("id")})


def d_discount_rate(prior, current):
    """Discount-rate movement. ⭐ WACC IS SOLE-OWNED AS AN EXPRESSION; ITS `kd`
    INPUT IS NOT. See `OWNERSHIP_QUALIFICATIONS` — the amount is reported as a
    RATE movement rather than a value attribution for exactly that reason."""
    from .modules.financials.ratios import KD_FLAT, cost_of_equity_at, wacc_at
    p0, p1 = _payload(prior), _payload(current)
    if not p0 or not p1:
        return _driver("discount_rate", "Discount-rate movement",
                       absent="one pack froze no dataset")

    def _wacc(p):
        c = p.get("company") or {}
        need = ("risk_free_rate", "market_risk_premium", "tax_rate",
                "cost_of_debt", "target_debt_to_equity")
        if any(c.get(k) is None for k in need):
            return None
        beta = c.get("beta")
        bu = c.get("unlevered_industry_beta")
        lev = float(c["target_debt_to_equity"])
        try:
            if beta is not None:
                ke = cost_of_equity_at(ke_source="observed_beta",
                                       rf=float(c["risk_free_rate"]),
                                       mrp=float(c["market_risk_premium"]),
                                       beta=float(beta))
            elif bu is not None:
                ke = cost_of_equity_at(ke_source="relevered_beta_u",
                                       rf=float(c["risk_free_rate"]),
                                       mrp=float(c["market_risk_premium"]),
                                       leverage=lev,
                                       tax_rate=float(c["tax_rate"]),
                                       beta_unlevered=float(bu))
            else:
                return None
            return wacc_at(leverage=lev, ke=ke,
                           kd_base=float(c["cost_of_debt"]),
                           tax_rate=float(c["tax_rate"]),
                           kd_treatment=KD_FLAT)
        except Exception:
            return None

    w0, w1 = _wacc(p0), _wacc(p1)
    if w0 is None or w1 is None:
        # ⭐ AN ABSENT DRIVER STILL NAMES ITS SITE. A reader must be able to tell
        # WHICH kd treatment this driver would have consumed even when it could
        # not run — otherwise the qualification disappears exactly when the
        # driver is least informative.
        return _driver("discount_rate", "Discount-rate movement",
                       absent=("a WACC input is absent in one pack "
                               "(cost of debt, leverage, or a beta)"),
                       basis="ratios.wacc_at — sole-owned expression, KD_FLAT",
                       detail={"kd_counterfactual": _kd_counterfactual(p0, p1)})
    cf = _kd_counterfactual(p0, p1)
    return _driver("discount_rate", "Discount-rate movement", amount=None,
                   absent=("the rate movement is measured; its equity-value "
                           "translation is not attributed here because the WACC "
                           "expression is sole-owned while its kd input is not "
                           "(see ownership_qualifications)"),
                   basis="ratios.wacc_at — sole-owned expression, KD_FLAT",
                   detail={"from": w0, "to": w1, "delta": w1 - w0,
                           # ⭐ THE QUALIFICATION IS COMPUTED INTO THE ARTEFACT,
                           # not left in a report. A reader of the bridge can see
                           # what the other kd treatment would have produced.
                           "kd_site_used": "ratios.py:115 wacc_at, KD_FLAT",
                           "kd_counterfactual": cf},
                   traceable=True)


def _kd_counterfactual(p0, p1):
    """⭐ WHAT THE OTHER kd SITES WOULD HAVE PRODUCED.

    The rate driver consumes the SOLE-OWNED expression `ratios.wacc_at` with
    `KD_FLAT` — it takes the company's stated cost of debt and applies NEITHER
    kink. That is the only choice that does not silently pick a side of an
    unresolved duplication.

    The two kink treatments are reported here so the qualification is visible in
    the bridge itself:

      * `ratios.py:97`            kd + 0.01 * max(0, D/E - 1.0)**2
      * `intelligence:2343`       kd + 0.35 * max(0, debt/rev - 0.25)**2

    A 35x coefficient difference on a DIFFERENT DENOMINATOR. Reported, not
    resolved — the duplication is routed to sole ownership.
    """
    from .modules.financials import engines as fin
    from .modules.financials import ratios
    from .modules.intelligence.engines import LEV_KD_COEF, LEV_KD_KINK

    def _one(p):
        c = p.get("company") or {}
        kd = c.get("cost_of_debt")
        lev = c.get("target_debt_to_equity")
        if kd is None or lev is None:
            return None
        out = {"kd_flat": float(kd),
               "kd_ratios_kinked": float(kd) + 0.01 * max(0.0, float(lev) - 1.0) ** 2}
        # the intelligence site keys on debt/REVENUE, a different quantity
        bs = p.get("balance_sheet") or {}
        is_ = p.get("income_statement") or {}
        years = (p.get("periods") or {}).get("historical") or []
        if years:
            ys = str(max(years))
            debt = fin._n(lambda a, b: a + b,
                          (bs.get("short_term_debt") or {}).get(ys),
                          (bs.get("long_term_debt") or {}).get(ys))
            rev = (is_.get("revenue") or {}).get(ys)
            # ⭐ THROUGH THE OWNER. Computing `debt / rev` here failed
            # check-margin-boundary: value_bridge.py is not in the declared set,
            # and the set is downward-only. The ratio moved to ratios.py rather
            # than the boundary moving to accommodate this lane.
            d_ratio = ratios.debt_to_revenue(debt, rev)
            if d_ratio is not None:
                out["debt_to_revenue"] = d_ratio
                out["kd_intelligence_kinked"] = float(kd) + LEV_KD_COEF * max(
                    0.0, d_ratio - LEV_KD_KINK) ** 2
            else:
                out["kd_intelligence_kinked"] = None
                out["kd_intelligence_absent"] = ("debt or revenue is absent, so "
                                                 "the debt/revenue base is not "
                                                 "computable")
        return out

    a, b = _one(p0), _one(p1)
    if a is None or b is None:
        return {"absent": "a cost-of-debt or leverage input is missing"}
    return {
        "site_consumed": "ratios.py:115 wacc_at with KD_FLAT — neither kink",
        "why": ("KD_FLAT is the only treatment that does not silently pick a side "
                "of an unresolved duplication"),
        "from": a, "to": b,
        "duplication": {
            "ratios.py:97": "kd + 0.01 * max(0, D/E - 1.0)**2",
            "intelligence/engines.py:2343":
                f"kd + {LEV_KD_COEF} * max(0, debt/revenue - {LEV_KD_KINK})**2",
            "difference": "35x coefficient on a DIFFERENT denominator",
            "status": "routed to sole ownership; unresolved. Not resolved here.",
        },
    }


def d_multiples(prior, current):
    """Market-multiple movement."""
    p0, p1 = _payload(prior), _payload(current)
    if not p0 or not p1:
        return _driver("multiples", "Market-multiple movement",
                       absent="one pack froze no dataset")
    s0 = (p0.get("company") or {}).get("sector")
    s1 = (p1.get("company") or {}).get("sector")
    if not s0 or not s1:
        return _driver("multiples", "Market-multiple movement",
                       absent="the company declares no sector, so no peer "
                              "multiple set applies")
    from .modules.valuation import engines as val
    try:
        m0, m1 = val.multiples(p0, s0), val.multiples(p1, s1)
    except Exception as exc:
        return _driver("multiples", "Market-multiple movement",
                       absent=f"multiples did not compute: {type(exc).__name__}")
    return _driver("multiples", "Market-multiple movement", amount=None,
                   absent=("the peer set is static between these packs, so no "
                           "multiple movement is attributable"),
                   basis="valuation.multiples(sector)",
                   detail={"sector": s1})


def d_initiatives(prior, current):
    """⭐ THE DISTINCTIVE CLAIM. Now computable WHERE A LINK IS DECLARED — and
    still absent where it is not.

    Before B10 no link reached a statement line, so this driver was absent
    entirely. It now attributes a line's movement to the initiatives that
    DECLARED it, at the share they declared, and leaves everything else in the
    residual.

    ⭐⭐ EXCLUSIVITY OF LINKAGE IS NOT EXCLUSIVITY OF CAUSE. A sole link
    attributes its DECLARED WEIGHT and no more: a line with one linked initiative
    and three real drivers must not lose its whole movement to the one link,
    because the model cannot see the drivers nobody declared.
    """
    i0, i1 = _klass(prior, "initiatives"), _klass(current, "initiatives")
    l1 = _klass(current, "initiative_line_links")

    detail = None
    if i0.get("present") and i1.get("present"):
        def _by_id(b):
            return {r["id"]: r for r in (b.get("initiatives") or [])}
        a, b = _by_id(i0), _by_id(i1)
        changed = [{"initiative_id": k,
                    "status_from": a[k].get("status"),
                    "status_to": b[k].get("status"),
                    "actual_impact_from": a[k].get("actual_impact_amount"),
                    "actual_impact_to": b[k].get("actual_impact_amount")}
                   for k in set(a) & set(b)
                   if a[k].get("status") != b[k].get("status")
                   or a[k].get("actual_impact_amount")
                   != b[k].get("actual_impact_amount")]
        detail = {"changed": changed, "count": len(changed)}

    if not l1.get("present"):
        # ⭐ ABSENCE STAYS ABSENT. No declared link, no attribution — and the
        # movement is reported as evidence rather than priced.
        return _driver(
            "initiatives", "Initiative delivery versus slippage",
            absent=(l1.get("reason") or "no initiative declares a statement line"),
            basis="ax_initiative_line_links (declared, never inferred)",
            detail=detail, traceable=False)

    moves = _line_movements(prior, current)
    attribution = _attribute_frozen(l1, moves)
    total = sum(a["amount"] for a in attribution["attributed"]
                if a.get("amount") is not None)
    return _driver(
        "initiatives", "Initiative delivery versus slippage",
        amount=total,
        basis="declared initiative→line links, at the declared share",
        detail={**(detail or {}), "attribution": attribution,
                "line_movements": moves,
                "unlinked": l1.get("unlinked")},
        traceable=True)


def _line_movements(prior, current):
    """Movement per statement line, latest historical period, both packs."""
    p0, p1 = _payload(prior), _payload(current)
    if not p0 or not p1:
        return {}
    out = {}
    for stmt in ("income_statement", "balance_sheet", "cash_flow"):
        for line, series in (p1.get(stmt) or {}).items():
            if not isinstance(series, dict):
                continue
            years = (p1.get("periods") or {}).get("historical") or []
            if not years:
                continue
            ys = str(max(years))
            a = ((p0.get(stmt) or {}).get(line) or {}).get(ys)
            b = series.get(ys)
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                out[line] = b - a
    return out


def _attribute_frozen(link_block, line_movements):
    """The attribution rule, run over the FROZEN links.

    ⭐ IT DOES NOT TAKE A SESSION. A bridge that re-read the live links would
    retro-attribute a movement in a pack already issued.
    """
    links = [l for l in (link_block.get("links") or [])
             if not l.get("revoked_at")]
    by_line = {}
    for l in links:
        by_line.setdefault(l.get("statement_line"), []).append(l)

    attributed, residual = [], {}
    for line, delta in (line_movements or {}).items():
        declared = by_line.get(line) or []
        if not declared:
            continue                      # not this driver's residual to claim
        weighted = [l for l in declared if l.get("weight") is not None]
        unweighted = [l for l in declared if l.get("weight") is None]
        total_w = sum(l["weight"] for l in weighted)
        mode = "sole" if len(declared) == 1 else "proportional"
        if total_w > 1.0 + 1e-9:
            residual[line] = {"amount": delta,
                              "reason": f"declared weights sum to {total_w} (>1)"}
            continue
        for l in weighted:
            attributed.append({"initiative_id": l.get("initiative_id"),
                               "statement_line": line, "mode": mode,
                               "declared_weight": l["weight"],
                               "amount": delta * l["weight"],
                               "declared_by": l.get("declared_by_label")})
        for l in unweighted:
            attributed.append({"initiative_id": l.get("initiative_id"),
                               "statement_line": line, "mode": mode,
                               "declared_weight": None, "amount": None,
                               "absent": ("no share declared — an unstated share "
                                          "is unknown, not full ownership")})
        left = delta * (1.0 - total_w)
        if abs(left) > 1e-12 or not weighted:
            residual[line] = {
                "amount": left,
                "reason": (f"{round((1.0 - total_w) * 100, 2)}% of this line's "
                           f"movement is not covered by a declared share")}
    return {"attributed": attributed, "residual": residual}


DRIVERS = [d_trading, d_forecast_revision, d_discount_rate, d_multiples,
           d_net_debt, d_initiatives]


# ⭐ OWNERSHIP QUALIFICATIONS — which drivers rest on a quantity whose ownership
# is QUALIFIED rather than CLOSED. Reported, not resolved.
OWNERSHIP_QUALIFICATIONS = [
    {
        "driver": "discount_rate",
        "quantity": "WACC",
        "state": "qualified",
        "why": ("the sole-owner guard counts one owner of the WACC EXPRESSION "
                "(we*ke + wd*kd*(1-T) at ratios.py:121), not of the kd ASSUMPTION "
                "inside it"),
        "evidence": ("the kd kink exists twice with different constants AND "
                     "different bases: ratios.py:97 applies 0.01 * max(0, "
                     "leverage - 1.0)**2 on D/E, while intelligence/engines.py:2343 "
                     "applies LEV_KD_COEF 0.35 * max(0, d_ratio - LEV_KD_KINK "
                     "0.25)**2 on debt/REVENUE — a 35x coefficient difference on a "
                     "different denominator"),
        "consequence": ("a WACC delta could reflect WHICH kd path ran rather than "
                        "a real change in the cost of debt, so this bridge reports "
                        "the RATE movement and does not attribute an equity-value "
                        "amount to it"),
        "routed": "sole ownership; unresolved. Not resolved in this lane.",
    },
    {
        "driver": "net_debt",
        "quantity": "net debt",
        "state": "closed",
        "why": "ratios.net_debt(debt, cash) is single-site and guard-enforced",
        "consequence": "this driver is exact",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# THE BRIDGE
# ═══════════════════════════════════════════════════════════════════════════

def build(prior_frozen, current_frozen, *, from_pack=None, to_pack=None):
    """The bridge between two frozen packs.

    ⭐ THE RESIDUAL IS A SUBTRACTION, NOT A PLUG. It is total movement minus the
    sum of what the named drivers explained. No driver is adjusted to make it
    close, and it is rendered whatever its size.
    """
    ev0, entv0, nd0, r0 = equity_value(prior_frozen)
    ev1, entv1, nd1, r1 = equity_value(current_frozen)

    drivers = [fn(prior_frozen, current_frozen) for fn in DRIVERS]
    explained = sum(d["amount"] for d in drivers if d["amount"] is not None)
    computable = [d for d in drivers if d["amount"] is not None]
    absent = [d for d in drivers if d["amount"] is None]

    if ev0 is None or ev1 is None:
        total = None
        residual = None
        residual_absent = (r0 or r1
                           or "equity value is absent in one of the two packs")
    else:
        total = ev1 - ev0
        residual = total - explained
        residual_absent = None

    return {
        "schema": SCHEMA,
        "from": _endpoint(from_pack, ev0, entv0, nd0, r0),
        "to": _endpoint(to_pack, ev1, entv1, nd1, r1),
        "total_movement": total,
        "explained": explained if total is not None else None,
        "residual": residual,
        "residual_absent": residual_absent,
        # ⭐ THE RESIDUAL IS NAMED IN THE PAYLOAD, not left for a renderer to
        # notice. A bridge whose residual can be dropped by a rendering choice is
        # a bridge that reconciles exactly on the page.
        "residual_label": "Unexplained residual",
        "drivers": drivers,
        "computable_drivers": [d["key"] for d in computable],
        "absent_drivers": [d["key"] for d in absent],
        "ownership_qualifications": OWNERSHIP_QUALIFICATIONS,
    }


def _endpoint(pack, ev, entv, nd, reason):
    out = {"pack_id": getattr(pack, "id", None),
           "period_end": getattr(pack, "period_end", None),
           "version": getattr(pack, "version", None),
           "equity_value": ev, "enterprise_value": entv, "net_debt": nd}
    if ev is None:
        out["absent"] = reason
    return out


# ═══════════════════════════════════════════════════════════════════════════
# 5 · THE ANCHOR — PE framing, an override rather than a second mechanism
# ═══════════════════════════════════════════════════════════════════════════

def anchor_pack(db, pack):
    """The pack this one bridges FROM.

    ⭐ THE DEFAULT IS THE PRIOR PACK, AND THE ANCHOR IS AN OVERRIDE ON THE
    EXISTING SCHEDULE ROW — not a second mechanism. "Value bridge since entry" is
    a PE framing of the same bridge, so it sets where the bridge starts and
    changes nothing else.
    """
    from .pack import Pack, PackSchedule, PUBLISHED
    sch = db.query(PackSchedule).filter_by(cid=pack.cid).first()
    anchor_end = getattr(sch, "bridge_anchor_period_end", None) if sch else None
    q = (db.query(Pack)
           .filter(Pack.cid == pack.cid, Pack.status == PUBLISHED,
                   Pack.id != pack.id))
    if anchor_end:
        row = (q.filter(Pack.period_end == anchor_end)
                .order_by(Pack.version.desc()).first())
        if row is not None:
            return row, "anchor override (value bridge since entry)"
        # ⭐ A CONFIGURED ANCHOR THAT RESOLVES TO NOTHING IS NAMED, not silently
        # replaced by the default — the reader would otherwise see a bridge from
        # the wrong date and no indication of it.
        return None, (f"the configured anchor {anchor_end} has no published pack")
    row = (q.filter(Pack.period_end < pack.period_end)
            .order_by(Pack.period_end.desc(), Pack.version.desc()).first())
    return row, ("prior published pack" if row is not None else
                 "this is the first published pack for this company")


def for_pack(db, pack):
    """The bridge for a published pack, or a stated absence.

    ⭐ THE FIRST PACK HAS NO BRIDGE AND SAYS SO. Rendering an empty bridge would
    show a movement of nothing against nothing, which reads as "value did not
    move" — a claim about the business rather than about the record.
    """
    from .pack import frozen_inputs
    prior, basis = anchor_pack(db, pack)
    if prior is None:
        return {"schema": SCHEMA, "present": False, "reason": basis,
                "to": {"pack_id": pack.id, "period_end": pack.period_end}}
    out = build(frozen_inputs(db, prior), frozen_inputs(db, pack),
                from_pack=prior, to_pack=pack)
    out["present"] = True
    out["anchor_basis"] = basis
    return out
