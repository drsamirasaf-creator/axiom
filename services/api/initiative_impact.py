"""B12 — client-declared expected impact per initiative, and plan versus actual.

⭐⭐ THIS IS NOT A BUSINESS-CASE MODEL, AND THE DISTINCTION IS THE WHOLE POINT.
The brochure proof point was withdrawn because AXIOM would have had to ORIGINATE a
per-initiative value it has no basis for — no cost, no benefit profile, no timing,
no IRR. ⭐ HERE AXIOM ORIGINATES NOTHING. A PE-backed company's value-creation plan
already carries expected financial impact per line item; the commitment exists, in
writing, before AXIOM sees the company. This stores that declaration and tracks
delivery against it.

⭐ DECLARED, NEVER DERIVED — the same guard as B10's. A module that fitted an
expectation to observed movement would manufacture agreement between plan and
actual, which is the one thing plan-versus-actual must never do.

⭐⭐ AND IT DOES NOT WEAKEN THE ATTRIBUTION RULE. Declaring an expected impact does
NOT make a linkage exclusive: the actual side still comes from B10's DECLARED
SHARE, and the residual still stands. Exclusivity of linkage is not exclusivity of
cause, and a declared expectation is not a licence to claim a whole movement.
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from .accounts import Base

# what a comparison can conclude
ON_OR_AHEAD = "on_or_ahead"
SHORT = "short"
MISS_NO_MOVEMENT = "miss_no_movement"     # declared, and the line did not move
# ⭐⭐ A SEPARATE VERDICT, AND THE DISTINCTION IS LOAD-BEARING. A line that MOVED
# while this initiative holds no B10 declared share is NOT a delivery failure —
# it is a MISSING LINK. Reporting it as a miss would tell a client they failed to
# deliver when the true answer is that nobody declared the share, and they would
# go looking in the wrong place.
MISS_UNLINKED = "miss_no_declared_share"
NOT_COMPARABLE = "not_comparable"         # the line's movement is not computable


class InitiativeImpactDeclaration(Base):
    """One client declaration: this initiative is expected to move this line.

    ⭐⭐ APPEND-ONLY, AND EVERY ROW CARRIES ITS PREDECESSOR'S VALUE. A declaration
    is a COMMITMENT, and a commitment that can be quietly revised is not one. The
    trail is the record of what was promised and when it changed.

    ⭐ DECISION-RECORD SHAPED — company-scoped, actor-attributed, timestamped,
    stable `event_type` — the same shape as `PackRelease`, `WatchEvent` and
    `AssumptionEdit`, so §7s.4 projects over it rather than needing a second store.
    ⭐ A DECLARED EXPECTATION IS A DECISION, and the Decision Record's coverage
    guard will claim it. That is correct and deliberate.
    """
    __tablename__ = "ax_initiative_impact_declarations"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    event_type = Column(String(40), nullable=False,
                        default="initiative_impact_declared")
    occurred_at = Column(DateTime, nullable=False, default=datetime.utcnow,
                         index=True)
    actor_user_id = Column(Integer, nullable=True)
    actor_label = Column(String(255), nullable=False, default="")

    initiative_id = Column(Integer, index=True, nullable=False)
    statement_line = Column(String(64), index=True, nullable=False)
    # ⭐ THE CLIENT'S NUMBER. Nullable because a client may declare that an
    # initiative affects a line WITHOUT committing to an amount — and that is a
    # different statement from declaring zero.
    expected_amount = Column(Float, nullable=True)
    # ⭐ TIMING IS PART OF THE COMMITMENT. "£2m" and "£2m by Q4" are different
    # promises, and comparing the first against a period is meaningless.
    expected_by = Column(String(24), nullable=True)      # period end, ISO date
    # ⭐ OPTIONAL, AND ITS ABSENCE IS NOT A DEFECT. The client may state a basis;
    # AXIOM neither requires nor validates one, because validating it would be
    # the beginning of originating it.
    basis = Column(Text, nullable=True)

    prior_amount = Column(Float, nullable=True)
    # ⭐ NULL prior is ambiguous on its own — a first declaration and a revision
    # from null look identical — so the distinction is stored, not inferred.
    prior_absent = Column(Integer, nullable=False, default=1)
    superseded_at = Column(DateTime, nullable=True)
    withdrawn_at = Column(DateTime, nullable=True)


def statement_lines():
    """⭐ THE SAME VOCABULARY B10 VALIDATES AGAINST, imported rather than
    re-listed. Two lists would drift and a declaration would name a line the
    attribution cannot find, contributing nothing while looking declared."""
    from .initiative_lines import statement_lines as _sl
    return _sl()


def declare(db, cid, initiative_id, statement_line, *, expected_amount=None,
            expected_by=None, basis=None, user=None, now=None):
    """Record a declaration, superseding any live one for the same pair."""
    from fastapi import HTTPException
    if statement_line not in statement_lines():
        raise HTTPException(422, f"{statement_line!r} is not a statement line")
    now = now or datetime.utcnow()

    prior = live_for(db, cid, initiative_id, statement_line)
    if prior is not None:
        prior.superseded_at = now

    row = InitiativeImpactDeclaration(
        company_id=cid, occurred_at=now,
        actor_user_id=getattr(user, "id", None),
        actor_label=(getattr(user, "name", None)
                     or getattr(user, "email", "") or ""),
        initiative_id=initiative_id, statement_line=statement_line,
        expected_amount=(None if expected_amount is None
                         else float(expected_amount)),
        expected_by=expected_by, basis=basis,
        prior_amount=(prior.expected_amount if prior is not None else None),
        prior_absent=0 if (prior is not None
                           and prior.expected_amount is not None) else 1)
    db.add(row)
    db.flush()
    return row


def live_for(db, cid, initiative_id, statement_line):
    return (db.query(InitiativeImpactDeclaration)
              .filter_by(company_id=cid, initiative_id=initiative_id,
                         statement_line=statement_line)
              .filter(InitiativeImpactDeclaration.superseded_at.is_(None))
              .filter(InitiativeImpactDeclaration.withdrawn_at.is_(None))
              .order_by(InitiativeImpactDeclaration.id.desc()).first())


def live(db, cid):
    return (db.query(InitiativeImpactDeclaration)
              .filter_by(company_id=cid)
              .filter(InitiativeImpactDeclaration.superseded_at.is_(None))
              .filter(InitiativeImpactDeclaration.withdrawn_at.is_(None))
              .order_by(InitiativeImpactDeclaration.id).all())


def history(db, cid, initiative_id=None):
    """⭐ Decision-Record shaped: actor, timestamp, prior value, new value."""
    q = db.query(InitiativeImpactDeclaration).filter_by(company_id=cid)
    if initiative_id is not None:
        q = q.filter(InitiativeImpactDeclaration.initiative_id == initiative_id)
    return [{"event_type": r.event_type,
             "occurred_at": r.occurred_at.isoformat() if r.occurred_at else None,
             "actor_user_id": r.actor_user_id, "actor_label": r.actor_label,
             "initiative_id": r.initiative_id,
             "statement_line": r.statement_line,
             "prior_amount": r.prior_amount,
             "prior_absent": bool(r.prior_absent),
             "expected_amount": r.expected_amount,
             "expected_by": r.expected_by, "basis": r.basis,
             "superseded_at": (r.superseded_at.isoformat()
                               if r.superseded_at else None),
             "withdrawn_at": (r.withdrawn_at.isoformat()
                              if r.withdrawn_at else None)}
            for r in q.order_by(InitiativeImpactDeclaration.occurred_at.desc()).all()]


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ PLAN VERSUS ACTUAL
# ═══════════════════════════════════════════════════════════════════════════

def plan_vs_actual(declaration_block, attribution, line_movements):
    """Compare declared expectations against what the lines actually did.

    ⭐⭐ IT TAKES NO SESSION. Like the bridge's attribution reader, a published
    pack must not be able to re-read live declarations — a promise revised after
    publication would silently rewrite the plan a pack was judged against.

    `attribution` is B10's output: the ACTUAL side comes from the DECLARED SHARE,
    never from the whole line movement.

    ⭐ THREE ABSENCES ARE KEPT APART, because collapsing them is how a miss
    becomes invisible:
      · a line moved and NOTHING was declared  -> stated, NOT zero expectation
      · an expectation exists and the line did not move -> a MISS, rendered as one
      · a line's movement is not computable    -> not comparable, not a miss
    """
    decls = [d for d in (declaration_block.get("declarations") or [])
             if not d.get("superseded_at") and not d.get("withdrawn_at")]
    attributed = (attribution or {}).get("attributed") or []

    # actual, per (initiative, line), from the DECLARED SHARE only
    actual = {}
    for a in attributed:
        if a.get("amount") is None:
            continue
        actual[(a.get("initiative_id"), a.get("statement_line"))] = a

    rows, declared_lines = [], set()
    for d in decls:
        key = (d.get("initiative_id"), d.get("statement_line"))
        declared_lines.add(d.get("statement_line"))
        exp = d.get("expected_amount")
        got = actual.get(key)
        moved = line_movements.get(d.get("statement_line"))

        if exp is None:
            rows.append({**_head(d), "verdict": None, "actual": None,
                         "variance": None,
                         "absent": ("an affected line was declared with NO "
                                    "expected amount — that is not an "
                                    "expectation of zero")})
            continue
        if moved is None:
            rows.append({**_head(d), "verdict": NOT_COMPARABLE, "actual": None,
                         "variance": None,
                         "absent": "this line's movement is not computable"})
            continue
        if got is None:
            # ⭐⭐ TWO DIFFERENT FAILURES, AND THEY SEND A READER TO DIFFERENT
            # PLACES. Collapsing them is the absence-with-a-plausible-reason
            # shape: "you missed" reads as settled and stops the enquiry.
            if abs(moved) <= 1e-12:
                rows.append({**_head(d), "verdict": MISS_NO_MOVEMENT,
                             "actual": 0.0, "variance": -exp,
                             "note": ("a commitment was declared and the line "
                                      "did not move — a delivery miss")})
            else:
                rows.append({**_head(d), "verdict": MISS_UNLINKED,
                             "actual": None, "variance": None,
                             "line_movement": moved,
                             "absent": ("the line MOVED, but this initiative "
                                        "declares no share of it, so no actual "
                                        "can be attributed — declare the link "
                                        "(B10) before reading this as a miss")})
            continue
        act = got["amount"]
        rows.append({**_head(d), "verdict": (ON_OR_AHEAD if _meets(exp, act)
                                             else SHORT),
                     "actual": act, "variance": act - exp,
                     "declared_weight": got.get("declared_weight"),
                     "note": ("actual is this initiative's DECLARED SHARE of the "
                              "line movement, not the whole movement")})

    # ⭐ lines that moved with NOTHING declared — stated, never zero
    undeclared = []
    for line, delta in (line_movements or {}).items():
        if delta is None or line in declared_lines:
            continue
        if abs(delta) <= 1e-12:
            continue
        undeclared.append({"statement_line": line, "movement": delta,
                           "expected": None,
                           "absent": ("this line moved and NO expectation was "
                                      "declared against it — absent, not zero")})

    return {"rows": rows,
            "undeclared_movement": undeclared,
            "counts": {
                "declared": len(rows),
                "on_or_ahead": sum(1 for r in rows if r["verdict"] == ON_OR_AHEAD),
                "short": sum(1 for r in rows if r["verdict"] == SHORT),
                "miss_no_movement": sum(1 for r in rows
                                        if r["verdict"] == MISS_NO_MOVEMENT),
                "miss_no_declared_share": sum(1 for r in rows
                                              if r["verdict"] == MISS_UNLINKED),
                "not_comparable": sum(1 for r in rows
                                      if r["verdict"] == NOT_COMPARABLE),
                "no_amount_declared": sum(1 for r in rows if r["verdict"] is None),
                "lines_moved_undeclared": len(undeclared)},
            # ⭐⭐ THE RESIDUAL DISCIPLINE IS CARRIED THROUGH, NOT DROPPED. A
            # declaration does not make a linkage exclusive, so the part no
            # declared share covers stays visible here too.
            "residual": (attribution or {}).get("residual"),
            "note": ("actuals are DECLARED SHARES of line movements; a declared "
                     "expectation does not license attributing a whole movement "
                     "to one initiative")}


def _head(d):
    return {"initiative_id": d.get("initiative_id"),
            "statement_line": d.get("statement_line"),
            "expected_amount": d.get("expected_amount"),
            "expected_by": d.get("expected_by"),
            "basis": d.get("basis"),
            "declared_by": d.get("actor_label"),
            "declared_at": d.get("occurred_at")}


def _meets(expected, actual):
    """⭐ DIRECTION-AWARE. A commitment to REDUCE a cost line is met by a
    NEGATIVE movement, and comparing magnitudes would mark every successful cost
    reduction a miss."""
    if expected >= 0:
        return actual >= expected
    return actual <= expected


def include(app, get_db, require_admin):
    from fastapi import APIRouter, Depends
    from pydantic import BaseModel

    class DeclareIn(BaseModel):
        initiative_id: int
        statement_line: str
        expected_amount: float | None = None
        expected_by: str | None = None
        basis: str | None = None

    r = APIRouter(tags=["initiative-impact"])

    @r.get("/companies/{company_id}/initiative-impact")
    def _list(company_id: int, db=Depends(get_db), _m=Depends(require_admin)):
        rows = live(db, company_id)
        return {"declarations": [
            {"id": x.id, "initiative_id": x.initiative_id,
             "statement_line": x.statement_line,
             "expected_amount": x.expected_amount,
             "expected_by": x.expected_by, "basis": x.basis,
             "declared_by": x.actor_label,
             "declared_at": x.occurred_at.isoformat() if x.occurred_at else None}
            for x in rows],
            "statement_lines": sorted(statement_lines())}

    @r.post("/companies/{company_id}/initiative-impact")
    def _declare(company_id: int, body: DeclareIn, db=Depends(get_db),
                 m=Depends(require_admin)):
        from .accounts import User
        uid = getattr(m, "user_id", None)
        row = declare(db, company_id, body.initiative_id, body.statement_line,
                      expected_amount=body.expected_amount,
                      expected_by=body.expected_by, basis=body.basis,
                      user=(db.get(User, uid) if uid else None))
        db.commit()
        return {"id": row.id, "declared": True,
                "initiative_id": row.initiative_id,
                "statement_line": row.statement_line,
                "expected_amount": row.expected_amount,
                "prior_amount": row.prior_amount,
                "prior_absent": bool(row.prior_absent)}

    @r.get("/companies/{company_id}/initiative-impact/history")
    def _hist(company_id: int, initiative_id: int | None = None,
              db=Depends(get_db), _m=Depends(require_admin)):
        return {"history": history(db, company_id, initiative_id)}

    app.include_router(r)
    return r
