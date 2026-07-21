"""AXIOM PLANNING — self-defined KPIs (Phase 7L, thread f).

The long-pending structured KPI feature, scoped to v1: a KPI is either a FORMULA
over named statement lines (simple arithmetic — + - * / and parentheses, NO
function calls or names beyond the whitelisted lines/aggregates) or a MANUAL
entry series. Each carries a target and a direction; tracking computes the value
per period and the variance vs target (absolute, %, and direction-aware
favorable/unfavorable). No formula language beyond arithmetic — that is a later
phase.

Named lines available to formulas: the canonical statement keys plus the computed
aggregates gross_profit, ebit, ebitda, total_assets, total_debt, net_debt, nwc.
"""
import ast
import operator
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON

from . import accounts as A
from .accounts import (Base, get_db, require_company_member, require_company_admin,
                       get_current_user, audit, _active_company_dataset)
from .modules.financials import engines as fin

_log = logging.getLogger("axiom.planning")

DIRECTIONS = ("higher_better", "lower_better")
KINDS = ("formula", "manual")
UNITS = ("ratio", "percent", "currency", "days", "count", "x")


# ======================================================================
# models
# ======================================================================
class KpiDefinition(Base):
    __tablename__ = "ax_kpi_definitions"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    name = Column(String(120), nullable=False)
    kind = Column(String(16), nullable=False)              # formula | manual
    formula = Column(Text, nullable=True)                  # formula kind only
    target = Column(Float, nullable=True)
    direction = Column(String(16), nullable=False, default="higher_better")
    unit = Column(String(16), nullable=False, default="ratio")
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class KpiValue(Base):
    __tablename__ = "ax_kpi_values"
    id = Column(Integer, primary_key=True)
    kpi_id = Column(Integer, index=True, nullable=False)
    company_id = Column(Integer, index=True, nullable=False)
    period = Column(Integer, nullable=False)
    value = Column(Float, nullable=False)
    source = Column(String(16), nullable=False, default="manual")  # manual | computed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ======================================================================
# safe arithmetic evaluator over named statement lines
# ======================================================================
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.USub: operator.neg, ast.UAdd: operator.pos}

_STATEMENT_KEYS = set(fin.IS_KEYS) | set(fin.BS_KEYS) | set(fin.CF_KEYS)
_AGGREGATES = {"gross_profit", "ebit", "ebitda", "total_assets", "total_debt",
               "net_debt", "nwc"}
ALLOWED_NAMES = sorted(_STATEMENT_KEYS | _AGGREGATES)


def _line_values(data, year):
    """Named line values (+ computed aggregates) for one period year."""
    ys = str(year)
    IS = data["income_statement"]; BS = data["balance_sheet"]; CF = data["cash_flow"]
    v = {}
    for k in fin.IS_KEYS: v[k] = IS.get(k, {}).get(ys)
    for k in fin.BS_KEYS: v[k] = BS.get(k, {}).get(ys)
    for k in fin.CF_KEYS: v[k] = CF.get(k, {}).get(ys)
    def g(k): return v.get(k) or 0.0
    v["gross_profit"] = g("revenue") - g("cogs")
    v["ebit"] = g("revenue") - g("cogs") - g("opex") - g("depreciation_amortization")
    v["ebitda"] = v["ebit"] + g("depreciation_amortization")
    v["total_assets"] = g("cash") + g("other_current_assets") + g("noncurrent_assets")
    v["total_debt"] = g("short_term_debt") + g("long_term_debt")
    v["net_debt"] = v["total_debt"] - g("cash")
    v["nwc"] = g("other_current_assets") - g("current_liabilities_ex_debt")
    return v


def validate_formula(formula):
    """Parse + whitelist. Returns the sorted set of referenced names. Raises 422
    with a plain message on anything outside simple arithmetic over named lines."""
    try:
        tree = ast.parse(formula, mode="eval")
    except SyntaxError as e:
        raise HTTPException(422, f"Formula is not valid arithmetic: {e.msg}.")
    names = set()

    def check(node):
        if isinstance(node, ast.Expression):
            return check(node.body)
        if isinstance(node, ast.BinOp):
            if type(node.op) not in _OPS:
                raise HTTPException(422, "Only + - * / are allowed in a KPI formula.")
            check(node.left); check(node.right); return
        if isinstance(node, ast.UnaryOp):
            if type(node.op) not in _OPS:
                raise HTTPException(422, "Only unary + and - are allowed.")
            check(node.operand); return
        if isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float)):
                raise HTTPException(422, "Only numeric constants are allowed.")
            return
        if isinstance(node, ast.Name):
            if node.id not in _STATEMENT_KEYS and node.id not in _AGGREGATES:
                raise HTTPException(422, f"Unknown line '{node.id}'. Allowed lines: "
                                         f"{', '.join(ALLOWED_NAMES)}.")
            names.add(node.id); return
        raise HTTPException(422, "A KPI formula may only use named lines, numbers, "
                                 "parentheses, and + - * /.")
    check(tree)
    if not names:
        raise HTTPException(422, "A formula must reference at least one statement line.")
    return sorted(names)


def _eval(formula, values):
    tree = ast.parse(formula, mode="eval").body

    def ev(node):
        if isinstance(node, ast.BinOp):
            a, b = ev(node.left), ev(node.right)
            if a is None or b is None:
                return None
            if isinstance(node.op, ast.Div) and b == 0:
                return None
            return _OPS[type(node.op)](a, b)
        if isinstance(node, ast.UnaryOp):
            a = ev(node.operand)
            return None if a is None else _OPS[type(node.op)](a)
        if isinstance(node, ast.Constant):
            return float(node.value)
        if isinstance(node, ast.Name):
            return values.get(node.id)
        return None
    return ev(tree)


# ======================================================================
# tracking + variance
# ======================================================================
def _variance(value, target, direction):
    if value is None or target is None:
        return {"abs": None, "pct": None, "status": None}
    ab = value - target
    pct = (ab / abs(target)) if target else None
    if direction == "lower_better":
        favorable = value <= target
    else:
        favorable = value >= target
    return {"abs": fin._r(ab), "pct": fin._r(pct) if pct is not None else None,
            "status": "favorable" if favorable else "unfavorable"}


def kpi_series(db, company_id, kpi):
    """Per-period values for a KPI + variance vs target on the latest period."""
    ds = _active_company_dataset(db, company_id)
    periods = []
    if ds and isinstance(ds.data, dict):
        p = ds.data.get("periods", {})
        periods = list(p.get("historical", [])) + list(p.get("forecast", []))
    series = []
    if kpi.kind == "formula" and ds:
        for y in periods:
            val = _eval(kpi.formula, _line_values(ds.data, y))
            series.append({"period": y, "value": fin._r(val) if val is not None else None})
    else:                                             # manual
        for row in (db.query(KpiValue).filter_by(kpi_id=kpi.id)
                    .order_by(KpiValue.period).all()):
            series.append({"period": row.period, "value": fin._r(row.value)})
    latest = next((s["value"] for s in reversed(series) if s["value"] is not None), None)
    return series, _variance(latest, kpi.target, kpi.direction), latest


def _kpi_out(db, company_id, kpi):
    series, var, latest = kpi_series(db, company_id, kpi)
    return {"kpi_id": kpi.id, "name": kpi.name, "kind": kpi.kind, "formula": kpi.formula,
            "target": kpi.target, "direction": kpi.direction, "unit": kpi.unit,
            "current_value": latest, "variance": var, "series": series}


# ======================================================================
# API
# ======================================================================
planning_router = APIRouter(tags=["planning-kpi"])


class KpiIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    kind: str = "formula"
    formula: str | None = None
    target: float | None = None
    direction: str = "higher_better"
    unit: str = "ratio"


class KpiValueIn(BaseModel):
    period: int
    value: float


@planning_router.get("/companies/{company_id}/kpis")
def list_kpis(company_id: int, member=Depends(require_company_member), db=Depends(get_db)):
    rows = db.query(KpiDefinition).filter_by(company_id=company_id).order_by(KpiDefinition.id).all()
    return {"company_id": company_id, "allowed_lines": ALLOWED_NAMES,
            "kpis": [_kpi_out(db, company_id, k) for k in rows]}


@planning_router.post("/companies/{company_id}/kpis", status_code=201)
def create_kpi(company_id: int, body: KpiIn, member=Depends(require_company_admin),
               user=Depends(get_current_user), db=Depends(get_db)):
    if body.kind not in KINDS:
        raise HTTPException(422, "kind must be 'formula' or 'manual'")
    if body.direction not in DIRECTIONS:
        raise HTTPException(422, "direction must be 'higher_better' or 'lower_better'")
    if body.kind == "formula":
        if not body.formula:
            raise HTTPException(422, "a formula KPI requires a formula")
        validate_formula(body.formula)                # 422 with plain message if invalid
    kpi = KpiDefinition(company_id=company_id, name=body.name.strip(), kind=body.kind,
                        formula=(body.formula or None), target=body.target,
                        direction=body.direction, unit=body.unit, created_by=user.id)
    db.add(kpi); db.flush()
    audit(db, user.id, "kpi_created", "company", company_id, detail=kpi.name)
    db.commit()
    return _kpi_out(db, company_id, kpi)


@planning_router.put("/companies/{company_id}/kpis/{kpi_id}")
def update_kpi(company_id: int, kpi_id: int, body: KpiIn,
               member=Depends(require_company_admin), db=Depends(get_db)):
    kpi = db.query(KpiDefinition).filter_by(id=kpi_id, company_id=company_id).first()
    if not kpi:
        raise HTTPException(404, "KPI not found")
    if body.kind == "formula" and body.formula:
        validate_formula(body.formula)
    kpi.name, kpi.kind, kpi.formula = body.name.strip(), body.kind, (body.formula or None)
    kpi.target, kpi.direction, kpi.unit = body.target, body.direction, body.unit
    db.commit()
    return _kpi_out(db, company_id, kpi)


@planning_router.delete("/companies/{company_id}/kpis/{kpi_id}")
def delete_kpi(company_id: int, kpi_id: int, member=Depends(require_company_admin),
               db=Depends(get_db)):
    kpi = db.query(KpiDefinition).filter_by(id=kpi_id, company_id=company_id).first()
    if not kpi:
        raise HTTPException(404, "KPI not found")
    db.query(KpiValue).filter_by(kpi_id=kpi_id).delete()
    db.delete(kpi); db.commit()
    return {"deleted": True, "kpi_id": kpi_id}


@planning_router.post("/companies/{company_id}/kpis/{kpi_id}/values", status_code=201)
def set_manual_value(company_id: int, kpi_id: int, body: KpiValueIn,
                     member=Depends(require_company_admin), db=Depends(get_db)):
    kpi = db.query(KpiDefinition).filter_by(id=kpi_id, company_id=company_id).first()
    if not kpi:
        raise HTTPException(404, "KPI not found")
    if kpi.kind != "manual":
        raise HTTPException(422, "values can only be set on a manual KPI")
    row = db.query(KpiValue).filter_by(kpi_id=kpi_id, period=body.period).first()
    if row:
        row.value = body.value
    else:
        db.add(KpiValue(kpi_id=kpi_id, company_id=company_id, period=body.period,
                        value=body.value, source="manual"))
    db.commit()
    return _kpi_out(db, company_id, kpi)
