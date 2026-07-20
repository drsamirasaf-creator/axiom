"""AXIOM PRESCIENCE — Phase 7c-2: Multiverse evaluation kernel, Strategic Move
Library, and decision search (the Strategic Decision Frontier).

Design (recon-approved):
  * The certified valuation kernel `valuation.run` is the per-node evaluator.
    CHEAP tier = run(n_paths=100); FULL tier = run(n_paths=2000) + real options
    + TV-DRO robustness (valuation.stress) + P(target).
  * A "move" mutates the proforma dataset along the timeline; a "trajectory" is a
    set of <= MAX_MOVES distinct-atom moves. Search is a bounded beam over the
    set-lattice: cheap-screen for breadth, full-evaluate the survivors + the
    do-nothing baseline (like-for-like percentile).
  * Objective = raev = (1-lambda)*mean + lambda*CVaR95 (lambda persisted).
  * DRO is Total-Variation (reused, certified) — NOT Wasserstein.
  * evaluate_trajectory is deterministic given (dataset_version, move set, tier)
    -> cached. Frontiers cached by (company, dataset_version, library signature).
  * Nightly recompute via a boot daemon thread with a DB single-flight guard,
    plus a protected /internal/frontier/recompute endpoint.
"""
import os
import copy
import json
import hashlib
import threading
import time as _time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy import (Column, DateTime, Integer, String, Text, JSON, Boolean,
                        Float, UniqueConstraint, func)

from . import accounts as A
from .accounts import (Base, get_db, require_company_member, require_company_admin,
                       get_current_user, audit, _active_company_dataset)
from .modules.valuation import engines as V
from .modules.financials import engines as fin
from .modules.intelligence import engines as intel

decision_router = APIRouter(tags=["prescience-decision"])

# ---- config (recon-approved bounds, env-overridable) -----------------------
def _cfg_int(k, d): return int(os.environ.get(k, str(d)))
def _cfg_float(k, d): return float(os.environ.get(k, str(d)))

MAX_MOVES = _cfg_int("AXIOM_DECISION_MAX_MOVES", 3)
CHEAP_SCREEN_CAP = _cfg_int("AXIOM_DECISION_CHEAP_CAP", 40000)
FULL_SURVIVORS = _cfg_int("AXIOM_DECISION_FULL_SURVIVORS", 400)
BEAM_WIDTH = _cfg_int("AXIOM_DECISION_BEAM", 24)
CHEAP_PATHS = _cfg_int("AXIOM_DECISION_CHEAP_PATHS", 100)
FULL_PATHS = _cfg_int("AXIOM_DECISION_FULL_PATHS", 2000)
LAMBDA = _cfg_float("AXIOM_DECISION_LAMBDA", 0.5)
NIGHTLY_ENABLED = os.environ.get("AXIOM_DECISION_NIGHTLY", "").strip().lower() in ("1", "true", "yes", "on")
# Phase 7i: the Sentinel (viability + radar) family folds into THIS one scheduler /
# one single-flight lock. Env-gated separately, default off until cost is reported.
SENTINEL_NIGHTLY = os.environ.get("AXIOM_SENTINEL_NIGHTLY", "").strip().lower() in ("1", "true", "yes", "on")
NIGHTLY_PERIOD_S = _cfg_int("AXIOM_DECISION_NIGHTLY_PERIOD", 86400)

ATOM_TYPES = ("revenue", "pricing", "cost", "working_capital", "capex",
              "refinancing", "capital_structure", "entity")

# default move templates seeded per company (magnitude, timing default), all
# value-accretive at these bounds — the frontier discovers which combination wins
DEFAULT_TEMPLATES = [
    ("revenue", "Accelerate organic growth +2pp", 0.02),
    ("revenue", "Accelerate organic growth +3pp", 0.03),
    ("pricing", "Price realization +2%", 0.02),
    ("pricing", "Price realization +3%", 0.03),
    ("cost", "Cost-out program -3% opex/cogs", 0.03),
    ("cost", "Cost-out program -5% opex/cogs", 0.05),
    ("working_capital", "Release working capital -10%", 0.10),
    ("working_capital", "Release working capital -20%", 0.20),
    ("capex", "Capex discipline -15%", 0.15),
    ("capex", "Capex discipline -25%", 0.25),
    ("refinancing", "Refinance debt -100bps", 0.010),
    ("refinancing", "Refinance debt -150bps", 0.015),
    ("capital_structure", "Optimize leverage +25% debt", 0.25),
    ("capital_structure", "Optimize leverage +50% debt", 0.50),
]


# ======================================================================
# models (accounts.Base -> ax_* tables auto-created at boot)
# ======================================================================
class StrategicMove(Base):
    __tablename__ = "ax_strategic_moves"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    atom_type = Column(String(24), nullable=False)
    label = Column(String(200), nullable=False)
    magnitude = Column(Float, nullable=False)
    start_year = Column(Integer, nullable=True)          # None -> first forecast year
    params = Column(JSON, default=dict, nullable=False)  # entity cell_deltas, prereqs, excludes
    source = Column(String(16), default="template", nullable=False)  # template|user|entity
    enabled = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DecisionFrontier(Base):
    __tablename__ = "ax_decision_frontiers"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    dataset_version = Column(Integer, nullable=False)
    library_signature = Column(String(64), nullable=False)
    lambda_ = Column("lambda", Float, nullable=False)
    frontier = Column(JSON, nullable=False)
    trajectories_evaluated = Column(Integer, default=0, nullable=False)
    node_cost = Column(JSON, default=dict, nullable=False)   # {cheap, full, wall_s}
    built_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("company_id", "dataset_version",
                                       "library_signature", name="uq_frontier"),)


class TrajectoryCache(Base):
    __tablename__ = "ax_trajectory_cache"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    dataset_version = Column(Integer, nullable=False)
    seq_hash = Column(String(64), nullable=False)
    tier = Column(String(8), nullable=False)
    metrics = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("company_id", "dataset_version", "seq_hash",
                                       "tier", name="uq_traj"),)


class DPPolicySurface(Base):
    __tablename__ = "ax_dp_policy_surfaces"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    dataset_version = Column(Integer, nullable=False)
    surface = Column(JSON, nullable=False)
    built_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("company_id", "dataset_version", name="uq_surface"),)


class FrontierJob(Base):
    __tablename__ = "ax_frontier_jobs"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    status = Column(String(12), default="queued", nullable=False)  # queued|running|done|error
    progress = Column(Integer, default=0, nullable=False)          # 0..100
    phase = Column(String(40), default="", nullable=False)
    result_frontier_id = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class NightlyLock(Base):
    """Single row (id=1) single-flight guard so only one replica runs the sweep."""
    __tablename__ = "ax_decision_nightly_lock"
    id = Column(Integer, primary_key=True)
    running = Column(Boolean, default=False, nullable=False)
    started_at = Column(DateTime, nullable=True)
    last_completed_at = Column(DateTime, nullable=True)


# ======================================================================
# move application — mutate a proforma working dataset along the timeline
# ======================================================================
def _materialize(data):
    """Return a (working dataset with forecast years, 'proforma')."""
    if data.get("periods", {}).get("forecast"):
        return copy.deepcopy(data), "proforma"
    work = fin.auto_forecast(data, {})       # materialize forecast years
    return work, "proforma"


def _fyears(work, start_year):
    fs = [int(y) for y in work["periods"]["forecast"]]
    y0 = start_year if start_year is not None else (fs[0] if fs else None)
    return [y for y in fs if y0 is not None and y >= y0], fs


def _apply_move(work, move, wacc_mods):
    """Mutate `work` in place for one move; accumulate WACC-affecting changes."""
    atom, mag = move["atom_type"], float(move["magnitude"])
    years, all_fy = _fyears(work, move.get("start_year"))
    IS, BS, CF = work["income_statement"], work["balance_sheet"], work["cash_flow"]
    hist = [int(y) for y in work["periods"]["historical"]]

    if atom == "revenue":
        orig = {int(y): IS["revenue"][str(y)] for y in all_fy}
        prev_year = None
        rev_prev = IS["revenue"][str(hist[-1])]
        for y in all_fy:
            ys = str(y)
            base_g = (orig[y] / (orig[prev_year] if prev_year in orig else rev_prev)) - 1.0 \
                if prev_year is not None else (orig[y] / rev_prev - 1.0)
            g = base_g + (mag if y in years else 0.0)
            new_rev = (IS["revenue"][str(prev_year)] if prev_year is not None else rev_prev) * (1 + g)
            scale = new_rev / orig[y] if orig[y] else 1.0
            for k in ("cogs", "opex", "depreciation_amortization"):
                IS[k][ys] *= scale
            IS["revenue"][ys] = new_rev
            prev_year = y
    elif atom == "pricing":
        # price realization: lift revenue, hold cost -> margin & EV up
        for y in years:
            IS["revenue"][str(y)] *= (1.0 + mag)
    elif atom == "cost":
        for y in years:
            IS["cogs"][str(y)] *= (1.0 - mag)
            IS["opex"][str(y)] *= (1.0 - mag)
    elif atom == "working_capital":
        for y in years:
            BS["other_current_assets"][str(y)] *= (1.0 - mag)
    elif atom == "capex":
        for y in years:
            CF["capex"][str(y)] *= (1.0 - mag)
    elif atom == "refinancing":
        wacc_mods["kd_delta"] = wacc_mods.get("kd_delta", 0.0) - mag
    elif atom == "capital_structure":
        wacc_mods["debt_scale"] = wacc_mods.get("debt_scale", 1.0) * (1.0 + mag)
    elif atom == "entity":
        # params.cell_deltas = {statement: {line: {year: delta}}} — additive
        deltas = (move.get("params") or {}).get("cell_deltas", {})
        blocks = {"income_statement": IS, "balance_sheet": BS, "cash_flow": CF}
        for stmt, lines in deltas.items():
            blk = blocks.get(stmt)
            if not blk:
                continue
            for line, byyear in lines.items():
                if line not in blk:
                    continue
                for y, dv in byyear.items():
                    if str(y) in blk[line]:
                        blk[line][str(y)] += float(dv)


def _wacc_override(work, wacc_mods):
    """Recompute certified WACC after refinancing / capital-structure moves."""
    c = dict(work["company"])
    ys = str(int(work["periods"]["historical"][-1]))
    bs = work["balance_sheet"]
    debt = (bs["short_term_debt"][ys] + bs["long_term_debt"][ys]) * wacc_mods.get("debt_scale", 1.0)
    c["_debt_book"] = debt
    kd = c.get("cost_of_debt", 0.06) + wacc_mods.get("kd_delta", 0.0)
    c["cost_of_debt"] = max(0.0001, kd)
    return float(fin.wacc(c)["wacc"])


# ======================================================================
# the evaluation kernel
# ======================================================================
def _seq_hash(moves):
    key = sorted([(m["atom_type"], round(float(m["magnitude"]), 6),
                   m.get("start_year"), json.dumps((m.get("params") or {}), sort_keys=True))
                  for m in moves])
    return hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:32]


def evaluate_trajectory(data, moves, tier="cheap", target_ev=None, lam=LAMBDA):
    """Apply the move set to a proforma working dataset, run the certified kernel,
    attach CVaR (+ real options, TV-DRO, P(target) at full tier). Deterministic."""
    work, mode = _materialize(data)
    wacc_mods = {}
    for m in sorted(moves, key=lambda x: ATOM_TYPES.index(x["atom_type"])):
        _apply_move(work, m, wacc_mods)
    assumptions = {}
    if wacc_mods:
        assumptions["wacc_override"] = _wacc_override(work, wacc_mods)
    n_paths = CHEAP_PATHS if tier == "cheap" else FULL_PATHS
    base = V.run(work, mode, assumptions, {"n_paths": n_paths}, _keep_paths=(tier == "full"))
    det = base["deterministic"]; ra = base["risk_adjusted"]
    ev = det["enterprise_value"]; mean = ra["mean"]; cvar = ra["cvar95"]
    raev = (1.0 - lam) * mean + lam * cvar
    metrics = {"ev": round(ev, 2), "equity_value": det.get("equity_value"),
               "mean_ev": round(mean, 2), "cvar95": round(cvar, 2),
               "var95": ra.get("var95"), "raev": round(raev, 2),
               "wacc": det.get("wacc_used"), "tier": tier}
    if tier == "full":
        paths = base["risk_adjusted"].get("_paths") or []
        if target_ev is not None and paths:
            metrics["p_target"] = round(sum(1 for e in paths if e > target_ev) / len(paths), 4)
        try:
            ro = V.real_options_suite(work)
            metrics["real_option_value"] = round(ro.get("total_flexibility_value", 0.0), 2)
        except Exception:
            metrics["real_option_value"] = None
        try:
            st = V.stress(work, mode, assumptions)
            # breakeven_radius is None when the valuation is resilient across the
            # whole tested ambiguity range — resilient_beyond then carries the reach.
            metrics["dro_breakeven_radius"] = st.get("breakeven_radius")
            metrics["dro_resilient_beyond"] = st.get("resilient_beyond")
        except Exception:
            metrics["dro_breakeven_radius"] = None
    return metrics


def _eval_cached(db, company_id, dsver, data, moves, tier, target_ev=None, lam=LAMBDA):
    h = _seq_hash(moves)
    if tier == "cheap":   # cheap results are cache-safe by key; full depends on target_ev(=stable per dsver)
        row = db.query(TrajectoryCache).filter_by(
            company_id=company_id, dataset_version=dsver, seq_hash=h, tier=tier).first()
        if row:
            return row.metrics
    m = evaluate_trajectory(data, moves, tier, target_ev=target_ev, lam=lam)
    row = db.query(TrajectoryCache).filter_by(
        company_id=company_id, dataset_version=dsver, seq_hash=h, tier=tier).first()
    if row:
        row.metrics = m
    else:
        db.add(TrajectoryCache(company_id=company_id, dataset_version=dsver,
                               seq_hash=h, tier=tier, metrics=m))
    return m


# ======================================================================
# decision search — bounded beam over the distinct-atom set lattice
# ======================================================================
def _compatible(existing_atoms, move):
    atom = move["atom_type"]
    if atom in existing_atoms:                       # one move per atom type
        return False
    params = move.get("params") or {}
    for ex in params.get("excludes", []):
        if ex in existing_atoms:
            return False
    for pre in params.get("prereqs", []):
        if pre not in existing_atoms:
            return False
    return True


def _search(db, company_id, dsver, data, moves, lam, progress=None):
    """Cheap-screen a bounded beam, then full-evaluate survivors + do-nothing."""
    cheap_count = 0
    evaluated = {}          # frozenset(move idx) -> (moveset, cheap_metrics)

    def cheap(moveset):
        nonlocal cheap_count
        if cheap_count >= CHEAP_SCREEN_CAP:
            return None
        cheap_count += 1
        return _eval_cached(db, company_id, dsver, data, moveset, "cheap", lam=lam)

    # tier 1: singles
    singles = []
    for i, mv in enumerate(moves):
        m = cheap([mv])
        if m is None:
            break
        evaluated[frozenset([i])] = ([mv], m)
        singles.append((frozenset([i]), [mv], m))
    beam = sorted(singles, key=lambda t: t[2]["raev"], reverse=True)[:BEAM_WIDTH]
    if progress:
        progress(35, f"screened {cheap_count} single moves")

    # tiers 2..MAX_MOVES: extend the beam
    for depth in range(2, MAX_MOVES + 1):
        nxt = []
        for idxset, moveset, _ in beam:
            atoms = {moves[i]["atom_type"] for i in idxset}
            for j, mv in enumerate(moves):
                if j in idxset or not _compatible(atoms, mv):
                    continue
                newset = idxset | {j}
                if newset in evaluated:
                    continue
                combo = moveset + [mv]
                m = cheap(combo)
                if m is None:
                    break
                evaluated[newset] = (combo, m)
                nxt.append((newset, combo, m))
            if cheap_count >= CHEAP_SCREEN_CAP:
                break
        if not nxt:
            break
        beam = sorted(nxt, key=lambda t: t[2]["raev"], reverse=True)[:BEAM_WIDTH]
        if progress:
            progress(35 + depth * 10, f"screened depth-{depth} ({cheap_count} nodes)")

    # full tier: top survivors by cheap raev + the do-nothing baseline
    ranked = sorted(evaluated.values(), key=lambda t: t[1]["raev"], reverse=True)
    survivors = [ms for ms, _ in ranked[:FULL_SURVIVORS]]
    if progress:
        progress(75, f"full-evaluating {len(survivors)} survivors + baseline")

    do_nothing = _eval_cached(db, company_id, dsver, data, [], "full", lam=lam)
    cur_mean = do_nothing["mean_ev"]
    # recompute do-nothing p_target vs its own mean = P(EV > current mean)
    do_nothing_full = evaluate_trajectory(data, [], "full", target_ev=cur_mean, lam=lam)
    full_results = [([], do_nothing_full)]
    for ms in survivors:
        fm = _eval_cached(db, company_id, dsver, data, ms, "full", target_ev=cur_mean, lam=lam)
        full_results.append((ms, fm))
    if progress:
        progress(92, "assembling frontier")
    return evaluated, full_results, do_nothing_full, cheap_count


def _pareto(points):
    """Pareto-optimal indices maximizing (mean_ev, cvar95)."""
    keep = []
    for i, (_, a) in enumerate(points):
        dominated = False
        for j, (_, b) in enumerate(points):
            if j != i and b["mean_ev"] >= a["mean_ev"] and b["cvar95"] >= a["cvar95"] \
               and (b["mean_ev"] > a["mean_ev"] or b["cvar95"] > a["cvar95"]):
                dominated = True
                break
        if not dominated:
            keep.append(i)
    return keep


def _move_view(m):
    return {"atom_type": m["atom_type"], "label": m.get("label"),
            "magnitude": m["magnitude"], "start_year": m.get("start_year")}


def build_frontier(db, company_id, progress=None):
    """Compute the Strategic Decision Frontier for a company. Returns the JSON."""
    t0 = _time.monotonic()
    ds = _active_company_dataset(db, company_id)
    if not ds or not isinstance(ds.data, dict):
        raise HTTPException(409, "No active dataset for this company.")
    dsver = ds.version
    moves = [_move_to_dict(m) for m in db.query(StrategicMove)
             .filter_by(company_id=company_id, enabled=True).order_by(StrategicMove.id).all()]
    sig = library_signature(moves)
    if progress:
        progress(20, f"{len(moves)} moves in library")
    evaluated, full_results, do_nothing, cheap_count = _search(
        db, company_id, dsver, ds.data, moves, LAMBDA, progress)

    # rank full trajectories by raev; optimal = best; do-nothing = baseline
    full_sorted = sorted(full_results, key=lambda t: t[1]["raev"], reverse=True)
    optimal_ms, optimal = full_sorted[0]
    dn_raev = do_nothing["raev"]
    n_full = len(full_results)
    below = sum(1 for _, m in full_results if m["raev"] <= dn_raev)
    current_percentile = round(100.0 * below / n_full, 1) if n_full else None
    pareto_idx = _pareto(full_results)
    trajectories_evaluated = len(evaluated) + 1     # + do-nothing baseline

    frontier = {
        "lambda": LAMBDA,
        "dataset_version": dsver,
        "library_signature": sig,
        "trajectories_evaluated": trajectories_evaluated,
        "cheap_screened": cheap_count,
        "full_evaluated": n_full,
        "current_plan": {"ev": do_nothing["ev"], "mean_ev": do_nothing["mean_ev"],
                         "cvar95": do_nothing["cvar95"], "raev": do_nothing["raev"],
                         "p_target": do_nothing.get("p_target")},
        "current_strategy_percentile": current_percentile,
        "optimal_sequence": {
            "moves": [_move_view(m) for m in sorted(optimal_ms, key=lambda x: ATOM_TYPES.index(x["atom_type"]))],
            "ev": optimal["ev"], "mean_ev": optimal["mean_ev"], "cvar95": optimal["cvar95"],
            "raev": optimal["raev"], "p_target": optimal.get("p_target"),
            "real_option_value": optimal.get("real_option_value"),
            "dro_breakeven_radius": optimal.get("dro_breakeven_radius"),
            "delta_ev": round(optimal["ev"] - do_nothing["ev"], 2),
            "strategic_regret": round(optimal["raev"] - dn_raev, 2)},
        "target_definition": "P(trajectory EV > current-plan mean EV); user-overridable target is a future field",
        "frontier_points": [
            {"moves": [_move_view(m) for m in ms], "mean_ev": mm["mean_ev"],
             "cvar95": mm["cvar95"], "raev": mm["raev"],
             "delta_ev": round(mm["ev"] - do_nothing["ev"], 2)}
            for i, (ms, mm) in enumerate(full_results) if i in pareto_idx],
    }
    wall = round(_time.monotonic() - t0, 2)
    node_cost = {"cheap_nodes": cheap_count, "full_nodes": n_full, "wall_s": wall}
    # persist
    row = db.query(DecisionFrontier).filter_by(
        company_id=company_id, dataset_version=dsver, library_signature=sig).first()
    if row:
        row.frontier = frontier; row.trajectories_evaluated = trajectories_evaluated
        row.lambda_ = LAMBDA; row.node_cost = node_cost; row.built_at = datetime.utcnow()
    else:
        row = DecisionFrontier(company_id=company_id, dataset_version=dsver,
                               library_signature=sig, lambda_=LAMBDA, frontier=frontier,
                               trajectories_evaluated=trajectories_evaluated,
                               node_cost=node_cost)
        db.add(row)
    db.flush()
    _build_policy_surface(db, company_id, dsver, ds.data, moves)
    db.commit()
    frontier["node_cost"] = node_cost
    frontier["frontier_id"] = row.id
    return frontier, row.id


def _build_policy_surface(db, company_id, dsver, data, moves):
    """Per-move magnitude->ΔEV response curves (cheap) + the growth/leverage DP
    slice — so the Trajectory Room interpolates, never runs live MC."""
    base = evaluate_trajectory(data, [], "cheap")
    base_ev = base["ev"]
    curves = {}
    for atom in ATOM_TYPES:
        mags = sorted({m["magnitude"] for m in moves if m["atom_type"] == atom})
        if not mags:
            continue
        pts = []
        for mg in mags:
            mv = {"atom_type": atom, "magnitude": mg, "start_year": None, "params": {}}
            em = evaluate_trajectory(data, [mv], "cheap")
            pts.append({"magnitude": mg, "delta_ev": round(em["ev"] - base_ev, 2),
                        "cvar95": em["cvar95"]})
        curves[atom] = pts
    dp_slice = None
    try:
        dp = intel.dp_optimize(data)
        dp_slice = {"policy_slice_at_d0": dp.get("policy_slice_at_d0"),
                    "equity_value_optimal": dp.get("equity_value_optimal"),
                    "optimization_uplift": dp.get("optimization_uplift")}
    except Exception:
        dp_slice = None
    surface = {"base_ev": base_ev, "response_curves": curves,
               "growth_leverage_dp": dp_slice}
    row = db.query(DPPolicySurface).filter_by(company_id=company_id, dataset_version=dsver).first()
    if row:
        row.surface = surface; row.built_at = datetime.utcnow()
    else:
        db.add(DPPolicySurface(company_id=company_id, dataset_version=dsver, surface=surface))


# ======================================================================
# move library helpers
# ======================================================================
def _move_to_dict(m):
    return {"id": m.id, "atom_type": m.atom_type, "label": m.label,
            "magnitude": m.magnitude, "start_year": m.start_year,
            "params": m.params or {}, "source": m.source, "enabled": m.enabled}


def library_signature(moves):
    key = sorted([(m["atom_type"], round(float(m["magnitude"]), 6), m.get("start_year"),
                   json.dumps(m.get("params") or {}, sort_keys=True))
                  for m in moves if m.get("enabled", True)])
    return hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:32]


def _ensure_seeded(db, company_id, actor_id=None):
    if db.query(StrategicMove).filter_by(company_id=company_id).first():
        return
    for atom, label, mag in DEFAULT_TEMPLATES:
        db.add(StrategicMove(company_id=company_id, atom_type=atom, label=label,
                             magnitude=mag, source="template", enabled=True,
                             created_by=actor_id))
    db.commit()


# ======================================================================
# API
# ======================================================================
class MoveIn(BaseModel):
    atom_type: str
    label: str = ""
    magnitude: float
    start_year: int | None = None
    params: dict = Field(default_factory=dict)
    enabled: bool = True


class EntityIntakeIn(BaseModel):
    kind: str                                  # acquisition | divestiture
    label: str = ""
    close_year: int
    target_revenue: float = 0.0
    target_ebit_margin: float = 0.0            # as fraction of target_revenue
    target_capex_pct: float = 0.0
    target_nwc_pct: float = 0.0
    price: float = 0.0                          # cash outflow (acq) / proceeds (div)
    acquired_debt: float = 0.0
    funding_debt_pct: float = 0.0              # share of price funded by new debt


@decision_router.get("/companies/{company_id}/moves")
def list_moves(company_id: int, member=Depends(require_company_member), db=Depends(get_db)):
    _ensure_seeded(db, company_id)
    rows = db.query(StrategicMove).filter_by(company_id=company_id).order_by(StrategicMove.id).all()
    return {"moves": [_move_to_dict(m) for m in rows], "atom_types": list(ATOM_TYPES)}


@decision_router.post("/companies/{company_id}/moves", status_code=201)
def create_move(company_id: int, body: MoveIn, member=Depends(require_company_admin),
                user=Depends(get_current_user), db=Depends(get_db)):
    if body.atom_type not in ATOM_TYPES:
        raise HTTPException(422, f"atom_type must be one of {list(ATOM_TYPES)}")
    m = StrategicMove(company_id=company_id, atom_type=body.atom_type,
                      label=body.label or body.atom_type, magnitude=body.magnitude,
                      start_year=body.start_year, params=body.params, source="user",
                      enabled=body.enabled, created_by=user.id)
    db.add(m); audit(db, user.id, "strategic_move_created", "company", company_id, detail=body.atom_type)
    db.commit(); db.refresh(m)
    return _move_to_dict(m)


@decision_router.put("/companies/{company_id}/moves/{move_id}")
def update_move(company_id: int, move_id: int, body: MoveIn,
                member=Depends(require_company_admin), user=Depends(get_current_user), db=Depends(get_db)):
    m = db.get(StrategicMove, move_id)
    if not m or m.company_id != company_id:
        raise HTTPException(404, "Move not found")
    m.atom_type, m.label, m.magnitude = body.atom_type, body.label or m.label, body.magnitude
    m.start_year, m.params, m.enabled = body.start_year, body.params, body.enabled
    audit(db, user.id, "strategic_move_updated", "company", company_id, detail=str(move_id))
    db.commit()
    return _move_to_dict(m)


@decision_router.delete("/companies/{company_id}/moves/{move_id}")
def delete_move(company_id: int, move_id: int, member=Depends(require_company_admin),
                user=Depends(get_current_user), db=Depends(get_db)):
    m = db.get(StrategicMove, move_id)
    if not m or m.company_id != company_id:
        raise HTTPException(404, "Move not found")
    db.delete(m); audit(db, user.id, "strategic_move_deleted", "company", company_id, detail=str(move_id))
    db.commit()
    return {"ok": True, "deleted": move_id}


@decision_router.post("/companies/{company_id}/moves/entity", status_code=201)
def entity_intake(company_id: int, body: EntityIntakeIn, member=Depends(require_company_admin),
                  user=Depends(get_current_user), db=Depends(get_db)):
    """Compile an acquisition/divestiture mini-intake into a lattice-consumable
    entity move (additive per-year cell deltas across post-close forecast years)."""
    if body.kind not in ("acquisition", "divestiture"):
        raise HTTPException(422, "kind must be 'acquisition' or 'divestiture'")
    ds = _active_company_dataset(db, company_id)
    if not ds or not isinstance(ds.data, dict):
        raise HTTPException(409, "No active dataset for this company.")
    fyears = [int(y) for y in ds.data["periods"].get("forecast", [])]
    post = [y for y in fyears if y >= body.close_year]
    if not post:
        raise HTTPException(422, "close_year is outside the forecast horizon")
    sign = 1.0 if body.kind == "acquisition" else -1.0
    rev = body.target_revenue * sign
    ebit = body.target_revenue * body.target_ebit_margin * sign
    # cost block that reproduces the stated EBIT margin: nonebit = rev - ebit - da(assume 0 extra)
    nonebit = rev - ebit
    capex = body.target_revenue * body.target_capex_pct * sign
    nwc = body.target_revenue * body.target_nwc_pct * sign
    cell = {"income_statement": {"revenue": {}, "cogs": {}, "opex": {}},
            "cash_flow": {"capex": {}}, "balance_sheet": {"other_current_assets": {},
            "short_term_debt": {}, "long_term_debt": {}, "cash": {}, "noncurrent_assets": {}}}
    for y in post:
        cell["income_statement"]["revenue"][str(y)] = rev
        cell["income_statement"]["cogs"][str(y)] = nonebit * 0.7
        cell["income_statement"]["opex"][str(y)] = nonebit * 0.3
        cell["cash_flow"]["capex"][str(y)] = capex
        cell["balance_sheet"]["other_current_assets"][str(y)] = nwc
    # financing + one-time price land in the close year
    cy = str(body.close_year)
    cell["balance_sheet"]["long_term_debt"][cy] = (body.acquired_debt + body.price * body.funding_debt_pct) * sign
    cell["balance_sheet"]["cash"][cy] = (-body.price + body.price * body.funding_debt_pct) * sign
    cell["balance_sheet"]["noncurrent_assets"][cy] = body.price * sign
    m = StrategicMove(company_id=company_id, atom_type="entity",
                      label=body.label or f"{body.kind.title()} @ {body.close_year}",
                      magnitude=1.0, start_year=body.close_year,
                      params={"cell_deltas": cell, "kind": body.kind}, source="entity",
                      enabled=True, created_by=user.id)
    db.add(m); audit(db, user.id, "entity_move_compiled", "company", company_id, detail=body.kind)
    db.commit(); db.refresh(m)
    return _move_to_dict(m)


@decision_router.get("/companies/{company_id}/frontier")
def get_frontier(company_id: int, member=Depends(require_company_member), db=Depends(get_db)):
    """Instant, cached latest frontier. 404 if not computed yet (nightly or POST search)."""
    _ensure_seeded(db, company_id)
    ds = _active_company_dataset(db, company_id)
    if not ds:
        raise HTTPException(409, "No active dataset for this company.")
    moves = [_move_to_dict(m) for m in db.query(StrategicMove)
             .filter_by(company_id=company_id, enabled=True).all()]
    sig = library_signature(moves)
    row = db.query(DecisionFrontier).filter_by(
        company_id=company_id, dataset_version=ds.version, library_signature=sig).first()
    if not row:
        raise HTTPException(404, "No current frontier — run a search (POST .../frontier/search).")
    out = dict(row.frontier); out["frontier_id"] = row.id; out["built_at"] = row.built_at
    out["node_cost"] = row.node_cost; out["cached"] = True
    return out


@decision_router.get("/companies/{company_id}/frontier/policy-surface")
def get_policy_surface(company_id: int, member=Depends(require_company_member), db=Depends(get_db)):
    ds = _active_company_dataset(db, company_id)
    if not ds:
        raise HTTPException(409, "No active dataset for this company.")
    row = db.query(DPPolicySurface).filter_by(company_id=company_id, dataset_version=ds.version).first()
    if not row:
        raise HTTPException(404, "No policy surface — run a search first.")
    return {"dataset_version": ds.version, "surface": row.surface, "built_at": row.built_at}


def _run_job(job_id, company_id):
    db = A.SessionLocal()
    try:
        job = db.get(FrontierJob, job_id)
        job.status = "running"; job.updated_at = datetime.utcnow(); db.commit()
        def prog(pct, phase):
            job.progress = int(pct); job.phase = phase[:40]; job.updated_at = datetime.utcnow(); db.commit()
        _, fid = build_frontier(db, company_id, progress=prog)
        job.status = "done"; job.progress = 100; job.phase = "complete"
        job.result_frontier_id = fid; job.updated_at = datetime.utcnow(); db.commit()
    except Exception as e:
        try:
            job = db.get(FrontierJob, job_id)
            job.status = "error"; job.error = str(e)[:500]; job.updated_at = datetime.utcnow(); db.commit()
        except Exception:
            pass
    finally:
        db.close()


@decision_router.post("/companies/{company_id}/frontier/search", status_code=202)
def start_search(company_id: int, member=Depends(require_company_member),
                 user=Depends(get_current_user), db=Depends(get_db)):
    """Bounded re-search (30-90s). Returns a job to poll. Any member may trigger."""
    _ensure_seeded(db, company_id)
    job = FrontierJob(company_id=company_id, status="queued", created_by=user.id)
    db.add(job); db.commit(); db.refresh(job)
    threading.Thread(target=_run_job, args=(job.id, company_id),
                     name=f"frontier-{company_id}", daemon=True).start()
    return {"job_id": job.id, "status": "queued", "poll": f"/companies/{company_id}/frontier/search/{job.id}"}


@decision_router.get("/companies/{company_id}/frontier/search/{job_id}")
def poll_search(company_id: int, job_id: int, member=Depends(require_company_member), db=Depends(get_db)):
    job = db.get(FrontierJob, job_id)
    if not job or job.company_id != company_id:
        raise HTTPException(404, "Job not found")
    return {"job_id": job.id, "status": job.status, "progress": job.progress,
            "phase": job.phase, "frontier_id": job.result_frontier_id, "error": job.error}


# ======================================================================
# nightly recompute + single-flight guard + protected endpoint
# ======================================================================
def _acquire_nightly_lock(db):
    row = db.query(NightlyLock).filter_by(id=1).first()
    if not row:
        row = NightlyLock(id=1, running=False); db.add(row); db.commit()
    stale = row.started_at and row.started_at < datetime.utcnow() - timedelta(hours=2)
    if row.running and not stale:
        return False
    row.running = True; row.started_at = datetime.utcnow(); db.commit()
    return True


def _release_nightly_lock(db):
    row = db.query(NightlyLock).filter_by(id=1).first()
    if row:
        row.running = False; row.last_completed_at = datetime.utcnow(); db.commit()


def recompute_all_frontiers(only_stale=True):
    """Sweep every company; skip when (dataset_version, library signature) unchanged."""
    from .modules.enterprise_state.models import Enterprise
    db = A.SessionLocal()
    summary = {"considered": 0, "recomputed": 0, "skipped": 0, "errors": 0}
    if not _acquire_nightly_lock(db):
        db.close()
        return {"skipped_reason": "another replica holds the nightly lock"}
    try:
        cids = [e.id for e in db.query(Enterprise).all()]
        for cid in cids:
            summary["considered"] += 1
            try:
                ds = _active_company_dataset(db, cid)
                if not ds or not isinstance(ds.data, dict):
                    summary["skipped"] += 1; continue
                _ensure_seeded(db, cid)
                moves = [_move_to_dict(m) for m in db.query(StrategicMove)
                         .filter_by(company_id=cid, enabled=True).all()]
                sig = library_signature(moves)
                frontier_current = bool(db.query(DecisionFrontier).filter_by(
                    company_id=cid, dataset_version=ds.version, library_signature=sig).first())
                viab_current = True
                if SENTINEL_NIGHTLY:                       # one lock, one sweep — 7i folds in here
                    from . import sentinel
                    viab_current = sentinel.viability_current(db, cid, ds.version, sig)
                if only_stale and frontier_current and viab_current:
                    summary["skipped"] += 1; continue
                if not frontier_current:
                    build_frontier(db, cid)               # sentinel needs a frontier for the radar headline
                if SENTINEL_NIGHTLY and not viab_current:
                    from . import sentinel
                    sentinel.sentinel_recompute(db, cid, do_frontier=False)
                summary["recomputed"] += 1
            except Exception:
                summary["errors"] += 1
    finally:
        _release_nightly_lock(db)
        db.close()
    return summary


def _nightly_loop():
    while True:
        try:
            recompute_all_frontiers(only_stale=True)
        except Exception:
            pass
        _time.sleep(NIGHTLY_PERIOD_S)


def spawn_nightly():
    # one daemon for BOTH families (decision frontier + 7i sentinel)
    if NIGHTLY_ENABLED or SENTINEL_NIGHTLY:
        threading.Thread(target=_nightly_loop, name="prescience-nightly", daemon=True).start()


def _spawn_recompute(company_id):
    """On-upload trigger: recompute the affected company's frontier + viability in
    the background (frontier is ~10s, so never inline). Always runs, env-independent."""
    def _run():
        db = A.SessionLocal()
        try:
            from . import sentinel
            sentinel.sentinel_recompute(db, company_id, do_frontier=True)
        except Exception:
            pass
        finally:
            db.close()
    threading.Thread(target=_run, name=f"upload-recompute-{company_id}", daemon=True).start()


@decision_router.post("/internal/frontier/recompute")
def internal_recompute(only_stale: bool = True, authorization: str = Header(None), db=Depends(get_db)):
    """Protected recompute trigger for an external cron. Requires the admin token."""
    from .core.config import admin_token
    tok = admin_token()
    if not tok or authorization != f"Bearer {tok}":
        raise HTTPException(403, "admin token required")
    return recompute_all_frontiers(only_stale=only_stale)
