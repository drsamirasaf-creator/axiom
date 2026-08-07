"""Financial Core routes — Data Input tab + Executive Dashboard metrics
(SPEC-004 Product §5, §6.14, §7; ADR-005). REQ-FIN-009..014.
"""
from fastapi import (APIRouter, Depends, Header, HTTPException, UploadFile,
                     File, Form, Response)
from sqlalchemy.orm import Session
from ...response_schemas import (DatasetProfileOut)  # noqa: E402
from ...core.db import get_db
from . import engines, models, schemas, templates

router = APIRouter(prefix="/api/v1/financials", tags=["financials"])
metrics_router = APIRouter(prefix="/api/v1/metrics", tags=["dashboard"])

MAX_UPLOAD = 5 * 1024 * 1024
XLSX_MIME = ("application/vnd.openxmlformats-officedocument"
             ".spreadsheetml.sheet")


# ADR-007: tenancy via session when authenticated; the legacy header
# path stays until AXIOM_REQUIRE_AUTH is flipped (then 401).
from ..identity.deps import read_tenant as _tenant  # noqa: E402
from ..identity.deps import write_tenant as _writer  # noqa: E402
from ..identity.deps import is_authenticated as _authed  # noqa: E402
from ..identity.deps import viewer_company as _scoped  # noqa: E402
from .periods import (forecast_periods as _fc_periods, frequency_of as _freq_of,
                      period_span as _period_span, advance as _advance)


def _statement_totals(A, co_rev, co_cogs, co_opex):
    """The total row for every column, TAKEN FROM THE STATEMENT.

    ⭐⭐ NEVER THE SUM OF THE DISPLAYED ROWS. Adding up the visible lines makes
    an INCOMPLETE decomposition read as complete: the residual is exactly the
    part that is not on a line, so a summed total silently equals the covered
    part and calls it the company. This is the same reason `revenue_mix`
    divides by the statement line rather than by the detail sum — the totals
    row is what makes `Unallocated / Other` mean something rather than being a
    row a reader can ignore.

    ⭐ THE COMPANY HIERARCHY IS COMPUTED BY T2, not here. This function selects
    which level ties to which column and states the ones that cannot.
    """
    company = A.margin_hierarchy(revenue=co_rev, direct_cost=co_cogs,
                                 direct_opex=co_opex)
    gp = company["gross_profit"]
    # At company level there is no shared-versus-direct split: every operating
    # cost is inside `opex`, so `revenue - cogs - opex` IS the company's
    # operating profit, and that is the figure a fully-allocated set of lines
    # must tie to.
    ebit = company["direct_operating_profit"]
    return {
        "source": "income_statement",
        "revenue": {"value": co_rev, "ties": co_rev is not None,
                    "source": "income_statement.revenue"},
        "gross_profit": {"value": gp.get("value"), "ties": gp["available"],
                         "source": "income_statement: revenue less cogs",
                         "reason": None if gp["available"] else gp.get("unlocks")},
        # ⭐⭐ THIS COLUMN CANNOT TIE, AND SAYS SO RATHER THAN SHOWING A NUMBER.
        # Direct operating profit EXCLUDES shared cost by construction, so no
        # statement line corresponds to it: any figure here would look
        # reconciled and would not be. Stating it is the honest total.
        "direct_operating_profit": {
            "value": None, "ties": False,
            "reason": ("Direct operating profit excludes shared and corporate "
                       "cost by construction, so no income-statement line "
                       "corresponds to it. The lines below sum to less than the "
                       "company because the shared pool is not charged at this "
                       "level; it is charged one row down, in allocated EBIT.")},
        "allocated_ebit": {
            "value": ebit.get("value"), "ties": ebit["available"],
            "source": "income_statement: revenue less cogs less opex",
            "reason": None if ebit["available"] else ebit.get("unlocks")},
    }


def _constrained_mix(M, capacity_rows, period, contributions, units, pools):
    """The constrained optimum and the transport plan, for one period.

    ⭐ WIRING, NOT ANALYTICS. Every number comes from a call into `managerial`;
    this selects the rows for the period and shapes them. The AST guard covers
    this function too, so a division here would fail the build rather than
    quietly becoming a second definition of contribution per unit.
    """
    rows = [r for r in (capacity_rows or [])
            if r.get("period") is None or r.get("period") == period]
    if not rows:
        return None, None
    capacity = next((r.get("value") for r in rows
                     if r.get("measure") == "capacity_available"), None)
    consumption = {r.get("line_code"): r.get("value") for r in rows
                   if r.get("measure") == "consumption_per_unit"}
    ceilings = {r.get("line_code"): r.get("value") for r in rows
                if r.get("measure") == "maximum_sales_units"}
    steps = []
    for pool in (pools or []):
        if pool.get("period") is not None and pool.get("period") != period:
            continue
        split = M.split_pool(pool)
        if split.get("available") and split.get("step"):
            steps.append(dict(split["step"], pool=pool.get("pool")))

    lines = {}
    for code, con in (contributions or {}).items():
        if not con.get("available"):
            continue
        per_unit = M.contribution_per_constrained_unit(con.get("value"),
                                                       (units or {}).get(code))
        lines[code] = {
            "contribution_per_unit": per_unit.get("value"),
            "consumption_per_unit": consumption.get(code),
            "max_units": ceilings.get(code),
        }
    plan = M.optimise_mix(lines, capacity, steps=steps)
    if not plan.get("available"):
        return plan, None

    # ⭐⭐ THE PLAN IS OVER THE UNITS MIX, AND THE SURFACE SAYS SO. A revenue
    # mix would need price x units — a multiplication, which the AST guard
    # forbids here and which `managerial` would have to own. Units are also the
    # better object for a CAPACITY decision: what a plant reallocates is
    # production, not invoice value. The difference is stated rather than left
    # for a reader to assume.
    opt_units = plan["value"]["units"]
    from . import ratios as _r
    cur_total = sum(v for v in (units or {}).values() if v is not None)
    opt_total = sum(v for v in opt_units.values() if v is not None)
    current_mix = {c: _r.share((units or {}).get(c), cur_total)
                   for c in opt_units}
    target_mix = {c: _r.share(opt_units.get(c), opt_total) for c in opt_units}
    move = M.transport_plan(current_mix, target_mix)
    if move.get("available"):
        move["basis"] = "share of units produced, not of revenue"
    return plan, move


def _avoid(M, rows, period, code, allocated_charge):
    """The declared avoidability for one line, or None. ⭐ Wiring only."""
    a = M.avoidability(rows, allocated_charge, period, code)
    return a.get("value") if a.get("available") else None


def _company_cost(cogs, opex):
    """The statement's total operating cost. ⭐ In `managerial`, not here — the
    endpoint's AST guard forbids arithmetic and the rule survived this lane."""
    from . import managerial as _M
    return _M._sum(cogs, opex)


def _mix_shift_series(A, block, ordered):
    """Every consecutive mix shift, each labelled with the pair it spans.

    ⭐ T2 OWNS THE ARITHMETIC. This calls `mix_shift` once per pair and labels
    the result; the deltas are not recomputed here.
    """
    out = []
    for before, after in zip(ordered, ordered[1:]):
        ma = block["by_period"][before]["mix"]
        mb = block["by_period"][after]["mix"]
        if not (ma["available"] and mb["available"]):
            continue
        shift = A.mix_shift(ma["value"], mb["value"])
        out.append(dict(shift, **{"from_period": before, "to_period": after}))
    return out


# ⭐ DIRECTION IS A COMPARISON, NOT A DIFFERENCE. Saying "fell in every period"
# needs `<` on values T2 already produced; saying "fell by $24.6m" would need a
# subtraction this layer does not own. The surface therefore reports the shape
# of the movement and quotes the endpoints, and the reader does the sum they
# can already see.
_RISING, _FALLING, _MIXED, _FLAT = "rising", "falling", "mixed", "flat"


def _direction(series):
    """rising | falling | mixed | flat, from a series of values.

    ⭐⭐ ROUNDED BEFORE COMPARING, AND STRICT MONOTONICITY IS THE WRONG TEST.
    Both were defects in the first version, and both made a real series read as
    noise:

      · a gross margin held at exactly 31% arrives as 0.31, 0.3100000000000001,
        0.31 — because it is computed as (revenue − cost) / revenue — so `==`
        was false and the series reported MIXED. A margin flat to twelve
        decimal places is flat, and the trend panel's whole claim rests on
        saying so.
      · a margin of 50%, 50%, 51%, 52% is rising, but `all(b > a)` rejects it
        for the one equal pair. Direction is about never going the other way,
        not about moving at every step.

    Rounding through `round` rather than a tolerance keeps this function free of
    arithmetic, which the AST guard requires of everything on this path.
    """
    vals = [round(v, 6) for v in series if v is not None]
    if len(vals) < 2:
        return None
    pairs = list(zip(vals, vals[1:]))
    if all(b == a for a, b in pairs):
        return _FLAT
    if all(b >= a for a, b in pairs):
        return _RISING
    if all(b <= a for a, b in pairs):
        return _FALLING
    return _MIXED


def _margin_trend(block, ordered):
    """Per line: gross margin and allocated EBIT across every period, and the
    direction of each.

    ⭐⭐ THIS IS WHERE THE INSIGHT LIVES. A line whose GROSS MARGIN HOLDS while
    its ALLOCATED EBIT DETERIORATES is consuming shared cost faster than it
    earns revenue — a statement neither series can make alone, and one that a
    single period cannot make at all.
    """
    codes = []
    for p in ordered:
        for code in block["by_period"][p]["lines"]:
            if code not in codes:
                codes.append(code)
    trend = {}
    for code in codes:
        gm, eb = [], []
        for p in ordered:
            line = block["by_period"][p]["lines"].get(code) or {}
            gp = line.get("gross_profit") or {}
            ae = line.get("allocated_ebit") or {}
            gm.append(gp.get("margin") if gp.get("available") else None)
            eb.append(ae.get("value") if ae.get("available") else None)
        trend[code] = {
            "periods": list(ordered),
            "gross_margin": gm, "allocated_ebit": eb,
            "gross_margin_direction": _direction(gm),
            "allocated_ebit_direction": _direction(eb),
            # ⭐ THE DIVERGENCE, NAMED. Gross margin steady or improving while
            # allocated EBIT falls is the pattern the module exists to surface.
            "diverging": _direction(gm) in (_RISING, _FLAT)
                         and _direction(eb) == _FALLING,
        }
    return trend


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ FINDINGS — SENTENCES DERIVED FROM THE PAYLOAD, NEVER WRITTEN
# ═══════════════════════════════════════════════════════════════════════════
#
# ⭐⭐ NO TEXT IS KEYED TO ANY COMPANY. Every sentence below is a template over
# values the payload already carries, and every one is GATED on a condition
# read from that payload. A finding that cannot be derived does not render, and
# on a company where the pattern is absent this function returns an empty list
# — which is the honest output, not a failure.
#
# ⭐ THE ARITHMETIC BOUNDARY IS REAL AND IT COST A SENTENCE. "Allocated EBIT
# fell by $24.6m" needs a subtraction T2 does not own, so it is NOT said. The
# findings quote the endpoints of a series and name the direction — both of
# which already exist — and the reader can do the sum they can see.
#
# ⭐ SEVERITY ORDERS THE LIST; it is not a score. There is no multiplication of
# factors here, for the reason CORE §8a gives about priority scores.
_HEALTHY_MARGIN = 0.15          # below this the line is weak, not squeezed
_MATERIAL_TOP_1 = 0.30          # a largest line above this is worth naming
_MATERIAL_MIX_MOVE = 0.02       # a share move below this is noise


def _findings(block, names, currency_note=None):
    """Derived findings for one dimension type. May legitimately be empty."""
    out = []
    ordered = block.get("periods") or []
    if not ordered:
        return out
    first, last = ordered[0], ordered[-1]
    cur = block["by_period"][last]
    label = names.get

    # ── 1 · the reversal, and its trajectory ──────────────────────────────
    for code, tr in (block.get("trend") or {}).items():
        eb = [v for v in (tr.get("allocated_ebit") or []) if v is not None]
        gm = [v for v in (tr.get("gross_margin") or []) if v is not None]
        if not eb or not gm or eb[-1] >= 0:
            continue
        if gm[-1] <= _HEALTHY_MARGIN:
            continue                     # not a reversal — the line is simply weak
        healthy = "its gross margin is still {:.0%}".format(gm[-1])
        if tr["allocated_ebit_direction"] == _FALLING and len(eb) > 2:
            # ⭐ THE TRAJECTORY SENTENCE, and it is only available because the
            # seed carries four periods. It is gated on len(eb) > 2 so a
            # two-period dataset gets the second sentence instead of a claim
            # about a trend nobody can see.
            out.append({
                "id": f"reversal_trajectory:{code}",
                "severity": 1,
                "sentence": (
                    f"{label(code, code)} has lost allocated EBIT in every "
                    f"period since {first}, from {eb[0]:,.1f} to {eb[-1]:,.1f}, "
                    f"while {healthy}. It is not a weak product — it is a "
                    f"product being charged more for shared cost every year "
                    f"than it earns."),
                "derivation": ("allocated_ebit falls at every consecutive pair "
                               "and is negative in the latest period, while "
                               "gross margin remains above 15%"),
            })
        else:
            out.append({
                "id": f"reversal:{code}",
                "severity": 1,
                "sentence": (
                    f"{label(code, code)} looks healthy until it is charged for "
                    f"what it consumes: {healthy}, and allocated EBIT is "
                    f"{eb[-1]:,.1f}."),
                "derivation": ("gross margin above 15% with negative allocated "
                               "EBIT in the latest period"),
            })

    # ── 1b · ⭐⭐ THE §22 CORRECTIVE, AND IT OUTRANKS THE REVERSAL ITSELF ──
    # The source document forbids recommending discontinuation on fully
    # allocated EBIT alone. A line negative there and POSITIVE at contribution
    # is the case where acting on the loss makes the company worse off, so the
    # sentence that says so is severity 1 and sits beside the reversal.
    for code, cov in (cur.get("covers_variable_cost") or {}).items():
        if not cov.get("available"):
            continue
        eb = ((cur["lines"].get(code) or {}).get("allocated_ebit") or {})
        if not eb.get("available") or (eb.get("value") or 0) >= 0:
            continue
        out.append({
            "id": f"covers_variable_cost:{code}",
            "severity": 1,
            "sentence": cov["statement"],
            "derivation": ("contribution is positive while allocated EBIT is "
                           "negative — the line covers its own variable cost"),
        })

    # ── 2 · gross margin holding while allocated EBIT falls ───────────────
    for code, tr in (block.get("trend") or {}).items():
        if not tr.get("diverging"):
            continue
        if any(f["id"].endswith(f":{code}") for f in out):
            continue                     # already named by the reversal above
        # ⭐⭐ THE SENTENCE CLAIMS "ITS OWN PRICING IS NOT THE PROBLEM", SO THE
        # MARGIN MUST ACTUALLY BE HEALTHY. A line at 9% gross margin whose EBIT
        # falls is diverging by the arithmetic and NOT by the meaning — telling
        # management its pricing is fine would send them after the wrong cause.
        gm_ok = [v for v in (tr.get("gross_margin") or []) if v is not None]
        if not gm_ok or gm_ok[-1] <= _HEALTHY_MARGIN:
            continue
        out.append({
            "id": f"diverging:{code}",
            "severity": 2,
            "sentence": (
                f"The gross margin of {label(code, code)} is holding while "
                f"its allocated EBIT falls every period. The line is consuming "
                f"shared cost faster than it earns revenue; its own pricing "
                f"and direct cost are not the problem."),
            "derivation": ("gross_margin_direction is rising or flat while "
                           "allocated_ebit_direction is falling"),
        })

    # ── 3 · the mix shift, and its margin consequence ─────────────────────
    series = block.get("mix_shift_series") or []
    if series:
        span = series[-1]
        # ⭐ ROUNDED BEFORE THE THRESHOLD, for the reason `_direction` is. A
        # share that moved from 20% to 22% arrives as 0.019999999999999997 and
        # was silently dropped as immaterial by `< 0.02` — the finding vanished
        # on the exact case it was written for.
        moves = {c: round(v, 6) for c, v in (span.get("value") or {}).items()
                 if v is not None and c != A_UNALLOCATED}
        for code, move in sorted(moves.items(), key=lambda kv: -abs(kv[1])):
            if abs(move) < _MATERIAL_MIX_MOVE:
                break
            tr = (block.get("trend") or {}).get(code) or {}
            gmdir = tr.get("gross_margin_direction")
            if move > 0 and gmdir == _FALLING:
                out.append({
                    "id": f"mix_dilutive:{code}",
                    "severity": 2,
                    "sentence": (
                        f"{label(code, code)} gained {move:.1%} of revenue "
                        f"share between {span['from_period']} and "
                        f"{span['to_period']} while its gross margin fell. "
                        f"The growth is being bought, and it dilutes the "
                        f"portfolio margin as it grows."),
                    "derivation": ("mix_shift positive above 2 points with "
                                   "gross_margin_direction falling"),
                })
            elif move < 0 and gmdir == _RISING:
                out.append({
                    "id": f"mix_accretive:{code}",
                    "severity": 3,
                    "sentence": (
                        f"{label(code, code)} gave up {abs(move):.1%} of "
                        f"revenue share while improving its gross margin — the "
                        f"opposite trade, and the one that raises portfolio "
                        f"margin per unit of revenue given up."),
                    "derivation": ("mix_shift negative above 2 points with "
                                   "gross_margin_direction rising"),
                })

    # ── 4 · concentration, only where material ────────────────────────────
    conc = cur.get("concentration") or {}
    if conc.get("available"):
        v = conc["value"]
        if v.get("top_1") is not None and v["top_1"] > _MATERIAL_TOP_1:
            out.append({
                "id": "concentration",
                "severity": 3,
                "sentence": (
                    f"{v['lines_for_80pct']} of {v['n_lines']} lines carry 80% "
                    f"of revenue, and the largest alone is {v['top_1']:.0%}. "
                    f"A shock to it is a shock to the company."),
                "derivation": (f"top_1 above {_MATERIAL_TOP_1:.0%} of the "
                               f"allocated detail"),
            })

    out.sort(key=lambda f: f["severity"])
    return out


A_UNALLOCATED = "__unallocated__"


def _get_dataset(db: Session, tenant: str, dataset_id: int,
                 scoped_enterprise: int | None = None) -> models.FinancialDataset:
    row = db.get(models.FinancialDataset, dataset_id)
    if not row or row.tenant != tenant:
        raise HTTPException(status_code=404, detail="dataset not found")
    # 7a-2/7a-4: a company-scoped viewer only sees its own enterprise's data.
    if scoped_enterprise is not None and row.enterprise_id != scoped_enterprise:
        raise HTTPException(status_code=404, detail="dataset not found")
    return row


def _enforce_company_limit(db, authorization):
    """Gate creation of a NEW company analysis against the subscription seat
    count (companies_allowed). No-op when the plan flag is off."""
    from ..identity.deps import _session_user, enforce_company_limit
    user, _ = _session_user(db, authorization)
    enforce_company_limit(db, user, creating_new=True)


# ⭐ ONE `_historicals_only`, NOT TWO. This was a byte-near-identical copy of
# proforma._historicals_only, and when that one was taught to carry `frequency`
# this one was not — so `compute_plan_vs_methods` stripped the plan, lost the
# declaration, every reader defaulted to annual, and the method series came back
# keyed 20225..20232. Same defect, same day, second copy: the IMPORT-DIRECTION
# WALL (§7.42) does not apply here — proforma is importable from this module —
# so the duplicate had no justification at all.
from .proforma import _historicals_only  # noqa: E402


def _store(db, tenant, name, data, source, warnings, enterprise_id=None,
           balance=None, assumptions=None):
    """⭐ `balance` IS STORED, NOT JUST WARNED. A warning shown once at upload is
    a warning that expires; the per-period result rides on the row so every
    surface can badge the exact periods that do not balance, months later,
    without recomputing or guessing. Keyed by period because a dataset can be
    exact on its historicals and broken on its client plan — and the reverse."""
    row = models.FinancialDataset(
        tenant=tenant, enterprise_id=enterprise_id, name=name,
        standard=data["company"]["standard"],
        ownership=data["company"]["ownership"], source=source, data=data,
        validation={"warnings": warnings,
                    "balance": balance if balance is not None
                    else engines.balance_audit(data),
                    # ⭐ STORED, NOT MERELY WARNED — same reason as `balance`.
                    # A warning shown once at upload expires; the per-field
                    # result rides on the row so a surface can badge the exact
                    # assumption months later without recomputing or guessing.
                    "assumptions": assumptions if assumptions is not None
                    else engines.assumption_audit(data)})
    db.add(row); db.commit(); db.refresh(row)
    return row


@router.get("/templates")
def list_templates():
    return [{"standard": s,
             "title": ("US GAAP" if s == "us_gaap" else "IFRS")
                      + " financial input template",
             "download": f"/api/v1/financials/templates/{s}",
             "note": ("Workbook is protected as input guidance; server-side "
                      "validation on upload is the integrity guarantee "
                      "(ADR-005).")}
            for s in templates.LABELS]


@router.get("/templates/{standard}")
def download_template(standard: str):
    try:
        content = templates.build_template(standard)
    except KeyError:
        raise HTTPException(status_code=404,
                            detail="unknown standard; use 'us_gaap' or 'ifrs'")
    fname = f"AXIOM_Financials_Template_{'USGAAP' if standard == 'us_gaap' else 'IFRS'}.xlsx"
    return Response(content, media_type=XLSX_MIME, headers={
        "Content-Disposition": f'attachment; filename="{fname}"'})


@router.post("/datasets", response_model=schemas.DatasetOut, status_code=201)
def create_dataset(body: schemas.DatasetIn, db: Session = Depends(get_db),
                   tenant: str = Depends(_writer),
                   authorization: str | None = Header(default=None)):
    _enforce_company_limit(db, authorization)
    v = engines.validate_dataset(body.data)
    if v["errors"]:
        raise HTTPException(status_code=422, detail=v["errors"])
    return _store(db, tenant, body.name, body.data, "direct", v["warnings"],
                  body.enterprise_id, balance=v.get("balance"),
                  assumptions=v.get("assumptions"))


@router.post("/datasets/upload", response_model=schemas.DatasetOut,
             status_code=201)
async def upload_dataset(file: UploadFile = File(...),
                         name: str | None = Form(default=None),
                         db: Session = Depends(get_db),
                         tenant: str = Depends(_writer),
                         authorization: str | None = Header(default=None)):
    _enforce_company_limit(db, authorization)
    content = await file.read()
    if len(content) > MAX_UPLOAD:
        raise HTTPException(status_code=413, detail="file exceeds 5 MB")
    dataset, issues = templates.parse_workbook(content)
    if dataset is None:
        raise HTTPException(status_code=422, detail=issues)
    warnings = [i["warning"] for i in issues if "warning" in i]
    return _store(db, tenant, name or dataset["company"].get("name")
                  or file.filename, dataset, "upload", warnings)


@router.get("/datasets", response_model=list[schemas.DatasetOut])
def list_datasets(limit: int = 50, db: Session = Depends(get_db),
                  tenant: str = Depends(_tenant),
                  scoped: int | None = Depends(_scoped)):
    q = db.query(models.FinancialDataset).filter_by(tenant=tenant)
    if scoped is not None:                       # magic-link viewer: this company only
        q = q.filter(models.FinancialDataset.enterprise_id == scoped)
    return q.order_by(models.FinancialDataset.id.desc()).limit(min(limit, 200)).all()


@router.get("/datasets/{dataset_id}", response_model=schemas.DatasetDetailOut)
def get_dataset(dataset_id: int, db: Session = Depends(get_db),
                tenant: str = Depends(_tenant),
                scoped: int | None = Depends(_scoped)):
    return _get_dataset(db, tenant, dataset_id, scoped)


@router.get("/datasets/{dataset_id}/profile",
            responses={200: {"model": DatasetProfileOut}})
def enterprise_profile(dataset_id: int, db: Session = Depends(get_db),
                       tenant: str = Depends(_tenant),
                       scoped: int | None = Depends(_scoped)):
    """One-call summary for the Business Enterprise page (ADR-011):
    company card, data coverage, lineage depth, documents, and the latest
    valuation headline."""
    row = _get_dataset(db, tenant, dataset_id, scoped)
    data = row.data
    from ..valuation.models import ValuationRun
    vr = db.query(ValuationRun).filter_by(tenant=tenant, dataset_id=row.id)\
           .order_by(ValuationRun.id.desc()).first()
    docs = db.query(models.EnterpriseDocument)\
             .filter_by(tenant=tenant).filter(
                 models.EnterpriseDocument.dataset_id == row.id).count()
    depth = 0
    cursor = row
    while cursor.parent_dataset_id:
        depth += 1
        cursor = db.get(models.FinancialDataset, cursor.parent_dataset_id)
    c = data["company"]
    latest = None
    if vr:
        det = vr.result.get("deterministic", {})
        ra = vr.result.get("risk_adjusted", {})
        latest = {"run_id": vr.id, "mode": vr.mode,
                  "enterprise_value": det.get("enterprise_value"),
                  "raev": ra.get("raev"), "created_at": vr.created_at}
    logo_url = None
    if row.enterprise_id:
        try:
            from ...accounts import _logo_url as _lu   # 7f rider: company identity
            logo_url = _lu(db, row.enterprise_id)
        except Exception:
            logo_url = None
    return {"dataset_id": row.id, "name": row.name, "source": row.source,
           "company": {k: c.get(k) for k in
                        ("name", "ownership", "standard", "currency",
                         "sector", "tax_rate", "shares_outstanding",
                         "share_price")},
            "logo_url": logo_url,
            "coverage": engines.data_coverage(data),
            "lineage_depth": depth, "root_is_self": depth == 0,
            "documents_attached": docs, "latest_valuation": latest,
            "created_at": row.created_at}


@router.get("/datasets/{dataset_id}/eva-distribution")
def eva_distribution_surface(dataset_id: int, db: Session = Depends(get_db),
                             tenant: str = Depends(_tenant),
                             scoped: int | None = Depends(_scoped)):
    """§7n — EVA's spread, in two panels that never blend.

    ⭐ A RENDERING JOB OVER COMPLETED WORK. `derive_series` already computes
    NOPAT and invested capital PER PERIOD; this hands that series and the
    engine's own WACC to the module and returns what came back. ⛔ It computes
    no statistic itself and never touches the Monte Carlo kernel.
    """
    from ...eva_distribution import eva_distribution as _dist
    row = _get_dataset(db, tenant, dataset_id, scoped)
    series = engines.derive_series(row.data)
    # ⭐ ONE WACC, ONE OWNER — the same call the ratio surface makes, so the
    # distribution and the headline EVA cannot disagree about the capital charge.
    # ⛔⭐⭐ THE REASON TRAVELS. `except Exception: w = None` discarded the one
    # sentence that tells the reader what to do — `engines.wacc` raises naming
    # the missing input, and that message is what makes the absence actionable.
    # Measured: of 17 broad except-handlers in the valuation path, 7 discard the
    # exception's reason; this was one of them.
    try:
        w = engines.wacc(dict((row.data.get("company") or {}), _debt_book=None))["wacc"]
        werr = None
    except Exception as e:                                   # noqa: BLE001
        w, werr = None, str(e)
    return _dist(series.get("ratios") or [], w, wacc_absent=werr)


@router.get("/datasets/{dataset_id}/frequency-view")
def frequency_view(dataset_id: int, view: str | None = None,
                   interpolate: bool = False,
                   db: Session = Depends(get_db),
                   tenant: str = Depends(_tenant),
                   scoped: int | None = Depends(_scoped)):
    """The statements at a chosen grain. ⭐ READ-TIME ONLY — nothing is stored.

    ⛔⭐⭐ THAT IS THE STRUCTURAL GUARANTEE THAT INTERPOLATION NEVER ENTERS A PACK.
    A pack freezes the STORED dataset; this computes a view from it and returns
    it. There is no write path, so an interpolated figure cannot be frozen
    however the calling code is later rewritten — the same reasoning as
    `ax_assigned_feedback` having no column able to hold comment text.

    ⭐ `interpolate` defaults to FALSE. The finer view exists only when the CXO
    asks for it, and every figure it produces carries its own status and method.
    """
    # ⛔⭐⭐ THREE DOTS, NOT FOUR. This file's package is
    # `services.api.modules.financials`, so `...` is `services.api` — where
    # `frequency_views` lives. `....` is `services`, which has no such module,
    # and the ImportError only fires WHEN THE ENDPOINT IS CALLED because the
    # import is function-level. Every gate passed and the endpoint had never
    # once succeeded in production.
    from ... import frequency_views as FVW
    from . import periods as _PR
    row = _get_dataset(db, tenant, dataset_id, scoped)
    base = _PR.frequency_of(row.data)
    views = FVW.enabled_views(base)
    target = view or base
    if target not in FVW.VIEWS:
        raise HTTPException(422, f"view must be one of {list(FVW.VIEWS)}")
    chosen = next(v for v in views if v["view"] == target)
    out = {"base_frequency": base, "view": target, "views": views,
           # ⛔⭐⭐ THE LABELS TRAVEL WITH THE FIGURES, and the FRAMEWORK with
           # them — us_gaap and ifrs disagree on 9 of 26 captions, so a client
           # holding only the key cannot pick between them. The key stays the
           # identifier; the label is render-only and never a pack input.
           "framework": FVW._framework_of(row.data),
           "line_labels": FVW.line_labels(row.data),
           # ⭐ Grain-aware from this lane: the constant never saw it.
           "method_labels": FVW.METHOD_LABEL,
           "refused_methods": FVW.REFUSED_METHODS,
           "interpolated": False, "statements": None}
    if chosen["enabled"]:
        st = FVW.aggregate_statements(row.data, target)
        out["statements"] = st
        out["period_labels"] = FVW.period_labels(FVW.periods_of(st), target)
        return out
    if not interpolate:
        # ⭐ The disabled view is RETURNED as disabled with its reason, never
        # omitted. A missing option reads as a product that cannot do it.
        out["disabled_reason"] = chosen["reason"]
        return out
    out["interpolated"] = True
    out["method"] = FVW.LINEAR
    # ⭐ The grain reaches the sentence now — see `method_label`'s note.
    out["method_label"] = FVW.method_label(FVW.LINEAR, base, target)
    st = FVW.interpolate_statements(row.data, target)
    out["statements"] = st
    out["period_labels"] = FVW.period_labels(FVW.periods_of(st), target)
    return out


@router.get("/datasets/{dataset_id}/derived")
def derived_series(dataset_id: int, db: Session = Depends(get_db),
                   tenant: str = Depends(_tenant),
                   scoped: int | None = Depends(_scoped)):
    row = _get_dataset(db, tenant, dataset_id, scoped)
    return engines.derive_series(row.data)


@router.get("/datasets/{dataset_id}/completeness",
            responses={404: {"description": "dataset not found — the id does "
                                            "not exist, or belongs to another "
                                            "tenant (deliberately "
                                            "indistinguishable)"}})
def dataset_completeness(dataset_id: int, db: Session = Depends(get_db),
                         tenant: str = Depends(_tenant),
                         scoped: int | None = Depends(_scoped)):
    """Which declared quantities this dataset can answer, and WHY not.

    ⛔ "54% complete" is a grade; "54%, and these six need current assets you
    have not supplied" is a next action. This returns the second — see
    `completeness.score` and `missing_input_index`.

    ⭐ The upload metadata travels with the score because the blank state needs
    both in one call: a reader asking "why is this empty" is asking about the
    last upload as often as about the fields.
    """
    from ... import completeness as CP
    row = _get_dataset(db, tenant, dataset_id, scoped)
    scored = CP.score(row.data)
    scored["next_actions"] = CP.missing_input_index(scored)
    scored["dataset"] = {
        "id": row.id,
        "name": row.name,
        "frequency": getattr(row, "frequency", None),
        "template_version": getattr(row, "template_version", None),
        # ⭐ Two different timestamps, both reported. "When did you upload" and
        # "when was the data last written" answer different questions, and a
        # surface showing one as the other misdates the customer's own work.
        "uploaded_at": getattr(row, "uploaded_at", None),
        "data_written_at": getattr(row, "data_written_at", None),
        "original_filename": getattr(row, "original_filename", None),
    }
    return scored


@router.post("/datasets/{dataset_id}/forecast")
def forecast_dataset(dataset_id: int, body: schemas.ForecastRequest,
                     db: Session = Depends(get_db),
                     tenant: str = Depends(_tenant),
                     scoped: int | None = Depends(_scoped),
               authed: bool = Depends(_authed)):
    row = _get_dataset(db, tenant, dataset_id, scoped)
    if body.persist:
        from ..identity.deps import write_allowance, enforce_write
        # authed flag alone is not entitlement: route through the one gate
        from fastapi import Request  # noqa: F401  (dep-free re-check)
        enforce_write({"authenticated": authed,
                       "plan": _plan_of(db, tenant) if authed else None,
                       "tenant": tenant})
    # A dataset that already carries a plan (forecast years) is re-forecast
    # from its historicals rather than rejected, so /forecast works on every
    # dataset (incl. the showcase reference companies).
    fdata = row.data
    if (fdata.get("periods") or {}).get("forecast"):
        fdata = _historicals_only(fdata)
    try:
        fc = engines.auto_forecast(fdata, body.assumptions)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    provenance = fc.pop("_forecast_provenance")
    out = {"provenance": provenance, "derived": engines.derive_series(fc)}
    if body.persist:
        stored = _store(db, tenant,
                        body.name or f"{row.name} (AXIOM trend forecast)",
                        fc, "forecast", [], row.enterprise_id)
        out["dataset_id"] = stored.id
    return out


# Line set for Plan vs Forecast + long-run variance, as the model carries them.
_PVM_LINES = [
    ("revenue", "Revenue"), ("cogs", "COGS"), ("gross_profit", "Gross profit"),
    ("opex", "Operating expenses"), ("ebitda", "EBITDA"), ("ebit", "EBIT"),
    ("net_income", "Net income"), ("capex", "Capex"),
    ("nwc_change", "Δ Net working capital"), ("fcff", "FCFF"),
]


def _pvm_full(base_hist: dict, forecast_stmts: dict, fyears: list) -> dict:
    """A full dataset = base historicals + a forecast statement set (income/balance/
    cash_flow, forecast-only), so derive_series can produce apples-to-apples lines."""
    hist = list(base_hist["periods"]["historical"])
    keep = {str(y) for y in hist}
    # ⭐ THE DECLARATION IS CARRIED, NOT REBUILT AWAY (§7.41, third instance).
    # This wrote a fresh periods dict with only historical/forecast, so every
    # downstream reader of the assembled dataset defaulted to annual.
    out = {"company": base_hist["company"],
           "periods": {"historical": hist,
                       "forecast": [int(y) for y in fyears],
                       "frequency": (base_hist.get("periods") or {}).get("frequency") or "annual"},
           "income_statement": {}, "balance_sheet": {}, "cash_flow": {}}
    for block, keys in (("income_statement", engines.IS_KEYS),
                        ("balance_sheet", engines.BS_KEYS),
                        ("cash_flow", engines.CF_KEYS)):
        for k in keys:
            hv = {y: base_hist[block].get(k, {}).get(y) for y in keep}
            fv = (forecast_stmts.get(block) or {}).get(k, {})
            out[block][k] = {**hv, **fv}
    return out


def _pvm_line_values(full: dict) -> dict:
    """{line_key: {year_str: value}} over the FORECAST years of `full`, using the
    model's own derivations so every series compares like-for-like."""
    d = engines.derive_series(full)
    years, n_h = d["years"], d["n_historical"]
    IS, CF = full["income_statement"], full["cash_flow"]
    out = {k: {} for k, _ in _PVM_LINES}
    for i, y in enumerate(years):
        if i < n_h:
            continue
        ys = str(y)
        rev = d["revenue"][i]
        cogs = IS["cogs"].get(ys)
        opex = IS["opex"].get(ys)
        out["revenue"][ys] = rev
        out["cogs"][ys] = cogs
        out["gross_profit"][ys] = round(rev - cogs, 4) if (rev is not None and cogs is not None) else None
        out["opex"][ys] = opex
        out["ebitda"][ys] = d["ratios"][i]["ebitda"]
        out["ebit"][ys] = d["ebit"][i]
        out["net_income"][ys] = d["net_income"][i]
        out["capex"][ys] = CF["capex"].get(ys)
        # ⭐ THE SECOND SITE OF THE SAME DEFECT, AND IT WAS LIVE FOR DAYS.
        # `extend_method=ensemble&horizon=10` — which is exactly what the
        # /valuation page sends — 500'd here with
        #   TypeError: unsupported operand type(s) for -: 'NoneType' and 'float'
        # derive_series now PROPAGATES absence rather than inventing a zero, so
        # d["nwc"][i] is None for any period the extended plan does not cover.
        # Note `gross_profit` four lines up already guards; this line did not.
        # One function, one data source, two different answers to the same
        # question — the two-owners shape at statement level.
        out["nwc_change"][ys] = (
            engines._n(lambda a, b: round(a - b, 4), d["nwc"][i], d["nwc"][i - 1])
            if i > 0 else None)
        out["fcff"][ys] = d["fcff"][i]
    return out


def _pvm_forecast_only(data: dict, years: list) -> dict:
    """Extract a forecast-only statement set (income/balance/cash_flow) for `years`."""
    keep = {str(y) for y in years}
    return {block: {k: {y: v for y, v in (data[block].get(k) or {}).items() if y in keep}
                    for k in keys}
            for block, keys in (("income_statement", engines.IS_KEYS),
                                ("balance_sheet", engines.BS_KEYS),
                                ("cash_flow", engines.CF_KEYS))}


def compute_plan_vs_methods(data: dict, horizon: int | None = None,
                            extend_method: str | None = None) -> dict:
    """Business Planning & Forecasting — the CLIENT PLAN laid against each of AXIOM's
    five forecasting methodologies + ensemble, per line item and per year, with
    variance (plan − ensemble, abs and %). The `horizon` governs how far the AXIOM
    method series project (shared across the page). `extend_method` optionally
    continues the client plan beyond its supplied years, ANCHORED ON THE PLAN'S
    ENDPOINT (level + trajectory continue from the plan, never re-anchored to
    history); extended years are flagged is_extension=true. Honest-empty when no
    client plan. method_params carries the ACTUAL fitted parameters for the drawers.

    Pure over `data` (an active dataset's .data dict) — no DB / tenant scoping — so
    the /plan-vs-methods route AND cross-domain aggregators (Urgent Items I5) share
    ONE computation. The caller merges dataset_id/dataset_version onto the result."""
    from ...forecast_studio import (compute_method, METHODS as FS_METHODS, _LABELS,
                                    DAMP_PHI, DAMP_ALPHA, DAMP_BETA, MC_PATHS, MC_SEED,
                                    DIVERGENCE_CV, HORIZON_MAX)
    periods = data.get("periods") or {}
    hist = [int(y) for y in periods.get("historical") or []]
    fc_years = [int(y) for y in periods.get("forecast") or []]
    std = (data.get("company") or {}).get("standard", "us_gaap")
    method_labels = {m: _LABELS.get(m, m) for m in FS_METHODS}
    base_resp = {"standard": std, "has_client_plan": bool(fc_years),
                 "historical_years": hist, "forecast_years": fc_years,
                 "methods": list(FS_METHODS), "method_labels": method_labels,
                 "ensemble_method": "ensemble"}
    if not fc_years:
        return {**base_resp, "line_items": [], "summary": None, "extension": None,
                "note": ("No client plan on this dataset. Upload your own forecast "
                         f"with the {templates.policy.version('user')} template — mark the right-hand columns "
                         "'Forecast', enter a year and your figures — and AXIOM "
                         "will compare it against its five forecasting methods.")}
    if len(hist) < 2:
        return {**base_resp, "line_items": [], "summary": None, "extension": None,
                "note": "At least 2 historical years are required to compare "
                        "against AXIOM's methods."}

    base = _historicals_only(data)
    _pfreq = _freq_of(data)
    hist_last, plan_last = hist[-1], max(fc_years)
    # ⭐ SPANS ARE COUNTED, NOT SUBTRACTED, AND HORIZONS ARE WALKED, NOT ADDED.
    # `plan_last - hist_last` gave 20 where the true distance is 8 quarters, and
    # `hist_last + hz` gave a period three quarters out when ten were meant. Both
    # are correct for annual by coincidence — there the encoding and the count
    # share a unit — which is why they survived from d3c70cb until a live 500.
    plan_span = _period_span(hist_last, plan_last, _pfreq)
    hz = max(1, min(horizon or plan_span, HORIZON_MAX))
    hz_last = _advance(hist_last, hz, _pfreq)
    all_last = plan_last if plan_span >= hz else hz_last
    method_hz = _period_span(hist_last, all_last, _pfreq)
    method_years = _fc_periods(hist_last, method_hz, _pfreq)

    # AXIOM method series — fit on HISTORY, projected across the full range.
    method_out = {m: compute_method(base, m, method_hz) for m in FS_METHODS}
    method_extra = {m: method_out[m][1] for m in FS_METHODS}
    method_vals = {m: _pvm_line_values(_pvm_full(base, method_out[m][0], method_years))
                   for m in FS_METHODS}

    # Optional PLAN EXTENSION — anchored on the plan's endpoint (the plan itself is
    # the "history" for the extension, so level + trajectory continue seamlessly).
    ext_years, extension = [], None
    plan_fyears = list(fc_years)
    plan_forecast = _pvm_forecast_only(data, fc_years)
    # A comparison is SAFE — YYYYQ is monotonic, so ordering holds even though
    # differences do not. Left as an ordinary comparison deliberately.
    if extend_method in FS_METHODS and all_last > plan_last:
        pseudo = {"company": data["company"],
                  "periods": {"historical": list(fc_years), "forecast": []},
                  **_pvm_forecast_only(data, fc_years)}
        ext_hz = _period_span(plan_last, all_last, _pfreq)
        ext_stmts, ext_extra = compute_method(pseudo, extend_method, ext_hz)
        ext_years = _fc_periods(plan_last, ext_hz, _pfreq)
        # splice the extension onto the plan's forecast statements
        for block in ("income_statement", "balance_sheet", "cash_flow"):
            for k, series in (ext_stmts.get(block) or {}).items():
                plan_forecast.setdefault(block, {}).setdefault(k, {}).update(series)
        plan_fyears = fc_years + ext_years
        extension = {"method": extend_method, "label": _LABELS.get(extend_method, extend_method),
                     "from_year": plan_last, "to_year": all_last, "anchor": "plan_endpoint",
                     "years": ext_years,
                     "note": ("Projected from the plan's endpoint — the level and trajectory "
                              "continue from the plan (fit on the plan's own years), never "
                              "re-anchored to history, so there is no discontinuity at the seam. "
                              "These years are an AXIOM projection, not management intent.")}

    plan_vals = _pvm_line_values(_pvm_full(base, plan_forecast, plan_fyears))

    all_years = sorted(set(plan_fyears) | set(method_years))
    ext_set = set(ext_years)

    def variance(plan_v, axiom_v):
        if plan_v is None or axiom_v is None:
            return None
        return {"abs": round(plan_v - axiom_v, 4),
                "pct": round((plan_v - axiom_v) / axiom_v, 6) if axiom_v else None}

    line_items = []
    for key, label in _PVM_LINES:
        yrs = []
        for y in all_years:
            ys = str(y)
            plan_v = plan_vals.get(key, {}).get(ys)
            methods_v = {m: method_vals[m].get(key, {}).get(ys) for m in FS_METHODS}
            yrs.append({"year": y, "plan": plan_v, "is_extension": y in ext_set,
                        "methods": methods_v, "variance": variance(plan_v, methods_v.get("ensemble"))})
        line_items.append({"key": key, "label": label, "years": yrs})

    # per-method ACTUAL parameters for the drawers (from the real fit)
    method_params = {"constants": {
        "damping_phi": DAMP_PHI, "damping_alpha": DAMP_ALPHA, "damping_beta": DAMP_BETA,
        "montecarlo_paths": MC_PATHS, "montecarlo_seed": MC_SEED,
        "driver_cagr_cap": 0.25, "ensemble_backtest_min_history": 6,
        "divergence_cv_threshold": DIVERGENCE_CV}}
    for m in FS_METHODS:
        e = method_extra[m]
        method_params[m] = {"drivers": e.get("drivers"), "bands": e.get("bands"),
                            "weights": e.get("weights"), "divergence": e.get("divergence"),
                            "fitted_history_len": e.get("fitted_history_len")}

    rev_line = next((li for li in line_items if li["key"] == "revenue"), None)
    summary = None
    if rev_line and rev_line["years"]:
        term = next((yy for yy in reversed(rev_line["years"]) if not yy["is_extension"]), rev_line["years"][-1])
        v = term["variance"]
        summary = {"line": "revenue", "terminal_year": term["year"],
                   "plan": term["plan"], "ensemble": term["methods"].get("ensemble"),
                   "variance": v, "plan_more_optimistic": bool(v and v["abs"] > 0)}
    # the full extended-plan forecast (supplied years + AXIOM tail) — ready to pass
    # to POST /valuation/run as forecast_override to value it as its own basis.
    extended_plan = None
    if extension is not None:
        extended_plan = {"periods": {"forecast": [int(y) for y in plan_fyears]},
                         "income_statement": plan_forecast["income_statement"],
                         "balance_sheet": plan_forecast["balance_sheet"],
                         "cash_flow": plan_forecast["cash_flow"]}
    return {**base_resp, "horizon": hz, "method_horizon": method_hz,
            "forecast_years": fc_years, "extended_years": ext_years, "all_years": all_years,
            "extension": extension, "extended_plan": extended_plan, "line_items": line_items,
            "method_params": method_params, "summary": summary}


@router.get("/datasets/{dataset_id}/plan-vs-methods")
def plan_vs_methods(dataset_id: int, db: Session = Depends(get_db),
                    tenant: str = Depends(_tenant),
                    scoped: int | None = Depends(_scoped),
                    horizon: int | None = None,
                    extend_method: str | None = None):
    row = _get_dataset(db, tenant, dataset_id, scoped)
    return {"dataset_id": row.id, "dataset_version": row.version,
            **compute_plan_vs_methods(row.data, horizon, extend_method)}


@router.post("/documents", response_model=schemas.DocumentOut, status_code=201)
async def upload_document(file: UploadFile = File(...),
                          note: str = Form(default=""),
                          dataset_id: int | None = Form(default=None),
                          db: Session = Depends(get_db),
                          tenant: str = Depends(_writer)):
    """Unstructured-document plumbing (CA §3.4). Stored only in Phase 6;
    AI analysis lands in Phase 7 behind the §6.15 approval gate, so
    ai_analysis stays null rather than fabricated (SPEC-008 §4.10)."""
    content = await file.read()
    if len(content) > MAX_UPLOAD:
        raise HTTPException(status_code=413, detail="file exceeds 5 MB")
    if dataset_id is not None:
        _get_dataset(db, tenant, dataset_id)
    row = models.EnterpriseDocument(
        tenant=tenant, dataset_id=dataset_id, filename=file.filename or "document",
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(content), note=note[:500], data=content, ai_analysis=None)
    db.add(row); db.commit(); db.refresh(row)
    return row


@router.get("/documents", response_model=list[schemas.DocumentOut])
def list_documents(limit: int = 50, db: Session = Depends(get_db),
                   tenant: str = Depends(_tenant)):
    return db.query(models.EnterpriseDocument).filter_by(tenant=tenant)\
             .order_by(models.EnterpriseDocument.id.desc())\
             .limit(min(limit, 200)).all()


@metrics_router.get("/glossary")
def glossary():
    """Tooltip definitions for every tab title, section header, chart title,
    and KPI — backend-owned so the words live beside the mathematics."""
    return engines.GLOSSARY


@metrics_router.get("/ratios/{dataset_id}")
def ratios_surface(dataset_id: int, db: Session = Depends(get_db),
                   tenant: str = Depends(_tenant),
                   scoped: int | None = Depends(_scoped)):
    """The ratio surface — the registry, rendered.

    ⭐⭐ A RENDERING JOB OVER COMPLETED WORK. The registry has executed since R7
    and reached no screen: pack.py pins `executed: true, renders_any_figure:
    false`. This endpoint computes NOTHING — it calls `ratio_registry.explain`
    per ratio per period and reports what came back. A test asserts by AST that
    this function contains no arithmetic operator.

    ⭐ SOLE OWNERSHIP HOLDS. Every value here resolves through the evaluator,
    which delegates the five guarded quantities to their owners in ratios.py.
    The surface consumes owners; it never restates one.

    ⭐⭐ MEASURED BEFORE BUILDING: of 77 registry ratios, 45 compute on at least
    one active dataset and 32 compute on none. Of the 45, ELEVEN already reach a
    screen (the KPI strip, the covenant panel, target-state) and 34 reach
    nothing. This surface is for all 45, with the 32 listed once with what they
    need.
    """
    from . import ratio_registry as rr
    row = _get_dataset(db, tenant, dataset_id, scoped)
    data = row.data
    der = engines.derive_series(data)
    years, n_hist = der["years"], der["n_historical"]
    # period_labels is a MAP keyed by period value, not a list — one map per
    # response, deliberately asymmetric with the per-row `year_label` (see
    # engines.period_labels). Indexing it by position raises KeyError, which is
    # how this was caught.
    labels = der.get("period_labels") or {}

    def _label(y):
        return str(labels.get(y, labels.get(str(y), y)))

    # ⭐ THE CALLER SUPPLIES WACC, because the registry delegates it to
    # ratios.wacc_at and the evaluator will not reach for a caller's data. This
    # is the ENGINE's own wacc for this dataset — one number, one owner.
    try:
        supplied = {"wacc_at": engines.wacc(dict(data.get("company") or {},
                                                 _debt_book=None))["wacc"]}
    except Exception:
        supplied = {}

    _standard = ((data.get("company") or {}).get("standard") or "us_gaap")
    out, absent = [], []
    for r in rr.load()["ratios"]:
        periods = []
        for i, y in enumerate(years):
            e = rr.explain(data, years, i, r["id"], supplied=supplied)
            periods.append({
                "year": y, "label": _label(y),
                # ⭐ PROJECTION IS MARKED, NEVER PRESENTED AS FACT. A ratio on a
                # forecast period is a projection of a projection.
                "projection": i >= n_hist,
                "value": e.get("value"), "absent": e.get("absent"),
                "needs": e.get("needs"),
                "needs_display": e.get("needs_display"),
                "operands": e.get("operands"), "inputs": e.get("inputs"),
                "unnamed_tokens": e.get("unnamed_tokens"),
            })
        computed = [p for p in periods if p["value"] is not None]
        rec = {"id": r["id"], "name": r["name"], "category": r["category"],
               "unit": r.get("unit"), "polarity": r.get("polarity"),
               "definition": r.get("definition"),
               "definition_display": rr.render_expr(r.get("definition"), _standard),
               "formula": r["formula"],
               "headline": bool(r.get("headline")),
               "display_rule": r.get("display_rule"),
               # ⭐ the display form travels with the machine-readable one
               "formula_display": rr.render_expr(r["formula"], _standard),
               "periods": periods}
        if computed:
            out.append(rec)
        else:
            # ⭐ LISTED ONCE, WITH WHAT IT WOULD NEED — never a page of blanks.
            absent.append({"id": r["id"], "name": r["name"],
                           "category": r["category"],
                           "definition": r.get("definition"),
                           "definition_display": rr.render_expr(
                               r.get("definition"), _standard),
                           "needs": next((p["needs"] for p in periods
                                          if p.get("needs")), None),
                           "needs_display": next(
                               (p["needs_display"] for p in periods
                                if p.get("needs_display")), None),
                           "reason": next((p["absent"] for p in periods
                                           if p.get("absent")), None)})
    return {
        "dataset_id": dataset_id,
        "registry_version": rr.load().get("registry_version"),
        "periods": [{"year": y, "label": _label(y),
                     "projection": i >= n_hist} for i, y in enumerate(years)],
        "n_historical": n_hist,
        "ratios": out,
        "absent": absent,
        # ⭐ COVERAGE ON THE SURFACE (III.4): "0 of 0" and "0 of 77" print the
        # same tick, so the denominator ships with the numerator.
        "coverage": {"in_registry": len(rr.load()["ratios"]),
                     "rendered": len(out), "absent": len(absent)},
    }


@metrics_router.get("/ratio-independence/{dataset_id}")
def ratio_independence_surface(dataset_id: int, db: Session = Depends(get_db),
                               tenant: str = Depends(_tenant),
                               scoped: int | None = Depends(_scoped)):
    """How many of the declared quantities are actually different questions.

    ⛔⭐⭐ THE FINDING IS NEGATIVE AND THE PAYLOAD SAYS SO. Measured: all but one
    computable quantity is algebraically independent, and the single exact
    identity is `dupont_three_step == roe` — the decomposition closing, which is
    its purpose. **There is essentially no redundancy to prune**, so "less is
    more" on a ratio page is a CURATION decision about what a reader needs, never
    a de-duplication. A surface that rendered this as "N duplicates found" would
    be dressing a negative result as a feature.

    ⭐ The method is EMPIRICAL because the textual one was disproved by a
    counterexample in the same registry, and the payload carries what the claim
    is worth: agreement over N periods is evidence, not proof.
    """
    from ... import ratio_independence as ri
    row = _get_dataset(db, tenant, dataset_id, scoped)
    out = ri.analyse(row.data)
    out["dataset_id"] = dataset_id
    return out


@metrics_router.get("/dupont/{dataset_id}")
def dupont_surface(dataset_id: int, period: int | None = None,
                   db: Session = Depends(get_db),
                   tenant: str = Depends(_tenant),
                   scoped: int | None = Depends(_scoped)):
    """The DuPont tree, its per-node history, and what moved ROE.

    ⛔⭐⭐ ONE PRODUCER. The frontend used to assemble this tree itself from
    `/ratios/{id}` — it held its own ROOT and FACTORS constants, decided each
    node's basis with a regex over the formula, and composed the mixed-basis
    sentence in TSX. Three facts the registry already owned, restated in a
    language the registry cannot be tested in. This endpoint serves
    `dupont_tree.build_tree`, which reads `explain` for every value, and the
    client-side assembly was deleted in the same lane (§7r-O).

    ⭐ THE SERIES IS A LOOP, NOT A SECOND CALL. Each node's history comes from
    the dataset already in hand, and every point carries its OWN status — a
    4-of-5 series ships four observed points and one absent one with its
    reason, never a 5-point line with an invented value.

    ⛔ THE ATTRIBUTION NAMES ITS METHOD. Logarithmic, symmetric in the three
    factors; it refuses at a sign change rather than switching silently.
    """
    from ... import dupont_tree as dt
    row = _get_dataset(db, tenant, dataset_id, scoped)
    data = row.data
    der = engines.derive_series(data)
    years, n_hist = der["years"], der["n_historical"]
    labels = der.get("period_labels") or {}

    def _label(y):
        return str(labels.get(y, labels.get(str(y), y)))

    # ⭐ THE CALLER NAMES A PERIOD BY ITS VALUE, not by an index. An index is a
    # position in an array the caller cannot see, and it silently means a
    # different year the day a period is added.
    idx = n_hist - 1
    if period is not None:
        if period not in years:
            raise HTTPException(404, detail={
                "error": "no_such_period",
                "message": f"period {period} is not in this dataset",
                "periods": years})
        idx = years.index(period)

    out = dt.build_tree(data, period_index=idx)
    # ⭐ LABELS ON THE SURFACE PAYLOAD ONLY (the label ruling). The tree carries
    # period IDENTIFIERS; the caption is attached here, where nothing freezes.
    for p in out["periods"]:
        p["label"] = _label(p["period"])
    for s_ in out.get("series", {}).values():
        for pt in s_["points"]:
            pt["label"] = _label(pt["period"])
    out["period_label"] = _label(out["period"])

    # ⛔ THE ATTRIBUTION IS AGAINST THE PRIOR REAL PERIOD, and it refuses when
    # there is not one — the first period of every dataset has no predecessor.
    out["attribution"] = (dt.attribute(data, idx - 1, idx) if idx > 0 else
                          {"available": False,
                           "reason": ("attribution compares two periods and "
                                      f"{years[idx]} is the first one")})
    if out["attribution"].get("available"):
        out["attribution"]["from_label"] = _label(out["attribution"]["from_period"])
        out["attribution"]["to_label"] = _label(out["attribution"]["to_period"])
    out["dataset_id"] = dataset_id
    from . import ratio_registry as rr
    out["registry_version"] = rr.load().get("registry_version")
    return out


@metrics_router.get("/dashboard/{dataset_id}")
def dashboard(dataset_id: int, valuation_run_id: int | None = None,
              db: Session = Depends(get_db), tenant: str = Depends(_tenant),
              scoped: int | None = Depends(_scoped)):
    """The Executive KPI Strip + Enterprise Health Index (Product §5.6/§5.8)."""
    row = _get_dataset(db, tenant, dataset_id, scoped)
    valuation_result = None
    if valuation_run_id is not None:
        from ..valuation.models import ValuationRun
        vr = db.get(ValuationRun, valuation_run_id)
        if not vr or vr.tenant != tenant:
            raise HTTPException(status_code=404, detail="valuation run not found")
        valuation_result = vr.result
    else:
        from ..valuation.models import ValuationRun
        vr = db.query(ValuationRun).filter_by(tenant=tenant, dataset_id=dataset_id)\
               .order_by(ValuationRun.id.desc()).first()
        if vr:
            valuation_result = vr.result
    return engines.dashboard_metrics(row.data, valuation_result)


def _plan_of(db, tenant: str) -> str:
    from ..identity.models import User
    u = db.query(User).filter_by(tenant=tenant).first()
    return (u.plan or "free") if u else "free"


@router.get("/datasets/{dataset_id}/pro-forma")
def pro_forma_statements(dataset_id: int, db: Session = Depends(get_db),
                         tenant: str = Depends(_tenant),
                         scoped: int | None = Depends(_scoped),
                         horizon: int | None = None):
    """Stochastic three-statement pro forma with per-line attainment
    probabilities and cumulative multi-year odds (ADR-018). Optional horizon
    scopes the statements to the first N forecast years (matches the chart)."""
    from . import proforma
    row = _get_dataset(db, tenant, dataset_id, scoped)
    try:
        return proforma.stochastic_statements(row.data, horizon=horizon)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/datasets/{dataset_id}/comprehensive-income")
def comprehensive_income(dataset_id: int, db: Session = Depends(get_db),
                         tenant: str = Depends(_tenant),
                         scoped: int | None = Depends(_scoped),
                         horizon: int | None = None):
    """Stochastic Statement of Comprehensive Income (net income + OCI),
    standard-aware (US GAAP vs IFRS), with FX/securities/pension/hedge OCI
    drivers modeled where on file (ADR-019). Optional horizon scopes to N years."""
    from . import oci as oci_mod
    row = _get_dataset(db, tenant, dataset_id, scoped)
    try:
        return oci_mod.statement_of_comprehensive_income(row.data, horizon=horizon)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/oci/schema")
def oci_schema():
    """The OCI driver input schema (for the data-entry surface)."""
    from . import oci as oci_mod
    return oci_mod.OCI_DRIVER_SCHEMA


@metrics_router.get("/profitability/{dataset_id}")
def profitability_surface(dataset_id: int, db: Session = Depends(get_db),
                          tenant: str = Depends(_tenant),
                          scoped: int | None = Depends(_scoped)):
    """The profitability surface — T2, rendered.

    ⭐⭐ A RENDERING JOB OVER COMPLETED WORK, exactly as the ratio surface was.
    This endpoint COMPUTES NOTHING: it reads the stored dimensional observations,
    hands them to `dimensional_analytics`, and reports what came back. A test
    asserts by AST that this function contains no arithmetic operator.

    ⭐ THE ASSUMPTION TRAVELS WITH THE NUMBER. T2 returns each allocated figure
    together with its method, grade and prose assumption in ONE object, and this
    passes that object through whole. Splitting them here — figures in one key,
    method in another — would restore exactly the defect the design prevents.

    ⭐⭐ R1'S REFUSAL IS PAYLOAD, NOT AN OMISSION. `profit_before_tax` and
    `net_profit` arrive as `{refused, ruling, reason}` and are forwarded intact,
    so a surface renders a stated refusal rather than a blank.
    """
    from . import dimensional_analytics as A
    from . import dimensions as DIM
    from . import managerial as M
    from ...dimensional import DimensionMember, DimensionObservation

    ds = _get_dataset(db, tenant, dataset_id, scoped)
    data = ds.data or {}
    IS = data.get("income_statement") or {}
    freq = (data.get("periods") or {}).get("frequency") or ds.frequency or "annual"

    rows = (db.query(DimensionObservation, DimensionMember)
            .filter(DimensionObservation.dataset_id == dataset_id)
            .filter(DimensionMember.id == DimensionObservation.member_id)
            .all())
    if not rows:
        # ⭐ ABSENCE DECLARES. No dimensional detail is not an empty chart — it
        # is a stated fact with the measure that would change it.
        return {"dataset_id": dataset_id, "available": False,
                "reason": ("No dimensional detail has been supplied for this "
                           "dataset. Add a Segments & Products sheet to your "
                           "upload to unlock revenue, margin and allocation "
                           "analysis by line."),
                "needs": ["revenue by segment or product line"],
                "dimension_types": [], "periods": []}

    # ⭐ THE POOLS RIDE ON THE DATASET PAYLOAD, like the statements. They are
    # company-level period facts, not dimensional observations, and the Cost
    # Behaviour sheet collects them at pool grain (CORE §8l).
    cb_pools = data.get("cost_behaviour") or []
    # ⭐⭐ T5.1's DECLARATION. Where it exists the §22 corrective quantifies;
    # where it does not it states its premise and asks for the column.
    avoid_rows = data.get("avoidability") or []
    by_type = {}
    for obs, mem in rows:
        by_type.setdefault(mem.dimension_type, {}) \
               .setdefault(obs.period, {}) \
               .setdefault(obs.measure, {})[mem.code] = obs.value
    names = {m.code: m.name for _o, m in rows}

    out = {"dataset_id": dataset_id, "available": True, "frequency": freq,
           "member_names": names, "dimension_types": sorted(by_type),
           "calculation_version": A.CALCULATION_VERSION, "by_type": {}}

    for dtype, periods in by_type.items():
        ordered = sorted(periods)
        block = {"periods": ordered, "by_period": {}, "mix_shift": None,
                 "margin_bridge": None}
        for p in ordered:
            meas = periods[p]
            rev = meas.get("revenue") or {}
            cost = meas.get("direct_cost") or {}
            dopex = meas.get("direct_opex") or {}
            co_rev = (IS.get("revenue") or {}).get(str(p))
            co_cogs = (IS.get("cogs") or {}).get(str(p))
            co_opex = (IS.get("opex") or {}).get(str(p))

            # ⭐⭐ T4.2 — CONTRIBUTION, AND THE §22 CORRECTIVE. The pools live on
            # the dataset payload (the Cost Behaviour sheet); where none are
            # supplied every capability below DECLINES in the client's own
            # column names and nothing is guessed.
            # ⭐ COVERAGE FIRST. Partial classification overstates contribution,
            # and contribution is the figure the §22 corrective argues from.
            coverage = M.pools_reconcile(cb_pools, p, _company_cost(co_cogs, co_opex))
            # ⭐⭐ THE OBSERVED PER-LINE MEASURES TRAVEL WITH THE POOLS (T4.4).
            # A pool marked `direct` is traceable to one of these and uses it;
            # re-allocating an observed figure by revenue discards the
            # observation, which is the defect this module exists to prevent.
            observed = {m: meas.get(m) for m in ("direct_cost", "direct_opex")
                        if meas.get(m)}
            variable_by_line = (
                M.variable_cost_by_line(cb_pools, p, rev, observed=observed)
                if coverage["available"] else {})
            variable_status = M.variable_cost_status(cb_pools, p)
            rev_panel = A.revenue_by_dimension(rev, co_rev)
            dopex_panel = A.revenue_by_dimension(dopex, co_opex)

            # ⭐⭐ THE SHARED POOL IS THE STATED RESIDUAL, AND T2 COMPUTED IT.
            # Direct opex that no line claimed IS the shared and corporate
            # overhead; `revenue_by_dimension` already returns it as the
            # `__unallocated__` member, so this reads a number T2 produced
            # rather than subtracting one here.
            #
            # ⭐ WITHOUT THIS, ALLOCATED EBIT WAS UNAVAILABLE FOR EVERY LINE OF
            # EVERY DATASET: the hierarchy was called with revenue, direct_cost
            # and direct_opex and never `allocated_opex`, so the deepest level —
            # the one the whole module builds towards — declared a missing input
            # forever and the surface drew an em dash.
            pool = (dopex_panel.get("value") or {}).get(A.UNALLOCATED_MEMBER) \
                if dopex_panel.get("available") else None
            # ⭐⭐ REVENUE IS A GRADE D DRIVER AND `allocate` SAYS SO. The method
            # is a modelling choice, not an observation, so it travels in the
            # payload with its grade and its prose assumption and the surface
            # renders both. A silent choice here would be the defect the whole
            # allocation vocabulary exists to prevent.
            shared = A.allocate(pool, rev, method="revenue")
            share_of = shared.get("value") or {}

            units_by_line = meas.get("units") or {}
            lines = {}
            contributions = {}
            for code in rev:
                contributions[code] = M.contribution(
                    rev.get(code), variable_by_line.get(code),
                    variable_status=variable_status)
                lines[code] = A.margin_hierarchy(
                    revenue=rev.get(code), direct_cost=cost.get(code),
                    direct_opex=dopex.get(code),
                    allocated_opex=share_of.get(code))
            mix_plan, move_plan = _constrained_mix(
                M, data.get("capacity"), p, contributions, units_by_line,
                cb_pools)
            block["by_period"][p] = {
                "revenue": rev_panel,
                "mix": A.revenue_mix(rev, co_rev),
                "concentration": A.concentration(rev),
                "direct_cost": A.revenue_by_dimension(cost, co_cogs),
                "direct_opex": dopex_panel,
                "shared_allocation": dict(shared, pool=pool),
                "lines": lines,
                "contribution": contributions,
                "cost_behaviour_coverage": coverage,
                "constrained_mix": mix_plan,
                "transport_plan": move_plan,
                # ⭐⭐ THE SENTENCE THE SOURCE DOCUMENT'S §22 REQUIRES BESIDE THE
                # FULLY-ALLOCATED LOSS. Without it the surface shows a negative
                # line and invites the exit that would make the company worse
                # off.
                "covers_variable_cost": {
                    code: M.covers_variable_cost(
                        (contributions[code] or {}).get("value"),
                        (lines[code]["allocated_ebit"] or {}).get("value"),
                        line=names.get(code, code),
                        avoidable=(_avoid(M, avoid_rows, p, code,
                                          share_of.get(code)) or {}).get("avoidable"),
                        stranded=(_avoid(M, avoid_rows, p, code,
                                         share_of.get(code)) or {}).get("stranded"))
                    for code in rev},
                "avoidability": {
                    code: M.avoidability(avoid_rows, share_of.get(code), p, code)
                    for code in rev},
                "totals": _statement_totals(A, co_rev, co_cogs, co_opex),
            }
        if len(ordered) >= 2:
            a, b = ordered[-2], ordered[-1]
            ma = block["by_period"][a]["mix"]
            mb = block["by_period"][b]["mix"]
            if ma["available"] and mb["available"]:
                block["mix_shift"] = A.mix_shift(ma["value"], mb["value"])
                ga = {c: block["by_period"][a]["lines"][c]["gross_profit"].get("margin")
                      for c in block["by_period"][a]["lines"]}
                gb = {c: block["by_period"][b]["lines"][c]["gross_profit"].get("margin")
                      for c in block["by_period"][b]["lines"]}
                block["margin_bridge"] = A.margin_bridge(ma["value"], ga,
                                                         mb["value"], gb)
        # ⭐⭐ EVERY CONSECUTIVE PAIR, NOT ONLY THE LAST. T2 built `mix_shift`
        # and the surface rendered none of it, so the module answered "what is
        # the mix" and never "what changed" — the second is the question worth
        # asking. With four periods the shift has a DIRECTION, and a single
        # latest-pair delta cannot show one.
        block["mix_shift_series"] = _mix_shift_series(A, block, ordered)
        block["trend"] = _margin_trend(block, ordered)
        # ⭐⭐ THE LANE'S PURPOSE. Every other panel restates what the client
        # uploaded plus arithmetic they can do themselves; these are sentences
        # about what the data SAYS. Derived, gated, and empty where the pattern
        # is absent.
        block["findings"] = _findings(block, names)
        out["by_type"][dtype] = block

    # ⭐⭐ WHAT THE SURFACE DOES NOT HAVE, STATED. Meridian holds ten periods of
    # statements and four of dimensional detail; a page that draws a four-point
    # series beside a ten-point one, saying nothing, implies a series it does
    # not hold. The shortfall is payload, not a footnote someone remembers.
    stmt_periods = sorted(
        {int(p) for p in ((IS.get("revenue") or {}).keys()) if str(p).isdigit()})
    dim_periods = sorted({p for pers in by_type.values() for p in pers})
    # ⭐⭐ A FORECAST PERIOD IS EXCLUDED BY RULING, NOT MISSING — AND THE FIRST
    # VERSION OF THIS BLOCK CALLED IT MISSING. On Meridian, whose statements run
    # five actual and five forecast periods, the page listed 2026–2030 among the
    # periods with "no product-line detail" — one sentence above a note saying
    # AXIOM DOES NOT PRODUCE ONE. The surface contradicted its own ruling, and
    # the fixture could not reveal it because the fixture has no forecast years.
    #
    # ⭐ Only an ACTUAL period with no detail is a gap a client can close by
    # supplying data. Conflating the two would send someone looking for a sheet
    # that is not merely absent but refused.
    fc = {int(p) for p in ((data.get("periods") or {}).get("forecast") or [])
          if str(p).isdigit()}
    actual_periods = [p for p in stmt_periods if p not in fc]
    out["coverage"] = {
        "statement_periods": stmt_periods,
        "actual_periods": actual_periods,
        "dimensional_periods": dim_periods,
        "missing_periods": [p for p in actual_periods if p not in dim_periods],
        "excluded_forecast_periods": sorted(p for p in stmt_periods if p in fc),
        "note": ("Dimensional detail covers actual periods only. A product-line "
                 "allocation of a forecast compounds two estimates — the "
                 "projection's own uncertainty and the allocation assumption on "
                 "top of it — so AXIOM does not produce one."),
    }
    out["data_statuses"] = list(DIM.DATA_STATUSES)
    out["allocation_methods"] = A.ALLOCATION_METHODS
    return out
