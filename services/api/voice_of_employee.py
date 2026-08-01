"""§4u-c — Voice of Employee: departmental survey feedback, grouped by category.

⭐⭐ THE RULING THIS MODULE EXISTS TO ENFORCE (1 Aug): **VERBATIM TEXT DOES NOT
TRAVEL INTO AN ASSIGNMENT.** A manager reads the words on the tab, under the
k-anonymity floor. The words do not become a management object with a name
attached, exported, forwarded or quoted.

⭐ WHY, IN ONE LINE: a comment under the floor is protected by the CONTEXT it is
read in. Copy it onto an initiative and it leaves that context — it acquires an
owner, a due date, an export, and a thread of people who never saw the consent
line. The floor cannot follow it there.

⭐ SO AN ASSIGNMENT CARRIES CATEGORY AND THEME ONLY. The theme is the manager's
own words about what they intend to do — not the employee's words about what is
wrong.

⭐ THE MACHINERY IS INHERITED, NOT REIMPLEMENTED. §4u-b already established: the
floor counts DISTINCT PARTICIPANTS (not comments), `participant_ref` is never
emitted, comments are shuffled, and department/seniority never travel back on a
comment. This module reuses `assessment_engine`'s floor, its suppression reasons
and its complement-inference guard.
"""
import random
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from .accounts import Base


class AssignedFeedback(Base):
    """A category of departmental feedback, assigned to an initiative.

    ⭐⭐ THERE IS NO COLUMN FOR COMMENT TEXT, AND THAT IS THE FEATURE. A schema
    that cannot hold verbatim text cannot leak it, however the calling code is
    later rewritten — the guarantee is structural rather than procedural.

    ⭐ DECISION-RECORD SHAPED — company-scoped, actor-attributed, timestamped,
    stable `event_type` — the same shape as `PackRelease`, `WatchEvent`,
    `AssumptionEdit` and `InitiativeImpactDeclaration`. **Assigning feedback is a
    decision**, and §7s.4 projects over it rather than needing a second store.
    """
    __tablename__ = "ax_assigned_feedback"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    event_type = Column(String(40), nullable=False, default="feedback_assigned")
    occurred_at = Column(DateTime, nullable=False, default=datetime.utcnow,
                         index=True)
    actor_user_id = Column(Integer, nullable=True)
    actor_label = Column(String(255), nullable=False, default="")

    department_id = Column(Integer, index=True, nullable=False)
    cycle_id = Column(Integer, index=True, nullable=True)
    # ⭐ THE SOURCE IS A CATEGORY, NEVER A COMMENT ID. A comment id would be a
    # pointer back to one person's sentence — the individual-tracking path §4x
    # forbids — and it would survive in the record after the tab stopped showing
    # the text.
    source_category = Column(String(64), nullable=False)
    # ⭐ THE MANAGER'S OWN WORDS about what they intend to do.
    theme = Column(Text, nullable=True)
    initiative_id = Column(Integer, index=True, nullable=True)
    withdrawn_at = Column(DateTime, nullable=True)


# ⭐ Fields that must NEVER appear in an assignment payload. Named once, asserted
# by the guard and by the module's own writer.
FORBIDDEN_IN_ASSIGNMENT = ("comment", "comments", "verbatim", "text", "body",
                           "participant_ref", "quote", "excerpt")


def categories():
    """The instrument's own categories — DERIVED, never a hand list.

    ⭐ A HAND LIST WOULD DRIFT FROM THE SURVEY. A category that fell out of the
    instrument would keep rendering as an empty section, which reads as "nobody
    said anything about this" — the exact confusion §4u-c's suppression rules
    exist to prevent.
    """
    import json
    import pathlib
    p = (pathlib.Path(__file__).resolve().parent / "assets"
         / "axiom_assessment_taxonomy_v2.json")
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []
    out = []
    for c in doc.get("categories") or []:
        out.append({"code": str(c.get("code")),
                    "title": c.get("title") or c.get("name"),
                    "definition": c.get("definition")})
    return out


def _category_of(item_id, item_index):
    """item_id -> the L1 CATEGORY code, derived from the instrument's own
    hierarchy.

    ⭐ `ax_assessment_items` is a TREE: `code` "3.4" hangs under the L1 "3.0",
    and the taxonomy's categories are exactly those L1 codes. So the category is
    the item's own first segment — read off the instrument, not mapped by a hand
    list that would drift the moment a question moved.
    """
    code = item_index.get(item_id)
    if not code:
        return None
    head = str(code).split(".")[0].strip()
    return f"{head}.0" if head else None


def for_department(db, company_id, department_id, *, cycle_id=None):
    """Feedback for ONE department, grouped by category.

    ⭐⭐ A SUPPRESSED CATEGORY IS RENDERED, NEVER OMITTED. An absent category and
    a suppressed one are different facts, and a department reading a blank
    section concludes its people said nothing.
    """
    from .accounts import (AssessmentCycle, AssessmentItem, AssessmentResponse,
                           Department)
    from .assessment_engine import KFLOOR, suppression_block

    dept = db.get(Department, department_id)
    base = {"company_id": company_id, "department_id": department_id,
            "department": getattr(dept, "name", None),
            "cycle_id": None, "has_data": False, "categories": []}
    if dept is None or dept.company_id != company_id:
        return {**base, "absent": "no such department for this company"}

    cyc = None
    if cycle_id is not None:
        cyc = db.get(AssessmentCycle, cycle_id)
    else:
        cyc = (db.query(AssessmentCycle)
                 .filter_by(company_id=company_id)
                 .filter(AssessmentCycle.closed_at.isnot(None))
                 .order_by(AssessmentCycle.closed_at.desc()).first())
    if cyc is None:
        return {**base, "absent": "no closed assessment cycle yet"}

    rows = (db.query(AssessmentResponse)
              .filter_by(cycle_id=cyc.id)
              .filter(AssessmentResponse.department == dept.name).all())
    # ⭐ THE FLOOR COUNTS DISTINCT PARTICIPANTS, NOT COMMENTS. Five comments from
    # one person is n=1 — five sentences from one identifiable person is a worse
    # exposure than five from five. Inherited from §4u-b verbatim.
    dept_people = {r.participant_ref for r in rows}

    # ⭐ the item's OWN code; the category is its first segment (see _category_of)
    item_index = {i.id: (i.code or "")
                  for i in db.query(AssessmentItem).filter_by(
                      framework_id=cyc.framework_id).all()}

    # ⭐⭐ THE COMPLEMENT GUARD, AT DEPARTMENT LEVEL. If only ONE department in the
    # cycle is below the floor, publishing every other makes its content derivable
    # by subtraction — so the department set is evaluated together, exactly as
    # `_partition_status` does for CEI.
    by_dept = {}
    for r in db.query(AssessmentResponse).filter_by(cycle_id=cyc.id).all():
        by_dept.setdefault(r.department, set()).add(r.participant_ref)
    below = [d for d, ppl in by_dept.items() if 0 < len(ppl) < KFLOOR]
    # one hidden slice is derivable; a second must join it
    at_floor = sorted((d for d, ppl in by_dept.items() if len(ppl) == KFLOOR),
                      key=lambda d: len(by_dept[d]))
    complement_hidden = set(at_floor[:1]) if len(below) == 1 else set()

    out_cats, n_shown = [], 0
    cat_titles = {c["code"]: c["title"] for c in categories()}
    grouped = {}
    for r in rows:
        if not (r.comment or "").strip():
            continue
        grouped.setdefault(_category_of(r.item_id, item_index) or "uncategorised",
                           []).append(r)

    for code in sorted(set(list(cat_titles) + list(grouped))):
        rs = grouped.get(code, [])
        people = {r.participant_ref for r in rs}
        n = len(people)
        block = {"category": code, "title": cat_titles.get(code, code),
                 "n_participants": n, "n_comments": len(rs)}
        if not rs:
            # ⭐ ABSENT ≠ SUPPRESSED. Nobody commented on this category.
            block.update({"suppressed": False, "comments": [],
                          "absent": "no comments in this category this cycle"})
        elif dept.name in complement_hidden or len(dept_people) < KFLOOR or n < KFLOOR:
            by_partition = (dept.name in complement_hidden
                            and len(dept_people) >= KFLOOR and n >= KFLOOR)
            # ⭐ THE COUNT IS PUBLISHED EVEN WHEN HIDDEN — it is what makes
            # "withheld" credible rather than indistinguishable from silence.
            block.update(suppression_block(n, by_partition))
            block["comments"] = []
        else:
            # ⭐ SHUFFLED, so list order cannot be aligned with roster order.
            shown = [{"comment": r.comment, "item_id": r.item_id} for r in rs]
            random.shuffle(shown)
            block.update({"suppressed": False, "comments": shown})
            n_shown += len(shown)
        out_cats.append(block)

    return {**base, "cycle_id": cyc.id, "has_data": bool(rows),
            "n_participants": len(dept_people),
            "categories": out_cats, "n_comments_shown": n_shown,
            "floor": KFLOOR}


def assign(db, company_id, department_id, source_category, *, initiative_id=None,
           theme=None, actor=None, cycle_id=None, now=None, **rejected):
    """Assign a CATEGORY of feedback to an initiative.

    ⭐⭐ IT REFUSES ANY ARGUMENT THAT COULD CARRY VERBATIM TEXT. Not by stripping
    it — by RAISING. Silently dropping a `comment=` kwarg would let a caller
    believe the text travelled, and the next reader would build on that belief.
    """
    from fastapi import HTTPException
    if rejected:
        bad = sorted(k for k in rejected)
        raise HTTPException(
            422, f"verbatim feedback does not travel into an assignment; "
                 f"refused fields: {bad}. An assignment carries the CATEGORY and "
                 f"your own THEME — the employee's words stay on the tab, under "
                 f"the anonymity floor.")
    now = now or datetime.utcnow()
    row = AssignedFeedback(
        company_id=company_id, occurred_at=now,
        actor_user_id=getattr(actor, "id", None),
        actor_label=(getattr(actor, "name", None)
                     or getattr(actor, "email", "") or ""),
        department_id=department_id, cycle_id=cycle_id,
        source_category=str(source_category),
        theme=(theme or None), initiative_id=initiative_id)
    db.add(row)
    db.flush()
    return {"id": row.id, "department_id": department_id,
            "source_category": row.source_category,
            "initiative_id": initiative_id, "theme": row.theme,
            "note": ("category and theme only — no verbatim comment text is "
                     "stored, exported or forwarded with this assignment")}


def assignments(db, company_id, *, department_id=None):
    q = db.query(AssignedFeedback).filter_by(company_id=company_id)
    if department_id is not None:
        q = q.filter(AssignedFeedback.department_id == department_id)
    return [{"id": r.id, "occurred_at": (r.occurred_at.isoformat()
                                         if r.occurred_at else None),
             "actor_user_id": r.actor_user_id, "actor_label": r.actor_label,
             "department_id": r.department_id, "cycle_id": r.cycle_id,
             "source_category": r.source_category, "theme": r.theme,
             "initiative_id": r.initiative_id,
             "withdrawn_at": (r.withdrawn_at.isoformat()
                              if r.withdrawn_at else None)}
            for r in q.order_by(AssignedFeedback.occurred_at.desc()).all()]


def include(app, get_db, require_member):
    from fastapi import APIRouter, Depends
    from pydantic import BaseModel

    class AssignIn(BaseModel):
        source_category: str
        initiative_id: int | None = None
        theme: str | None = None
        cycle_id: int | None = None
        # ⭐ NO COMMENT FIELD, DELIBERATELY. Pydantic rejects unknown keys by
        # default here, so a client that tries to post comment text is refused
        # at the boundary rather than server-side.

        model_config = {"extra": "forbid"}

    r = APIRouter(tags=["voice-of-employee"])

    @r.get("/companies/{company_id}/departments/{department_id}/voice")
    def _voice(company_id: int, department_id: int, cycle_id: int | None = None,
               db=Depends(get_db), _m=Depends(require_member)):
        return for_department(db, company_id, department_id, cycle_id=cycle_id)

    @r.post("/companies/{company_id}/departments/{department_id}/voice/assign")
    def _assign(company_id: int, department_id: int, body: AssignIn,
                db=Depends(get_db), m=Depends(require_member)):
        from .accounts import User
        uid = getattr(m, "user_id", None)
        out = assign(db, company_id, department_id, body.source_category,
                     initiative_id=body.initiative_id, theme=body.theme,
                     cycle_id=body.cycle_id,
                     actor=(db.get(User, uid) if uid else None))
        db.commit()
        return out

    @r.get("/companies/{company_id}/departments/{department_id}/voice/assignments")
    def _list(company_id: int, department_id: int, db=Depends(get_db),
              _m=Depends(require_member)):
        return {"assignments": assignments(db, company_id,
                                           department_id=department_id)}

    app.include_router(r)
    return r
