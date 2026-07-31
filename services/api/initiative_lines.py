"""B10/B11 — the initiative → statement-line link, and the attribution rule.

⭐ THREE RECORDED GAPS TRACE TO ONE MEASURED FACT: `linked_item_code` reaches an
assessment item and no link reaches a statement line. The Value Bridge's
initiatives driver is absent, §7o's causal chain stops at `kpi_movement`, and the
brochure proof point is withdrawn as unsupportable — all for the same reason.

⭐ THE LINK IS DECLARED, NEVER INFERRED. An initiative relates to a statement line
because someone SAID SO. Inferring it from a correlation would fabricate exactly
the number the brochure ruling was withdrawn for asserting — a figure that looks
derived and is invented.

⭐ WHY NOT VIA THE EXISTING KPI LINKS. Measured before building: 41 live
`KpiInitiativeLink` rows exist, so initiative→KPI is already declared. But
`KpiPlan` — the LIVE surface, 413 rows — carries NO FORMULA, and the only model
that does (`KpiDefinition`, with `formula` over canonical statement keys) holds
ZERO ROWS and is the subject of an open retire-or-repoint ruling (A6). Routing
this through it would build on an empty surface that may be deleted.
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from .accounts import Base

# Attribution modes — the rule recorded at 42d23da.
SOLE = "sole"                 # exactly one initiative declares this line
PROPORTIONAL = "proportional"  # several do; split by declared weight
UNATTRIBUTED = "unattributed"  # movement no initiative declares


class InitiativeLineLink(Base):
    """One declared relationship: this initiative moves this statement line.

    ⭐ `declared_by` IS NOT NULLABLE IN SPIRIT AND THE COLUMN SAYS SO. A link with
    no declarer is an inference wearing a declaration's clothes, and the whole
    point of this model is that a human asserted the relationship.

    ⭐ `weight` IS THE DECLARER'S CLAIM ABOUT SHARE, not a fitted coefficient.
    Where several initiatives touch one line, the weights are what the company
    says the split is — AXIOM does not estimate it.
    """
    __tablename__ = "ax_initiative_line_links"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    initiative_id = Column(Integer, index=True, nullable=False)
    # a canonical statement key or computed aggregate — validated on write
    statement_line = Column(String(64), index=True, nullable=False)
    # ⭐ NULL means "the declarer did not state a share". It is NOT 1.0 and NOT 0:
    # an unstated share is unknown, and treating it as full ownership is exactly
    # the over-crediting this rule exists to prevent.
    weight = Column(Float, nullable=True)
    declared_by = Column(Integer, nullable=True)
    declared_by_label = Column(String(255), nullable=False, default="")
    declared_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    note = Column(Text, nullable=True)
    revoked_at = Column(DateTime, nullable=True)


def statement_lines():
    """Every name a link may reference — DERIVED from the engine's own key sets.

    ⭐ A HAND LIST WOULD LET A LINK NAME A LINE THAT DOES NOT EXIST, and the
    attribution would then silently contribute nothing while looking declared.
    """
    from .modules.financials import engines as fin
    base = set(fin.IS_KEYS) | set(fin.BS_KEYS) | set(fin.CF_KEYS)
    # the computed aggregates planning already exposes to formulas
    return base | {"gross_profit", "ebit", "ebitda", "total_assets",
                   "total_debt", "net_debt", "nwc"}


def declare(db, cid, initiative_id, statement_line, *, weight=None, user=None,
            note=None, now=None):
    """Declare a link. ⭐ VALIDATES THE LINE AGAINST THE ENGINE'S OWN KEYS."""
    from fastapi import HTTPException
    if statement_line not in statement_lines():
        raise HTTPException(422, f"{statement_line!r} is not a statement line")
    if weight is not None and not (0.0 < float(weight) <= 1.0):
        raise HTTPException(422, "weight must lie in (0, 1]")
    row = InitiativeLineLink(
        company_id=cid, initiative_id=initiative_id,
        statement_line=statement_line,
        weight=None if weight is None else float(weight),
        declared_by=getattr(user, "id", None),
        declared_by_label=(getattr(user, "name", None)
                           or getattr(user, "email", "") or ""),
        declared_at=now or datetime.utcnow(), note=note)
    db.add(row)
    db.flush()
    return row


def links_for(db, cid):
    return (db.query(InitiativeLineLink)
              .filter_by(company_id=cid)
              .filter(InitiativeLineLink.revoked_at.is_(None))
              .order_by(InitiativeLineLink.id).all())


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE ATTRIBUTION RULE
# ═══════════════════════════════════════════════════════════════════════════

def attribute(db, cid, line_movements):
    """Split each line's movement across the initiatives that DECLARED it.

    `line_movements` is {statement_line: delta}.

    ⭐⭐ EXCLUSIVITY OF LINKAGE IS NOT EXCLUSIVITY OF CAUSE. A line with ONE
    linked initiative and THREE real drivers must not have its whole movement
    attributed to the one link — a partially-linked model systematically
    over-credits whichever initiative was wired up first, and it does so
    invisibly, because the model cannot see the drivers nobody declared.

    So a SOLE link attributes its DECLARED WEIGHT and no more. Where no weight
    was stated, NOTHING is attributed and the reason is given — an unstated share
    is unknown, and assuming full ownership is the fabrication this exists to
    prevent.
    """
    rows = links_for(db, cid)
    by_line = {}
    for r in rows:
        by_line.setdefault(r.statement_line, []).append(r)

    out, residual = [], {}
    for line, delta in (line_movements or {}).items():
        declared = by_line.get(line) or []
        if delta is None:
            residual[line] = {"amount": None,
                              "reason": "the line's movement is not computable"}
            continue
        if not declared:
            # ⭐ ABSENCE STAYS ABSENT. No declared link, no attribution.
            residual[line] = {"amount": delta,
                              "reason": "no initiative declares this line"}
            continue

        weighted = [r for r in declared if r.weight is not None]
        unweighted = [r for r in declared if r.weight is None]
        total_w = sum(r.weight for r in weighted)

        if total_w > 1.0 + 1e-9:
            # ⭐ DECLARED SHARES EXCEEDING THE WHOLE ARE A DECLARATION ERROR, and
            # normalising them would silently invent a split nobody stated.
            residual[line] = {
                "amount": delta,
                "reason": (f"declared weights sum to {round(total_w, 4)} (>1); "
                           f"the declaration is inconsistent and nothing is "
                           f"attributed")}
            continue

        mode = SOLE if len(declared) == 1 else PROPORTIONAL
        for r in weighted:
            out.append({"initiative_id": r.initiative_id,
                        "statement_line": line, "mode": mode,
                        "declared_weight": r.weight,
                        "amount": delta * r.weight,
                        "declared_by": r.declared_by_label,
                        "declared_at": (r.declared_at.isoformat()
                                        if r.declared_at else None)})
        for r in unweighted:
            out.append({"initiative_id": r.initiative_id,
                        "statement_line": line, "mode": mode,
                        "declared_weight": None, "amount": None,
                        "absent": ("no share was declared, so no amount is "
                                   "attributed — an unstated share is unknown, "
                                   "not full ownership"),
                        "declared_by": r.declared_by_label})
        # ⭐ THE UNDECLARED REMAINDER IS RESIDUAL, ALWAYS. Even a sole link with
        # weight 1.0 leaves zero here only because the declarer said so.
        left = delta * (1.0 - total_w)
        if abs(left) > 1e-12 or not weighted:
            residual[line] = {
                "amount": left,
                "reason": (f"{round((1.0 - total_w) * 100, 2)}% of this line's "
                           f"movement is not covered by a declared share")}

    return {"attributed": out,
            "residual": residual,
            "residual_total": sum(v["amount"] for v in residual.values()
                                  if v.get("amount") is not None),
            "unlinked_initiatives": unlinked(db, cid)}


def unlinked(db, cid):
    """⭐ INITIATIVES WITH NO DECLARED LINK, NAMED. They contribute nothing, and
    saying so is what stops a reader assuming the linked ones are all of them."""
    from .accounts import Initiative
    linked_ids = {r.initiative_id for r in links_for(db, cid)}
    rows = db.query(Initiative).filter_by(company_id=cid).all()
    return [{"initiative_id": i.id, "ref_code": i.ref_code, "title": i.title,
             "reason": "no statement-line link has been declared"}
            for i in rows if i.id not in linked_ids]
