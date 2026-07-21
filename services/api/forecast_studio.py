"""AXIOM FORECAST STUDIO (Phase 7L).

Five forecasting methods, each producing a FULL kernel-consumable statement set
(the projection roll-forward is shared; methods differ only in how they project
the revenue top line, then operating drivers fitted from history build the rest,
with equity as the balancing plug — identical mechanics to fin.auto_forecast):

  1. trend        — historical revenue CAGR extrapolation
  2. driver       — fin.auto_forecast (fitted mean driver ratios, capped CAGR)
  3. smoothing    — damped-trend exponential smoothing (NOT Holt-Winters; no
                    seasonality is claimed — fixed smoothing params, honest about
                    short annual history; fitted_history_len carried in payload)
  4. montecarlo   — seeded MC revenue simulation surfaced as P10/P50/P90 bands
                    (the P50 path drives the stored statements)
  5. ensemble     — inverse-MAE weighted blend of 1-4 when >=6 history points,
                    else equal weights; weights persisted; divergence flagged

Each generated forecast is stored immutably as an ax_forecast_sets row. Exactly
one set per company is PRIMARY; the kernel (valuation/viability/frontier) consumes
ONLY the primary — set-primary writes it into the active dataset's forecast
columns and eagerly triggers the bounded frontier+viability recompute.
"""
import math
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON

from . import accounts as A
from .accounts import (Base, get_db, require_company_member, require_company_admin,
                       get_current_user, audit, _active_company_dataset)
from .modules.financials import engines as fin

_log = logging.getLogger("axiom.forecast_studio")

METHODS = ("trend", "driver", "smoothing", "montecarlo", "ensemble")
HORIZON_MIN, HORIZON_MAX = 3, 15
MC_PATHS = 2000
MC_SEED = 26202
DAMP_PHI, DAMP_ALPHA, DAMP_BETA = 0.85, 0.6, 0.2
DIVERGENCE_CV = 0.15                      # terminal-revenue CV above which we flag


# ======================================================================
# model
# ======================================================================
class ForecastSet(Base):
    __tablename__ = "ax_forecast_sets"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    dataset_version = Column(Integer, nullable=False)      # the historicals this was fit on
    method = Column(String(24), nullable=False)            # trend|driver|smoothing|montecarlo|ensemble|client
    label = Column(String(120), nullable=False)
    source = Column(String(16), nullable=False)            # generated | client
    horizon = Column(Integer, nullable=False)
    fitted_history_len = Column(Integer, nullable=False)
    drivers = Column(JSON, nullable=True)
    statements = Column(JSON, nullable=False)              # {periods, income_statement, balance_sheet, cash_flow} forecast-only
    bands = Column(JSON, nullable=True)                    # montecarlo: {p10,p50,p90} revenue paths
    weights = Column(JSON, nullable=True)                  # ensemble
    divergence = Column(JSON, nullable=True)               # ensemble: {cv, flag, terminal_by_method}
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ======================================================================
# shared projection engine (revenue path -> full statements)
# ======================================================================
def _avg(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else 0.0


def _fit_drivers(data):
    """Operating drivers fitted from history — same definitions as auto_forecast."""
    hist = list(data["periods"]["historical"])
    IS, BS, CF = data["income_statement"], data["balance_sheet"], data["cash_flow"]
    rev_h = [IS["revenue"][str(y)] for y in hist]
    def per(fn):
        return _avg([fn(str(y)) for y in hist if IS["revenue"][str(y)]])
    m_ebit = per(lambda ys: (IS["revenue"][ys] - IS["cogs"][ys] - IS["opex"][ys]
                             - IS["depreciation_amortization"][ys]) / IS["revenue"][ys])
    p_da = per(lambda ys: IS["depreciation_amortization"][ys] / IS["revenue"][ys])
    p_capex = per(lambda ys: CF["capex"][ys] / IS["revenue"][ys])
    p_nwc = per(lambda ys: (BS["other_current_assets"][ys]
                            - BS["current_liabilities_ex_debt"][ys]) / IS["revenue"][ys])
    p_cl = per(lambda ys: BS["current_liabilities_ex_debt"][ys] / IS["revenue"][ys])
    cogs_share = _avg([IS["cogs"][str(y)] / (IS["cogs"][str(y)] + IS["opex"][str(y)])
                       for y in hist if (IS["cogs"][str(y)] + IS["opex"][str(y)])])
    cagr = fin._cagr(rev_h[0], rev_h[-1], len(hist) - 1) if len(hist) > 1 else 0.03
    return {"rev_hist": rev_h, "hist": hist, "cagr": cagr, "m_ebit": m_ebit,
            "p_da": p_da, "p_capex": p_capex, "p_nwc": p_nwc, "p_cl": p_cl,
            "cogs_share": cogs_share,
            "interest": IS["interest_expense"][str(hist[-1])]}


def _project(data, rev_path, drivers):
    """Roll a full forecast statement set from an explicit revenue path, mirroring
    fin.auto_forecast exactly (equity as the balancing plug). rev_path has len == horizon."""
    d = drivers
    hist = d["hist"]
    horizon = len(rev_path)
    T = float(data["company"]["tax_rate"])
    IS, BS, CF = data["income_statement"], data["balance_sheet"], data["cash_flow"]
    fcst_years = [hist[-1] + k for k in range(1, horizon + 1)]
    out = {"periods": {"forecast": fcst_years},
           "income_statement": {k: {} for k in fin.IS_KEYS},
           "balance_sheet": {k: {} for k in fin.BS_KEYS},
           "cash_flow": {k: {} for k in fin.CF_KEYS}}
    y_prev = str(hist[-1])
    prev_oca = BS["other_current_assets"][y_prev]
    prev_cl = BS["current_liabilities_ex_debt"][y_prev]
    prev_nca = BS["noncurrent_assets"][y_prev]
    prev_cash = BS["cash"][y_prev]
    carry = {k: BS[k][y_prev] for k in ("short_term_debt", "long_term_debt",
                                        "preferred_equity", "minority_interest")}
    r = fin._r
    for i, y in enumerate(fcst_years):
        ys = str(y)
        rev = rev_path[i]
        ebit = d["m_ebit"] * rev
        da = d["p_da"] * rev
        nonebit = rev - ebit - da
        cogs = d["cogs_share"] * nonebit
        opex = nonebit - cogs
        capex = d["p_capex"] * rev
        oca = (d["p_nwc"] + d["p_cl"]) * rev
        cl = d["p_cl"] * rev
        ni = (ebit - d["interest"]) * (1 - T) if ebit >= d["interest"] else (ebit - d["interest"])
        out["income_statement"]["revenue"][ys] = r(rev)
        out["income_statement"]["cogs"][ys] = r(cogs)
        out["income_statement"]["opex"][ys] = r(opex)
        out["income_statement"]["depreciation_amortization"][ys] = r(da)
        out["income_statement"]["interest_expense"][ys] = r(d["interest"])
        nca = prev_nca + capex - da
        out["balance_sheet"]["other_current_assets"][ys] = r(oca)
        out["balance_sheet"]["current_liabilities_ex_debt"][ys] = r(cl)
        out["balance_sheet"]["noncurrent_assets"][ys] = r(nca)
        for k, v in carry.items():
            out["balance_sheet"][k][ys] = v
        out["cash_flow"]["capex"][ys] = r(capex)
        out["cash_flow"]["net_borrowing"][ys] = 0.0
        out["cash_flow"]["dividends"][ys] = 0.0
        d_nwc = (oca - cl) - (prev_oca - prev_cl)
        fcfe = ni + da - capex - d_nwc
        cash = prev_cash + fcfe
        out["balance_sheet"]["cash"][ys] = r(cash)
        assets = cash + oca + nca
        out["balance_sheet"]["total_equity"][ys] = r(
            assets - cl - carry["short_term_debt"] - carry["long_term_debt"]
            - carry["preferred_equity"] - carry["minority_interest"])
        prev_oca, prev_cl, prev_nca, prev_cash = oca, cl, nca, cash
    return out


# ======================================================================
# the five revenue projections
# ======================================================================
def _rev_trend(d, horizon):
    last = d["rev_hist"][-1]
    return [last * (1 + d["cagr"]) ** k for k in range(1, horizon + 1)]


def _rev_driver(d, horizon):
    g = min(d["cagr"], 0.25)                # auto_forecast's capped growth
    last = d["rev_hist"][-1]
    return [last * (1 + g) ** k for k in range(1, horizon + 1)]


def _rev_smoothing(rev_hist, horizon):
    """Damped-trend exponential smoothing (Gardner). Level + damped trend, fixed
    smoothing params. NO seasonality — not Holt-Winters."""
    if len(rev_hist) < 2:
        return [rev_hist[-1]] * horizon
    level = rev_hist[0]
    trend = rev_hist[1] - rev_hist[0]
    for y in rev_hist[1:]:
        prev_level = level
        level = DAMP_ALPHA * y + (1 - DAMP_ALPHA) * (level + DAMP_PHI * trend)
        trend = DAMP_BETA * (level - prev_level) + (1 - DAMP_BETA) * DAMP_PHI * trend
    out, damp_sum = [], 0.0
    for h in range(1, horizon + 1):
        damp_sum += DAMP_PHI ** h
        out.append(level + damp_sum * trend)
    return out


def _rev_montecarlo(d, horizon):
    """Seeded MC around the fitted growth with historical growth volatility.
    Returns (p50_path, {p10,p50,p90})."""
    import random as _random
    rev_h = d["rev_hist"]
    growths = [rev_h[i] / rev_h[i - 1] - 1 for i in range(1, len(rev_h)) if rev_h[i - 1]]
    mu = _avg(growths) if growths else d["cagr"]
    sigma = (math.sqrt(_avg([(g - mu) ** 2 for g in growths])) if len(growths) > 1 else 0.05) or 0.05
    rng = _random.Random(MC_SEED)
    paths = []
    for _ in range(MC_PATHS):
        rev, row = rev_h[-1], []
        for _h in range(horizon):
            rev *= (1 + rng.gauss(mu, sigma))
            row.append(rev)
        paths.append(row)
    def pct(col, q):
        s = sorted(p[col] for p in paths)
        return s[min(len(s) - 1, int(q * len(s)))]
    p10 = [pct(h, 0.10) for h in range(horizon)]
    p50 = [pct(h, 0.50) for h in range(horizon)]
    p90 = [pct(h, 0.90) for h in range(horizon)]
    return p50, {"p10": [fin._r(x) for x in p10], "p50": [fin._r(x) for x in p50],
                 "p90": [fin._r(x) for x in p90]}


def _backtest_mae(data, drivers, method_fn):
    """Hold out the last min(2, ...) historical years, fit on the rest, MAE of the
    method's revenue prediction vs actual. Only meaningful with >=6 points."""
    hist = drivers["hist"]
    if len(hist) < 6:
        return None
    holdout = 2
    train = {**data, "periods": {"historical": hist[:-holdout], "forecast": []}}
    dtr = _fit_drivers(train)
    pred = method_fn(dtr, holdout)
    actual = [data["income_statement"]["revenue"][str(y)] for y in hist[-holdout:]]
    return _avg([abs(pred[i] - actual[i]) for i in range(holdout)])


# ======================================================================
# generation
# ======================================================================
def _summary(rev_path, drivers, horizon):
    last_hist = drivers["rev_hist"][-1]
    term = rev_path[-1]
    implied = (term / last_hist) ** (1.0 / horizon) - 1 if last_hist > 0 else None
    return {"terminal_revenue": fin._r(term),
            "implied_revenue_cagr": fin._r(implied) if implied is not None else None}


def compute_method(data, method, horizon):
    """Compute a single method -> (statements, extra) where extra carries method
    payload (drivers/bands/weights/divergence, fitted_history_len)."""
    d = _fit_drivers(data)
    hist_len = len(d["hist"])
    bands = weights = divergence = None
    if method == "trend":
        rev = _rev_trend(d, horizon)
    elif method == "driver":
        rev = _rev_driver(d, horizon)
    elif method == "smoothing":
        rev = _rev_smoothing(d["rev_hist"], horizon)
    elif method == "montecarlo":
        rev, bands = _rev_montecarlo(d, horizon)
    elif method == "ensemble":
        members = {"trend": _rev_trend(d, horizon), "driver": _rev_driver(d, horizon),
                   "smoothing": _rev_smoothing(d["rev_hist"], horizon),
                   "montecarlo": _rev_montecarlo(d, horizon)[0]}
        fns = {"trend": _rev_trend, "driver": _rev_driver,
               "smoothing": lambda dd, h: _rev_smoothing(dd["rev_hist"], h),
               "montecarlo": lambda dd, h: _rev_montecarlo(dd, h)[0]}
        maes = {k: _backtest_mae(data, d, fns[k]) for k in members}
        if hist_len >= 6 and all(m is not None and m > 0 for m in maes.values()):
            inv = {k: 1.0 / maes[k] for k in members}
            tot = sum(inv.values())
            weights = {k: fin._r(inv[k] / tot, 4) for k in members}
        else:
            weights = {k: fin._r(1.0 / len(members), 4) for k in members}
        rev = [sum(weights[k] * members[k][i] for k in members) for i in range(horizon)]
        terminals = {k: fin._r(members[k][-1]) for k in members}
        vals = list(terminals.values())
        mean = _avg(vals)
        cv = (math.sqrt(_avg([(v - mean) ** 2 for v in vals])) / mean) if mean else 0.0
        divergence = {"cv": fin._r(cv, 4), "flag": cv > DIVERGENCE_CV,
                      "terminal_by_method": terminals}
    else:
        raise HTTPException(422, f"unknown method '{method}'")
    stmts = _project(data, rev, d)
    drivers_out = {"revenue_cagr": fin._r(d["cagr"]), "ebit_margin": fin._r(d["m_ebit"]),
                   "da_pct_revenue": fin._r(d["p_da"]), "capex_pct_revenue": fin._r(d["p_capex"]),
                   "nwc_pct_revenue": fin._r(d["p_nwc"]), "interest_expense": fin._r(d["interest"]),
                   **_summary(rev, d, horizon)}
    return stmts, {"drivers": drivers_out, "bands": bands, "weights": weights,
                   "divergence": divergence, "fitted_history_len": hist_len}


_LABELS = {"trend": "Trend (CAGR extrapolation)", "driver": "Driver-based",
           "smoothing": "Damped-trend smoothing", "montecarlo": "Monte Carlo (P10/P50/P90)",
           "ensemble": "AXIOM Ensemble", "client": "Client's own forecast"}


def _historicals_only(data):
    hist = list(data["periods"]["historical"])
    keep = set(str(y) for y in hist)
    def trim(block):
        return {k: {y: v for y, v in series.items() if y in keep} for k, series in block.items()}
    return {"company": dict(data["company"]),
            "periods": {"historical": hist, "forecast": []},
            "income_statement": trim(data["income_statement"]),
            "balance_sheet": trim(data["balance_sheet"]),
            "cash_flow": trim(data["cash_flow"])}


def generate(db, company_id, methods, horizon):
    ds = _active_company_dataset(db, company_id)
    if not ds or not isinstance(ds.data, dict):
        raise HTTPException(409, "No active dataset for this company — upload data first.")
    if not (HORIZON_MIN <= horizon <= HORIZON_MAX):
        raise HTTPException(422, f"horizon must be between {HORIZON_MIN} and {HORIZON_MAX} years")
    base = _historicals_only(ds.data)
    if len(base["periods"]["historical"]) < 2:
        raise HTTPException(422, "at least 2 historical years are required to forecast")
    _capture_client_set(db, company_id, ds)          # register client forecast as a set (once)
    out = []
    for method in methods:
        if method not in METHODS:
            raise HTTPException(422, f"unknown method '{method}'")
        stmts, extra = compute_method(base, method, horizon)
        row = _upsert_set(db, company_id, ds.version, method, "generated", horizon, stmts, extra)
        out.append(_set_out(row))
    db.commit()
    return out


def _capture_client_set(db, company_id, ds):
    """If the active dataset carries a client pro-forma, register it as a set once."""
    fc = (ds.data.get("periods") or {}).get("forecast") or []
    if not fc:
        return
    exists = db.query(ForecastSet).filter_by(company_id=company_id, method="client",
                                             dataset_version=ds.version).first()
    if exists:
        return
    keep = set(str(y) for y in fc)
    stmts = {"periods": {"forecast": list(fc)},
             "income_statement": {k: {y: v for y, v in ds.data["income_statement"].get(k, {}).items() if y in keep} for k in fin.IS_KEYS},
             "balance_sheet": {k: {y: v for y, v in ds.data["balance_sheet"].get(k, {}).items() if y in keep} for k in fin.BS_KEYS},
             "cash_flow": {k: {y: v for y, v in ds.data["cash_flow"].get(k, {}).items() if y in keep} for k in fin.CF_KEYS}}
    row = ForecastSet(company_id=company_id, dataset_version=ds.version, method="client",
                      label=_LABELS["client"], source="client", horizon=len(fc),
                      fitted_history_len=len(ds.data["periods"].get("historical", [])),
                      statements=stmts, is_primary=True)   # client's own is default primary
    db.add(row); db.flush()


def _upsert_set(db, company_id, dsver, method, source, horizon, stmts, extra):
    row = db.query(ForecastSet).filter_by(company_id=company_id, method=method,
                                          dataset_version=dsver).first()
    was_primary = row.is_primary if row else False
    if row is None:
        row = ForecastSet(company_id=company_id, dataset_version=dsver, method=method,
                          source=source, is_primary=False)
        db.add(row)
    row.label = _LABELS.get(method, method)
    row.horizon = horizon
    row.statements = stmts
    row.drivers = extra.get("drivers")
    row.bands = extra.get("bands")
    row.weights = extra.get("weights")
    row.divergence = extra.get("divergence")
    row.fitted_history_len = extra.get("fitted_history_len", 0)
    row.is_primary = was_primary
    db.flush()
    # default primary: if no primary exists yet, ensemble (else client already primary)
    if not db.query(ForecastSet).filter_by(company_id=company_id, is_primary=True).first() \
            and method == "ensemble":
        row.is_primary = True
    return row


def _set_out(row):
    return {"set_id": row.id, "method": row.method, "label": row.label, "source": row.source,
            "horizon": row.horizon, "fitted_history_len": row.fitted_history_len,
            "is_primary": row.is_primary, "drivers": row.drivers, "bands": row.bands,
            "weights": row.weights, "divergence": row.divergence,
            "forecast_years": (row.statements or {}).get("periods", {}).get("forecast", []),
            "created_at": row.created_at}


# ======================================================================
# set-primary + eager bounded recompute
# ======================================================================
def set_primary(db, company_id, set_id):
    row = db.query(ForecastSet).filter_by(id=set_id, company_id=company_id).first()
    if not row:
        raise HTTPException(404, "forecast set not found")
    ds = _active_company_dataset(db, company_id)
    if not ds or not isinstance(ds.data, dict):
        raise HTTPException(409, "No active dataset for this company.")
    # write the set's forecast into the active dataset's forecast columns (historicals
    # untouched); the kernel consumes exactly this.
    data = dict(ds.data)
    hist = list((data.get("periods") or {}).get("historical", []))
    fstmts = row.statements
    data["periods"] = {"historical": hist,
                       "forecast": list(fstmts["periods"]["forecast"])}
    for block, keys in (("income_statement", fin.IS_KEYS), ("balance_sheet", fin.BS_KEYS),
                        ("cash_flow", fin.CF_KEYS)):
        merged = {}
        for k in keys:
            hv = {str(y): data[block].get(k, {}).get(str(y)) for y in hist}
            fv = fstmts[block].get(k, {})
            merged[k] = {**hv, **fv}
        data[block] = merged
    ds.data = data
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(ds, "data")
    for other in db.query(ForecastSet).filter_by(company_id=company_id).all():
        other.is_primary = (other.id == row.id)
    db.commit()
    # eager bounded recompute: frontier + viability (background thread)
    progress = {"status": "recomputing", "steps": ["frontier", "viability"]}
    try:
        from .prescience_decision import _spawn_recompute
        _spawn_recompute(company_id)
        progress["spawned"] = True
    except Exception:
        progress["spawned"] = False
    return {"primary_set_id": row.id, "method": row.method, "recompute": progress}


# ======================================================================
# API
# ======================================================================
forecast_router = APIRouter(tags=["forecast-studio"])


class GenerateIn(BaseModel):
    methods: list[str] = Field(default_factory=lambda: list(METHODS))
    horizon: int = 5


@forecast_router.post("/companies/{company_id}/forecast/generate", status_code=201)
def generate_endpoint(company_id: int, body: GenerateIn,
                      member=Depends(require_company_admin),
                      user=Depends(get_current_user), db=Depends(get_db)):
    sets = generate(db, company_id, body.methods, body.horizon)
    audit(db, user.id, "forecast_generated", "company", company_id,
          detail=f"methods={body.methods} horizon={body.horizon}")
    db.commit()
    return {"company_id": company_id, "sets": sets}


@forecast_router.get("/companies/{company_id}/forecast/sets")
def list_sets(company_id: int, member=Depends(require_company_member), db=Depends(get_db)):
    rows = db.query(ForecastSet).filter_by(company_id=company_id).order_by(ForecastSet.id).all()
    return {"company_id": company_id, "sets": [_set_out(r) for r in rows]}


@forecast_router.get("/companies/{company_id}/forecast/sets/{set_id}")
def get_set(company_id: int, set_id: int, member=Depends(require_company_member), db=Depends(get_db)):
    row = db.query(ForecastSet).filter_by(id=set_id, company_id=company_id).first()
    if not row:
        raise HTTPException(404, "forecast set not found")
    return {**_set_out(row), "statements": row.statements}


@forecast_router.post("/companies/{company_id}/forecast/sets/{set_id}/primary", status_code=201)
def set_primary_endpoint(company_id: int, set_id: int,
                         member=Depends(require_company_admin),
                         user=Depends(get_current_user), db=Depends(get_db)):
    res = set_primary(db, company_id, set_id)
    audit(db, user.id, "forecast_set_primary", "company", company_id, detail=f"set={set_id}")
    db.commit()
    return res
