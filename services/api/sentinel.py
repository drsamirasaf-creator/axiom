"""AXIOM PRESCIENCE — Phase 7i: Corporate Viability Kernel (Sentinel) + Radar.

The viability kernel measures how far a company is from failure. It bisects along
shock rays (single-dimension and named simultaneous combos) to the nearest failure
surface, using the certified engines as the failure detector:
  * EV < debt              (valuation.run deterministic)
  * distance-to-default    (valuation.run MC tail: (ev_mean - debt)/ev_std)
  * stochastic cash < 0    (twin.simulate recession p_cash_below_zero)
  * covenant breach        (intelligence.covenants)
CHEAP detector = run(n=100) + simulate(n=500) + covenants (~3ms) for the bisection
search; FULL detector (n=2000) confirms the surface and the 12-month breach prob.

Bands STABLE/FRAGILE/CRITICAL by distance thresholds (config, persisted in the
payload). Nearest-breach rendered in plain terms; minimum-intervention prescriptions
found by reverse-search over the 7c-2 lever library and emitted as recommendation
dispositions. Critical-slowing-down indicators from available history (honest
available:false below CSD_MIN_YEARS).

Radar diffs successive nightly snapshots (frontier headline + viability state) and
persists change events. No notification delivery — storage + API only.

v2 (true Aubin kernels, bifurcation surfaces, contagion) is OUT — not built here.
"""
import os
import copy
import json
import hashlib
import math
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import (Column, DateTime, Integer, String, Text, JSON, Float,
                        Boolean, UniqueConstraint)

from . import accounts as A
from .accounts import (Base, get_db, require_company_member, audit,
                       _active_company_dataset, _is_showcase_company,
                       RecommendationDisposition, _get_or_create_disp)
from . import prescience_decision as PD
from .modules.valuation import engines as V
from .modules.twin import engines as T
from .modules.intelligence import engines as I

sentinel_router = APIRouter(tags=["sentinel"])

# ---- config (all env-overridable; band thresholds persisted in the payload) ----
def _cf(k, d): return float(os.environ.get(k, str(d)))
def _ci(k, d): return int(os.environ.get(k, str(d)))

STABLE_MIN = _cf("AXIOM_VIA_STABLE_MIN", 0.20)     # distance t* above -> STABLE
FRAGILE_MIN = _cf("AXIOM_VIA_FRAGILE_MIN", 0.08)   # t* below -> CRITICAL
FAIL_DD_MIN = _cf("AXIOM_VIA_DD_MIN", 1.0)         # distance-to-default < 1 sigma -> fail
FAIL_CASH_P = _cf("AXIOM_VIA_CASH_P", 0.20)        # P(cash<0) recession > 20% -> fail
CSD_MIN_YEARS = _ci("AXIOM_VIA_CSD_MIN_YEARS", 8)
CHEAP_RUN, CHEAP_SIM = _ci("AXIOM_VIA_CHEAP_RUN", 100), _ci("AXIOM_VIA_CHEAP_SIM", 500)
FULL_RUN, FULL_SIM = _ci("AXIOM_VIA_FULL_RUN", 2000), _ci("AXIOM_VIA_FULL_SIM", 2000)
BISECT_STEPS = _ci("AXIOM_VIA_BISECT_STEPS", 8)
T_MAX = _cf("AXIOM_VIA_TMAX", 1.0)
RADAR_DELTA_EV = _cf("AXIOM_RADAR_DELTA_EV", 50.0)  # material ΔEV move ($M)

# a shock intensity t in [0,1] maps to these natural-unit reference severities at t=1
SHOCK_REF = {"revenue": 0.50, "margin": 0.10, "rate": 0.05, "wc": 0.50}
# shock rays: single dimensions + the three approved named combos
RAYS = {
    "revenue": {"revenue": 1.0},
    "margin": {"margin": 1.0},
    "rate": {"rate": 1.0},
    "working_capital": {"wc": 1.0},
    "recession": {"revenue": 1.0, "margin": 1.0},
    "stagflation": {"revenue": 1.0, "rate": 1.0},
    "credit_crunch": {"rate": 1.0, "wc": 1.0},
}
_DIM_LABEL = {"revenue": "revenue decline", "margin": "margin compression",
              "rate": "rate rise", "wc": "working-capital build"}


# ======================================================================
# models (accounts.Base -> ax_* tables auto-created at boot)
# ======================================================================
class Viability(Base):
    __tablename__ = "ax_viability"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    dataset_version = Column(Integer, nullable=False)
    library_signature = Column(String(64), nullable=False)
    band = Column(String(12), nullable=False)
    overall_distance = Column(Float, nullable=False)
    payload = Column(JSON, nullable=False)
    computed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("company_id", "dataset_version",
                                       "library_signature", name="uq_viability"),)


class RadarSnapshot(Base):
    __tablename__ = "ax_radar_snapshots"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    band = Column(String(12), nullable=True)
    nearest_ray = Column(String(24), nullable=True)
    delta_ev = Column(Float, nullable=True)
    optimal_hash = Column(String(32), nullable=True)
    headline = Column(JSON, nullable=False)
    taken_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class RadarEvent(Base):
    __tablename__ = "ax_radar_events"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    event_type = Column(String(32), nullable=False)
    summary = Column(Text, nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ======================================================================
# shock application + failure detector
# ======================================================================
def _apply_shock(work, sv, wacc_mods):
    """Adverse shock on a proforma working dataset (in place). Reuses the 7c-2
    cell-mutation shape; rate feeds the shared wacc_mods (composes with moves)."""
    IS, BS = work["income_statement"], work["balance_sheet"]
    fy = [int(y) for y in work["periods"]["forecast"]]
    s_rev, s_mar = sv.get("revenue", 0.0), sv.get("margin", 0.0)
    s_wc, s_rate = sv.get("wc", 0.0), sv.get("rate", 0.0)
    for y in fy:
        ys = str(y)
        if s_rev > 0:                              # volume shock: revenue + variable costs down
            IS["revenue"][ys] *= (1 - s_rev)
            for k in ("cogs", "opex", "depreciation_amortization"):
                IS[k][ys] *= (1 - s_rev)
        if s_mar > 0:                              # margin compression: raise cost lines
            rev = IS["revenue"][ys]
            IS["cogs"][ys] += s_mar * rev * 0.6
            IS["opex"][ys] += s_mar * rev * 0.4
        if s_wc > 0:                               # more working capital tied up
            BS["other_current_assets"][ys] *= (1 + s_wc)
    if s_rate > 0:
        wacc_mods["kd_delta"] = wacc_mods.get("kd_delta", 0.0) + s_rate


def _debt_book(work):
    ys = str(int(work["periods"]["historical"][-1]))
    bs = work["balance_sheet"]
    return bs["short_term_debt"][ys] + bs["long_term_debt"][ys]


def _detect(work, assumptions, tier="cheap"):
    """True if the shocked company is in failure by ANY of the four conditions."""
    npr = CHEAP_RUN if tier == "cheap" else FULL_RUN
    nps = CHEAP_SIM if tier == "cheap" else FULL_SIM
    r = V.run(work, "proforma", assumptions, {"n_paths": npr})
    det, ra = r["deterministic"], r["risk_adjusted"]
    debt = _debt_book(work)
    ev = det["enterprise_value"]
    dd = (ra["mean"] - debt) / ra["std"] if ra.get("std") else None
    sim = T.simulate(work, "recession", n_paths=nps)
    p_cash = sim["p_cash_below_zero_ever"]
    cov = I.covenants(work)
    cov_breach = (cov.get("overall_status") == "red"
                  or any((t.get("headroom") or 0) < 0 for t in cov.get("tests", [])))
    signals = {
        "ev_below_debt": ev < debt, "ev": round(ev, 1), "debt": round(debt, 1),
        "distance_to_default": round(dd, 2) if dd is not None else None,
        "dd_collapse": bool(dd is not None and dd < FAIL_DD_MIN),
        "p_cash_below_zero": p_cash, "cash_fail": p_cash > FAIL_CASH_P,
        "covenant_breach": bool(cov_breach)}
    failed = (signals["ev_below_debt"] or signals["dd_collapse"]
              or signals["cash_fail"] or signals["covenant_breach"])
    return failed, signals


def _nearest_t(data, direction, tier="cheap", pre_moves=None):
    """Bisect the shock intensity t in [0, T_MAX] to the smallest t that fails.
    pre_moves (7c-2 lever moves) are applied first — used by the prescription
    reverse-search to test whether a move restores STABLE."""
    base, _ = PD._materialize(data)
    pre_wacc = {}
    if pre_moves:
        for m in sorted(pre_moves, key=lambda x: PD.ATOM_TYPES.index(x["atom_type"])):
            PD._apply_move(base, m, pre_wacc)

    def failed_at(t):
        w = copy.deepcopy(base)
        wm = dict(pre_wacc)
        _apply_shock(w, {d: t * SHOCK_REF[d] for d in direction}, wm)
        assumptions = {"wacc_override": PD._wacc_override(w, wm)} if wm else {}
        return _detect(w, assumptions, tier)[0]

    if failed_at(0.0):
        return 0.0                     # already failing unshocked
    if not failed_at(T_MAX):
        return T_MAX                   # survives even a severe shock along this ray
    lo, hi = 0.0, T_MAX
    for _ in range(BISECT_STEPS):
        mid = (lo + hi) / 2.0
        if failed_at(mid):
            hi = mid
        else:
            lo = mid
    return round(hi, 4)


def _band(t):
    return "STABLE" if t >= STABLE_MIN else ("FRAGILE" if t >= FRAGILE_MIN else "CRITICAL")


def _plain(ray, t):
    """Natural-unit rendering of the nearest breach, e.g. 'a 12% revenue decline
    combined with a 150bps rate rise'."""
    if t <= 1e-6:
        return "already in breach at current conditions (no shock required)"
    parts = []
    for d in RAYS[ray]:
        mag = t * SHOCK_REF[d]
        if d == "rate":
            parts.append(f"a {mag*10000:.0f}bps rate rise")
        else:
            parts.append(f"a {mag*100:.0f}% {_DIM_LABEL[d]}")
    return " combined with ".join(parts)


# ======================================================================
# 12-month breach probability + CSD indicators
# ======================================================================
def _breach_probability_12m(data):
    work, _ = PD._materialize(data)
    r = V.run(work, "proforma", {}, {"n_paths": FULL_RUN}, _keep_paths=True)
    paths = r["risk_adjusted"].get("_paths") or []
    debt = _debt_book(work)
    p_ev = (sum(1 for e in paths if e < debt) / len(paths)) if paths else 0.0
    p_cash = T.simulate(work, "recession", n_paths=FULL_SIM)["p_cash_below_zero_ever"]
    combined = 1.0 - (1.0 - p_ev) * (1.0 - p_cash)   # union, independence approx
    return {"p_ev_below_debt": round(p_ev, 4), "p_cash_below_zero": round(p_cash, 4),
            "combined": round(combined, 4),
            "definition": "P(EV<debt or cash<0 within the horizon), independence approx"}


def _csd(data):
    hist = [int(y) for y in data["periods"]["historical"]]
    n = len(hist)
    if n < CSD_MIN_YEARS:
        return {"available": False, "history_years": n,
                "reason": f"insufficient history ({n} < {CSD_MIN_YEARS} yrs) for a "
                          "critical-slowing-down trend"}
    IS = data["income_statement"]
    rev = [IS["revenue"][str(y)] for y in hist]
    g = [rev[i] / rev[i - 1] - 1.0 for i in range(1, n)]     # revenue-growth series
    mean = sum(g) / len(g)
    dev = [x - mean for x in g]
    var = sum(d * d for d in dev) / len(dev)
    num = sum(dev[i] * dev[i - 1] for i in range(1, len(dev)))
    den = sum(d * d for d in dev) or 1e-9
    ac1 = num / den
    half = len(g) // 2
    v1 = sum((x - sum(g[:half]) / half) ** 2 for x in g[:half]) / max(half, 1)
    v2 = sum((x - sum(g[half:]) / (len(g) - half)) ** 2 for x in g[half:]) / max(len(g) - half, 1)
    return {"available": True, "history_years": n, "lag1_autocorrelation": round(ac1, 3),
            "variance": round(var, 6), "variance_rising": bool(v2 > v1),
            "note": "rising variance + AC1 near 1 indicate critical slowing down"}


# ======================================================================
# minimum-intervention prescriptions (reverse-search the 7c-2 lever library)
# ======================================================================
def _prescribe(db, company_id, data, nearest_ray):
    """Smallest accretive library move that lifts the nearest-breach ray back to
    STABLE. Cheap: only the nearest ray is re-bisected per candidate move."""
    PD._ensure_seeded(db, company_id)
    moves = [PD._move_to_dict(m) for m in db.query(PD.StrategicMove)
             .filter_by(company_id=company_id, enabled=True).all()]
    direction = RAYS[nearest_ray]
    restorers = []
    for mv in moves:
        try:
            t2 = _nearest_t(data, direction, tier="cheap", pre_moves=[mv])
        except Exception:
            continue
        if t2 >= STABLE_MIN:
            restorers.append((abs(float(mv["magnitude"])), mv, t2))
    restorers.sort(key=lambda x: x[0])
    out = []
    for mag, mv, t2 in restorers[:3]:
        fp = hashlib.sha256(f"viability:{company_id}:{mv['atom_type']}:{mv['magnitude']}"
                            .encode()).hexdigest()[:32]
        out.append({"lever": mv["atom_type"], "label": mv.get("label"),
                    "magnitude": mv["magnitude"], "restores_distance": t2,
                    "fingerprint": fp,
                    "plain": f"{mv.get('label') or mv['atom_type']} restores STABLE "
                             f"(nearest-breach distance {t2:.2f})"})
    return out


def _emit_prescription_dispositions(db, company_id, prescriptions):
    """Flow prescriptions into the existing disposition/initiative machinery."""
    for p in prescriptions:
        d = _get_or_create_disp(db, company_id, p["fingerprint"])
        d.last_seen_at = datetime.utcnow()
        d.times_reissued = (d.times_reissued or 0) + 1
        if not d.note:
            d.note = "Sentinel viability prescription: " + p["plain"]


# ======================================================================
# the kernel
# ======================================================================
def _lib_sig(db, company_id):
    PD._ensure_seeded(db, company_id)
    moves = [PD._move_to_dict(m) for m in db.query(PD.StrategicMove)
             .filter_by(company_id=company_id, enabled=True).all()]
    return PD.library_signature(moves)


def viability_current(db, company_id, dataset_version, library_signature) -> bool:
    return db.query(Viability.id).filter_by(
        company_id=company_id, dataset_version=dataset_version,
        library_signature=library_signature).first() is not None


def compute_viability(db, company_id, use_cache=True):
    """Compute (or return cached) viability. Persists ax_viability. Read-safe:
    writes only the viability cache, never dispositions (that is the recompute
    path's job)."""
    ds = _active_company_dataset(db, company_id)
    if not ds or not isinstance(ds.data, dict):
        raise HTTPException(409, "No active dataset for this company.")
    dsver = ds.version
    sig = _lib_sig(db, company_id)
    if use_cache:
        row = db.query(Viability).filter_by(
            company_id=company_id, dataset_version=dsver, library_signature=sig).first()
        if row:
            out = dict(row.payload); out["cached"] = True; out["computed_at"] = row.computed_at
            return out
    data = ds.data
    distances = {name: _nearest_t(data, direction, tier="cheap")
                 for name, direction in RAYS.items()}
    overall = min(distances.values())
    nearest_ray = min(distances, key=distances.get)
    band = _band(overall)
    prescriptions = _prescribe(db, company_id, data, nearest_ray) if band != "STABLE" else []
    payload = {
        "band": band, "overall_distance": round(overall, 4),
        "thresholds": {"stable_min": STABLE_MIN, "fragile_min": FRAGILE_MIN},
        "distances": {k: round(v, 4) for k, v in distances.items()},
        "nearest_breach": {"ray": nearest_ray, "distance": round(distances[nearest_ray], 4),
                           "plain": _plain(nearest_ray, distances[nearest_ray])},
        "breach_probability_12m": _breach_probability_12m(data),
        "prescriptions": prescriptions,
        "csd": _csd(data),
        "shock_reference": SHOCK_REF,
        "dataset_version": dsver,
    }
    row = db.query(Viability).filter_by(
        company_id=company_id, dataset_version=dsver, library_signature=sig).first()
    if row:
        row.band, row.overall_distance, row.payload = band, overall, payload
        row.computed_at = datetime.utcnow()
    else:
        db.add(Viability(company_id=company_id, dataset_version=dsver, library_signature=sig,
                         band=band, overall_distance=overall, payload=payload))
    db.commit()
    out = dict(payload); out["cached"] = False; out["computed_at"] = datetime.utcnow()
    return out


# ======================================================================
# Radar — snapshot + diff -> events
# ======================================================================
def _frontier_headline(db, company_id):
    ds = _active_company_dataset(db, company_id)
    if not ds:
        return None
    row = (db.query(PD.DecisionFrontier).filter_by(company_id=company_id, dataset_version=ds.version)
           .order_by(PD.DecisionFrontier.built_at.desc()).first())
    if not row:
        return None
    f = row.frontier
    opt = f.get("optimal_sequence", {})
    return {"optimal_moves": [m.get("atom_type") for m in opt.get("moves", [])],
            "delta_ev": opt.get("delta_ev"), "raev": opt.get("raev"),
            "current_strategy_percentile": f.get("current_strategy_percentile")}


def update_radar(db, company_id, viability_payload=None):
    """Snapshot (frontier headline + viability state) and diff vs the previous
    snapshot, emitting change events. Returns the events emitted."""
    if viability_payload is None:
        v = db.query(Viability).filter_by(company_id=company_id).order_by(
            Viability.computed_at.desc()).first()
        viability_payload = v.payload if v else {}
    fh = _frontier_headline(db, company_id) or {}
    band = viability_payload.get("band")
    nearest = (viability_payload.get("nearest_breach") or {}).get("ray")
    delta_ev = fh.get("delta_ev")
    opt_moves = fh.get("optimal_moves") or []
    opt_hash = hashlib.sha256(json.dumps(opt_moves, sort_keys=True).encode()).hexdigest()[:32]
    headline = {"viability": {"band": band, "nearest_ray": nearest,
                              "overall_distance": viability_payload.get("overall_distance")},
                "frontier": fh}
    prev = (db.query(RadarSnapshot).filter_by(company_id=company_id)
            .order_by(RadarSnapshot.taken_at.desc()).first())
    events = []
    def emit(etype, summary, payload):
        db.add(RadarEvent(company_id=company_id, event_type=etype, summary=summary, payload=payload))
        events.append(etype)
    if prev:
        if prev.band and band and prev.band != band:
            emit("band_transition", f"Viability moved {prev.band} → {band}.",
                 {"from": prev.band, "to": band, "overall_distance": viability_payload.get("overall_distance")})
        if prev.nearest_ray and nearest and prev.nearest_ray != nearest:
            emit("nearest_breach_change", f"Nearest breach shifted {prev.nearest_ray} → {nearest}.",
                 {"from": prev.nearest_ray, "to": nearest,
                  "plain": (viability_payload.get("nearest_breach") or {}).get("plain")})
        if prev.optimal_hash and prev.optimal_hash != opt_hash:
            emit("optimal_sequence_change", "The optimal decision sequence changed.",
                 {"to_moves": opt_moves})
        if (prev.delta_ev is not None and delta_ev is not None
                and abs(prev.delta_ev - delta_ev) > RADAR_DELTA_EV):
            emit("material_delta_ev", f"Optimal ΔEV moved {prev.delta_ev:.0f} → {delta_ev:.0f}.",
                 {"from": prev.delta_ev, "to": delta_ev})
    db.add(RadarSnapshot(company_id=company_id, band=band, nearest_ray=nearest,
                         delta_ev=delta_ev, optimal_hash=opt_hash, headline=headline))
    db.commit()
    return events


# ======================================================================
# unified recompute (frontier + viability + radar + dispositions)
# ======================================================================
def sentinel_recompute(db, company_id, do_frontier=True):
    if do_frontier:
        try:
            PD.build_frontier(db, company_id)
        except Exception:
            pass
    v = compute_viability(db, company_id, use_cache=False)
    try:
        _emit_prescription_dispositions(db, company_id, v.get("prescriptions", []))
        db.commit()
    except Exception:
        db.rollback()
    update_radar(db, company_id, v)
    return v


# ======================================================================
# API
# ======================================================================
@sentinel_router.get("/companies/{company_id}/viability")
def get_viability(company_id: int, _role=Depends(A._summary_access), db=Depends(get_db)):
    """Viability bands/distances/nearest-breach/prescriptions/CSD. Anonymous read
    for SHOWCASE companies (via _summary_access), member-gated otherwise."""
    return compute_viability(db, company_id, use_cache=True)


@sentinel_router.get("/companies/{company_id}/radar/events")
def get_radar_events(company_id: int, since: int = 0, limit: int = 50,
                     member=Depends(require_company_member), db=Depends(get_db)):
    """Paged radar change feed. `since` is an id cursor (exclusive)."""
    limit = max(1, min(limit, 200))
    q = db.query(RadarEvent).filter(RadarEvent.company_id == company_id)
    if since:
        q = q.filter(RadarEvent.id > since)
    rows = q.order_by(RadarEvent.id).limit(limit).all()
    return {"events": [{"id": r.id, "event_type": r.event_type, "summary": r.summary,
                        "payload": r.payload, "created_at": r.created_at} for r in rows],
            "next_cursor": rows[-1].id if rows else since}


@sentinel_router.post("/internal/sentinel/recompute")
def internal_sentinel_recompute(only_stale: bool = True, authorization: str = Header(None),
                                db=Depends(get_db)):
    """Protected recompute (external cron), mirroring the frontier's internal endpoint."""
    from .core.config import admin_token
    tok = admin_token()
    if not tok or authorization != f"Bearer {tok}":
        raise HTTPException(403, "admin token required")
    return PD.recompute_all_frontiers(only_stale=only_stale)
