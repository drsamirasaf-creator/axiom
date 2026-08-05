"""§7s.4 — the Decision Record. A PROJECTION, not a fifth audit table.

⭐ IT READS SOURCE EVENTS AND COPIES NOTHING. Overrides, sign-offs, recommendation
dispositions, initiative approvals, changeset decisions, authority grants, pack
releases and watch events are ALREADY attributed and ALREADY stored. A second copy
is a second source of truth, and this era's own log records which way that goes.

⭐ `decision_id` IS DERIVED, NOT ALLOCATED — `"{source}:{row_id}"`. An allocated id
would need a table to allocate it from, and that table would be the fifth audit
store this design exists to avoid.

⭐ REALISED EFFECT IS THE COMPOUNDING HALF AND MUST NOT BE FABRICATED. Where an
earlier decision's outcome is now measurable, it is linked. Where it is not, the
field is ABSENT with a stated reason — never zero, never inferred. **A decision
whose effect cannot yet be measured is a legitimate state, not a gap to fill**,
and it is invisible in month one by construction.
"""
from datetime import datetime

# Status values for a projected decision.
TAKEN = "taken"                 # decided; effect not yet measurable
REALISED = "realised"           # decided, and the outcome is measurable
SUPERSEDED = "superseded"       # decided, then replaced by a later decision
WITHDRAWN = "withdrawn"         # decided, then revoked


def _d(source, row_id, *, cid, type_, decided_at, author, statement,
       rationale=None, computed_state=None, linked=None,
       expected=None, realised=None, realised_absent=None, status=TAKEN,
       attribution=None):
    """One projected decision.

    ⭐ `realised_effect` AND `realised_effect_absent` ARE MUTUALLY EXCLUSIVE, and
    exactly one is always set. A row carrying neither would read as "no effect";
    a row carrying both would be a contradiction the reader has to adjudicate.
    """
    if realised is None and realised_absent is None:
        realised_absent = "not yet measurable"
    return {
        "decision_id": f"{source}:{row_id}",
        "source": source,
        "cid": cid,
        "type": type_,
        "decided_at": decided_at.isoformat() if isinstance(decided_at, datetime)
        else decided_at,
        "author": author or "",
        "statement": statement,
        "rationale": rationale,
        # ⭐ THE NUMBER AS IT STOOD WHEN THE DECISION WAS TAKEN. Without it the
        # record says what was decided and not what it was decided ABOUT.
        "computed_state_at_decision": computed_state,
        "linked_object_ref": linked,
        "expected_effect": expected,
        "realised_effect": realised,
        "realised_effect_absent": realised_absent,
        "status": status,
        # §4x — travels whole, never a hand-picked field list
        "attribution": attribution,
    }


def _name(db, user_id, fallback=""):
    if not user_id:
        return fallback
    from .accounts import User
    u = db.get(User, user_id)
    return (u.name or u.email) if u is not None else fallback


# ═══════════════════════════════════════════════════════════════════════════
# THE SOURCES — each reads its own store, in place
# ═══════════════════════════════════════════════════════════════════════════

def src_overrides(db, cid):
    """A CXO adjusting a figure. ⭐ THE DECISION IS THE ADJUSTMENT; the computed
    value it replaced is the state at decision, which the model already froze."""
    from .overrides import REASON_LABEL, MetricOverride
    out = []
    for o in db.query(MetricOverride).filter_by(company_id=cid).all():
        # ⭐ WHOLE-ROW SERIALISATION, not a hand-picked field list. The overrides
        # serialiser dropped `created_at` exactly this way in Stage 2 and the
        # §4x attribution line silently lost its date.
        row = {c.name: getattr(o, c.name) for c in o.__table__.columns}
        when = row.get("created_at")
        line = (f"computed {row.get('computed_value_at_override')}, "
                f"adjusted to {row.get('override_value')} by "
                f"{row.get('author_label') or 'an authorised approver'}, "
                f"{REASON_LABEL.get(row.get('reason_category'), row.get('reason_category'))}")
        if row.get("reason_note"):
            line += f" — {row['reason_note']}"
        if when:
            line += f", {when.isoformat()[:10]}"
        out.append(_d(
            "override", o.id, cid=cid, type_="figure_adjusted", decided_at=when,
            author=row.get("author_label"),
            statement=(f"{row.get('metric_label') or row.get('metric_ref')} "
                       f"adjusted to {row.get('override_value')}"),
            rationale=row.get("reason_note"),
            computed_state=row.get("computed_value_at_override"),
            linked={"metric_ref": row.get("metric_ref"),
                    "department_id": row.get("department_id")},
            expected=None,
            realised_absent=("an override states a figure; its realised effect is "
                             "the figure itself, which is already recorded"),
            status=(SUPERSEDED if row.get("superseded_at") else TAKEN),
            attribution=line))
    return out


def src_signoffs(db, cid):
    """A CXO attesting to a dashboard AS SHOWN. ⭐ `signed_state` IS the computed
    state at decision — the model already persists the displayed values per
    metric, which is exactly what this field means."""
    from .overrides import DashboardSignoff
    out = []
    for s in db.query(DashboardSignoff).filter_by(company_id=cid).all():
        row = {c.name: getattr(s, c.name) for c in s.__table__.columns}
        out.append(_d(
            "signoff", s.id, cid=cid, type_="dashboard_attested",
            decided_at=row.get("signed_at") or row.get("created_at"),
            author=row.get("signer_label") or _name(db, row.get("signer_user_id")),
            statement="Dashboard attested as shown",
            computed_state=row.get("signed_state"),
            linked={"department_id": row.get("department_id")},
            realised_absent=("an attestation asserts a state; it has no separate "
                             "realised effect"),
            status=(SUPERSEDED if row.get("superseded_at") else TAKEN)))
    return out


def src_dispositions(db, cid):
    """A company's decision on an AXIOM recommendation — adopted, parked or
    dismissed. ⭐ ADOPTION IS THE ONE THAT COMPOUNDS: it links to an initiative
    whose impact becomes measurable later."""
    from .accounts import Initiative, RecommendationDisposition
    out = []
    for r in db.query(RecommendationDisposition).filter_by(company_id=cid).all():
        row = {c.name: getattr(r, c.name) for c in r.__table__.columns}
        expected = realised = None
        absent = None
        ini = db.get(Initiative, row["initiative_id"]) if row.get("initiative_id") else None
        if ini is not None:
            expected = ini.expected_impact_amount
            realised = ini.actual_impact_amount
            if realised is None:
                absent = (f"initiative {ini.ref_code or ini.id} has no actual "
                          f"impact recorded yet")
        else:
            absent = "no initiative is linked to this disposition"
        out.append(_d(
            "disposition", r.id, cid=cid,
            type_=f"recommendation_{row.get('status') or 'none'}",
            decided_at=row.get("decided_at") or row.get("first_seen_at"),
            author=_name(db, row.get("decided_by")),
            statement=f"Recommendation {row.get('fingerprint')} "
                      f"{row.get('status') or 'undecided'}",
            rationale=row.get("note"),
            linked={"initiative_id": row.get("initiative_id"),
                    "fingerprint": row.get("fingerprint")},
            expected=expected, realised=realised, realised_absent=absent,
            status=(REALISED if realised is not None else TAKEN)))
    return out


def src_initiatives(db, cid):
    """Approving an initiative, and what it turned out to be worth."""
    from .accounts import Initiative
    out = []
    for i in db.query(Initiative).filter_by(company_id=cid).all():
        row = {c.name: getattr(i, c.name) for c in i.__table__.columns}
        realised = row.get("actual_impact_amount")
        absent = None if realised is not None else (
            "no actual impact has been recorded against this initiative")
        out.append(_d(
            "initiative", i.id, cid=cid, type_="initiative_approved",
            decided_at=row.get("created_at"),
            author=row.get("owner_name") or _name(db, row.get("created_by")),
            statement=row.get("title") or f"Initiative {row.get('ref_code')}",
            rationale=row.get("description"),
            linked={"initiative_id": i.id, "ref_code": row.get("ref_code"),
                    "department_id": row.get("department_id")},
            expected=row.get("expected_impact_amount"),
            realised=realised, realised_absent=absent,
            status=(REALISED if realised is not None else TAKEN)))
    return out


def src_changeset_items(db, cid):
    """⭐ NOT IN THE NAMED LIST, AND IT IS THE PUREST DECISION IN THE SYSTEM.
    The approval gate records, per item, `decision`, `decided_by_user_id`,
    `decided_at` and `decision_note` — an approve/reject on a specific proposed
    change, with the OLD AND NEW VALUE both stored. That is a decision, an actor,
    a timestamp and the state at decision, already captured."""
    from .changeset import Changeset, ChangesetItem
    cs_ids = [c for (c,) in db.query(Changeset.id).filter_by(company_id=cid).all()]
    if not cs_ids:
        return []
    out = []
    rows = (db.query(ChangesetItem)
              .filter(ChangesetItem.changeset_id.in_(cs_ids))
              .filter(ChangesetItem.decided_at.isnot(None)).all())
    for it in rows:
        row = {c.name: getattr(it, c.name) for c in it.__table__.columns}
        out.append(_d(
            "changeset_item", it.id, cid=cid,
            type_=f"change_{row.get('decision') or 'undecided'}",
            decided_at=row.get("decided_at"),
            author=_name(db, row.get("decided_by_user_id")),
            statement=(f"{row.get('op')} {row.get('category')} "
                       f"{row.get('entity_label') or row.get('entity_key')}"),
            rationale=row.get("decision_note"),
            computed_state=row.get("old_value"),
            linked={"changeset_id": row.get("changeset_id"),
                    "entity_key": row.get("entity_key")},
            expected=row.get("new_value"),
            realised=(row.get("new_value") if row.get("applied") else None),
            realised_absent=(None if row.get("applied")
                             else "this change was decided but not applied")))
    return out


def src_authority(db, cid):
    """⭐ NOT IN THE NAMED LIST. Granting or revoking who may speak for a
    department is a governance decision, and revocation already carries a
    `revoke_reason` — a rationale the model asked for."""
    from .accounts import Department
    from .overrides import DepartmentAuthority
    out = []
    for g in db.query(DepartmentAuthority).filter_by(company_id=cid).all():
        row = {c.name: getattr(g, c.name) for c in g.__table__.columns}
        dept = db.get(Department, row["department_id"])
        who = _name(db, row.get("user_id"), "a user")
        dname = dept.name if dept is not None else row["department_id"]
        out.append(_d(
            "authority", g.id, cid=cid, type_="authority_granted",
            decided_at=row.get("granted_at"),
            author=_name(db, row.get("granted_by")),
            statement=f"{who} granted {row.get('role_label') or row.get('role')} "
                      f"authority for {dname}",
            linked={"department_id": row["department_id"],
                    "user_id": row.get("user_id")},
            realised_absent="an authority grant has no measurable outcome",
            status=(WITHDRAWN if row.get("revoked_at") else TAKEN)))
        if row.get("revoked_at"):
            out.append(_d(
                "authority_revoked", g.id, cid=cid, type_="authority_revoked",
                decided_at=row["revoked_at"],
                author=_name(db, row.get("revoked_by")),
                statement=f"{who}'s authority for {dname} revoked",
                rationale=row.get("revoke_reason"),
                linked={"department_id": row["department_id"]},
                realised_absent="a revocation has no measurable outcome"))
    return out


def src_releases(db, cid):
    """A CEO releasing a pack. ⭐ `PackRelease` WAS WRITTEN IN THIS SHAPE
    DELIBERATELY (Stage 3) so this projection reads it without translation."""
    from .pack_dist import PackRelease
    out = []
    for r in db.query(PackRelease).filter_by(cid=cid).all():
        row = {c.name: getattr(r, c.name) for c in r.__table__.columns}
        out.append(_d(
            "pack_release", r.id, cid=cid, type_="pack_released",
            decided_at=row.get("occurred_at"), author=row.get("actor_label"),
            statement=(f"Pack {row.get('pack_id')} v{row.get('pack_version')} "
                       f"released to {row.get('recipient_count')} recipient(s)"),
            rationale=row.get("note"),
            linked={"pack_id": row.get("pack_id")},
            realised_absent="a release is a distribution act with no separate "
                            "measurable outcome"))
    return out


def src_watch_decisions(db, cid):
    """What was decided in response to a threshold crossing.

    ⭐ THE ONE SOURCE WHOSE REALISED EFFECT IS RECORDED AT THE SAME PLACE AS THE
    DECISION. `WatchEvent.realised_value` was added in §7s.6 for exactly this.
    """
    from .watch import WatchEvent
    out = []
    rows = (db.query(WatchEvent).filter_by(cid=cid)
              .filter(WatchEvent.decided_at.isnot(None)).all())
    for e in rows:
        row = {c.name: getattr(e, c.name) for c in e.__table__.columns}
        realised = row.get("realised_value")
        out.append(_d(
            "watch_decision", e.id, cid=cid, type_="watch_response",
            decided_at=row.get("decided_at"),
            author=_name(db, row.get("decided_by"), row.get("actor_label") or ""),
            statement=(f"Response to {row.get('signal_label')} "
                       f"{row.get('from_band')} → {row.get('to_band')}"),
            rationale=row.get("decision_note"),
            computed_state=row.get("value"),
            linked={"watch_event_id": e.id, "signal_key": row.get("signal_key")},
            expected=row.get("equity_value_impact"),
            realised=realised,
            realised_absent=(None if realised is not None else
                             "no realised value has been recorded against this "
                             "response"),
            status=(REALISED if realised is not None else TAKEN)))
    return out


def src_assumption_edits(db, cid):
    """⭐ AN ASSUMPTION EDIT IS A DECISION, AND THE III.4 GUARD SAID SO.

    B16's `AssumptionEdit` arrived attributed, scoped and timestamped, and
    `test_every_attributed_model_is_either_a_source_or_named_not_a_decision`
    failed on it immediately — neither carried nor excluded. It is carried,
    because changing the tax rate a valuation runs on is a deliberate act with an
    actor, a reason, and a prior value: exactly the shape this record exists for.

    ⭐ AND IT IS THE ONE SOURCE WHOSE `computed_state_at_decision` IS THE THING
    THAT WAS OVERWRITTEN. `prior_value` is what the number WAS, captured because
    the edit destroys it everywhere else.
    """
    from .assumptions_api import AssumptionEdit
    out = []
    for e in db.query(AssumptionEdit).filter_by(company_id=cid).all():
        row = {c.name: getattr(e, c.name) for c in e.__table__.columns}
        prior = None if row.get("prior_absent") else row.get("prior_value")
        was = ("previously unset" if row.get("prior_absent")
               else f"was {prior}")
        line = (f"{row['field']} set to {row.get('new_value')} "
                f"({was}) by {row.get('actor_label') or 'an administrator'}")
        if row.get("bound_state") == "out_of_bounds":
            line += " — flagged outside its expected bound and stored as supplied"
        out.append(_d(
            "assumption_edit", e.id, cid=cid, type_="assumption_edited",
            decided_at=row.get("occurred_at"), author=row.get("actor_label"),
            statement=f"{row['field']} changed to {row.get('new_value')}",
            rationale=row.get("reason"),
            computed_state=prior,
            linked={"field": row["field"], "dataset_id": row.get("dataset_id")},
            expected=row.get("new_value"),
            realised_absent=("an assumption edit states a value; its effect is "
                             "the figures recomputed under it, which are not "
                             "attributable to this edit alone"),
            attribution=line))
    return out


def src_line_links(db, cid):
    """⭐ DECLARING THAT AN INITIATIVE MOVES A STATEMENT LINE IS A DECISION —
    and the III.4 guard said so before anyone argued it.

    It is a person asserting a causal claim about their own business, with a
    share attached. That is the most consequential declaration in the product:
    every equity-value attribution the bridge makes rests on it.
    """
    from .initiative_lines import InitiativeLineLink
    out = []
    for l in db.query(InitiativeLineLink).filter_by(company_id=cid).all():
        row = {c.name: getattr(l, c.name) for c in l.__table__.columns}
        share = ("no share declared" if row.get("weight") is None
                 else f"{round(row['weight'] * 100, 2)}% of the line")
        out.append(_d(
            "line_link", l.id, cid=cid, type_="initiative_line_declared",
            decided_at=row.get("declared_at"),
            author=row.get("declared_by_label"),
            statement=(f"initiative {row['initiative_id']} declared to move "
                       f"{row['statement_line']} ({share})"),
            rationale=row.get("note"),
            linked={"initiative_id": row["initiative_id"],
                    "statement_line": row["statement_line"]},
            expected=row.get("weight"),
            realised_absent=("the realised effect is the attributed movement, "
                             "which the Value Bridge computes per period and "
                             "which is not attributable to this declaration "
                             "alone"),
            status=(WITHDRAWN if row.get("revoked_at") else TAKEN),
            attribution=(f"{row.get('declared_by_label') or 'someone'} declared "
                         f"this link on "
                         f"{(row.get('declared_at') or '').__str__()[:10]}; "
                         f"{share}")))
    return out


# ⭐ THE SOURCE REGISTRY. Each entry is a READER over an existing store. Nothing
# here writes, and there is no table named `decisions`.
def src_impact_declarations(db, cid):
    """⭐⭐ B12 — A DECLARED EXPECTED IMPACT IS A COMMITMENT, AND A COMMITMENT IS A
    DECISION. The III.4 guard claimed it the moment the model landed, which is
    the guard working rather than the guard complaining.

    ⭐ AND IT IS THE ONE SOURCE WITH A REAL `expected` AND A REAL REALISED SIDE.
    Every other decision here records what someone chose; this records what they
    PROMISED, and the pack reports delivery against it — so the realised effect
    is not absent, it is the attributed movement at the declared share.
    """
    from .initiative_impact import InitiativeImpactDeclaration as D
    out = []
    for r in db.query(D).filter_by(company_id=cid).all():
        row = {c.name: getattr(r, c.name) for c in r.__table__.columns}
        amt = row.get("expected_amount")
        # ⭐ "no amount declared" is NOT "declared zero", and the statement a
        # reader sees must not collapse them.
        amount_txt = ("no amount declared" if amt is None
                      else f"{amt:,.2f}")
        by = f" by {row['expected_by']}" if row.get("expected_by") else ""
        out.append(_d(
            "impact_declaration", r.id, cid=cid,
            type_="initiative_impact_declared",
            decided_at=row.get("occurred_at"),
            author=row.get("actor_label"),
            statement=(f"initiative {row['initiative_id']} declared to deliver "
                       f"{amount_txt} on {row['statement_line']}{by}"),
            rationale=row.get("basis"),
            linked={"initiative_id": row["initiative_id"],
                    "statement_line": row["statement_line"]},
            expected=amt,
            realised_absent=(None if amt is not None else
                             "no amount was declared, so there is nothing to "
                             "deliver against — this is not an expectation of "
                             "zero"),
            status=(WITHDRAWN if (row.get("withdrawn_at")
                                  or row.get("superseded_at")) else TAKEN),
            attribution=(f"{row.get('actor_label') or 'someone'} declared this "
                         f"expected impact"),
        ))
    return out


def src_assigned_feedback(db, cid):
    """⭐⭐ §4u-c — ASSIGNING EMPLOYEE FEEDBACK TO AN INITIATIVE IS A DECISION.
    The III.4 guard claimed it the moment the model landed, and that is correct.

    ⭐⭐ AND THE STATEMENT CARRIES THE CATEGORY, NEVER THE WORDS. The ruling is
    that verbatim text does not travel into an assignment; a Decision Record that
    quoted the comment would be the leak the ruling forbids, arriving by the one
    route nobody was watching — the audit trail.
    """
    from .voice_of_employee import AssignedFeedback
    out = []
    for r in db.query(AssignedFeedback).filter_by(company_id=cid).all():
        row = {c.name: getattr(r, c.name) for c in r.__table__.columns}
        out.append(_d(
            "assigned_feedback", r.id, cid=cid,
            type_="employee_feedback_assigned",
            decided_at=row.get("occurred_at"),
            author=row.get("actor_label"),
            statement=(f"feedback in category {row['source_category']} from "
                       f"department {row['department_id']} assigned to "
                       f"initiative {row.get('initiative_id')}"),
            rationale=row.get("theme"),
            linked={"department_id": row["department_id"],
                    "initiative_id": row.get("initiative_id"),
                    "category": row["source_category"]},
            expected=None,
            realised_absent=("the effect of acting on feedback is not "
                             "attributable to the assignment alone"),
            status=(WITHDRAWN if row.get("withdrawn_at") else TAKEN),
            attribution=(f"{row.get('actor_label') or 'someone'} assigned this "
                         f"feedback category"),
        ))
    return out


def src_issue_states(db, cid):
    """⭐⭐ ACCEPTING AN ISSUE IS A DECISION, AND THE SHARPEST KIND.

    "The company has chosen to live with this" is a considered position on a
    thing that remains TRUE — an actor, a date and a note against a named
    friction. ⛔ It is precisely the act that would otherwise vanish: an issue
    routed through the initiative queue and rejected leaves "dismissed" in a
    disposition log, which records the opposite of what happened.

    ⭐ ONLY A DECIDED STATE IS CARRIED. `open` is the resting state and nobody
    decided it, so a bare unaddressed issue is authorship, not a decision.
    """
    from .accounts import Issue
    out = []
    for i in (db.query(Issue).filter_by(company_id=cid)
                .filter(Issue.status_changed_at.isnot(None)).all()):
        if i.status == "open":
            continue
        verb = ("accepted — the company has chosen to live with it, and it "
                "remains true" if i.status == "accepted"
                else f"addressed by initiative {i.initiative_id}")
        out.append(_d(
            "issue_state", i.id, cid=cid, type_=f"issue_{i.status}",
            decided_at=i.status_changed_at,
            author=None,
            actor_user_id=i.status_changed_by,
            statement=f"issue “{(i.title or '')[:120]}” {verb}",
            rationale=i.status_note))
    return out


def src_axis_links(db, cid):
    """⭐⭐ DECLARING WHAT ADDRESSES AN ASSESSMENT AXIS IS A DECISION — the same
    class as B10's line links, and the III.4 guard said so before anyone argued.

    "Our weak Operational Excellence is what this objective is for" is a person
    asserting a causal claim about their own business. It is the claim on which
    every "did the intervention move the score" reading afterwards rests, and
    without it that reading has no premise at all.
    """
    from .accounts import AxisObjectiveLink
    out = []
    for l in (db.query(AxisObjectiveLink).filter_by(company_id=cid)
                .filter(AxisObjectiveLink.revoked_at.is_(None)).all()):
        out.append(_d(
            "axis_link", l.id, cid=cid, type_="axis_objective_declared",
            decided_at=l.declared_at, author=l.declared_by_label,
            actor_user_id=l.declared_by,
            statement=(f"objective {l.obj_key} declared to address assessment "
                       f"axis {l.l1_code}"),
            rationale=l.note))
    return out


def src_raci(db, cid):
    """⭐⭐ NAMING WHO IS ACCOUNTABLE IS A DECISION, AND ARGUABLY THE PUREST ONE.

    Every other entry here records a decision ABOUT something — a figure, a link,
    a disposition. This records who ANSWERS for it. ⭐ A board asking "who owned
    this" is asking exactly this question, and before RACI the product's only
    answer was a free-text owner field with no actor and no date behind it.
    """
    from .accounts import InitiativeRaci
    out = []
    for r in (db.query(InitiativeRaci).filter_by(company_id=cid)
                .filter(InitiativeRaci.revoked_at.is_(None)).all()):
        out.append(_d(
            "raci", r.id, cid=cid, type_=f"raci_{r.role}",
            decided_at=r.declared_at, author=r.declared_by_label,
            actor_user_id=r.declared_by,
            statement=(f"{r.party} declared {r.role.upper()} on initiative "
                       f"{r.initiative_id}"),
            rationale=r.note))
    return out


SOURCES = {
    "override": src_overrides,
    "signoff": src_signoffs,
    "disposition": src_dispositions,
    "initiative": src_initiatives,
    "changeset_item": src_changeset_items,
    "authority": src_authority,
    "pack_release": src_releases,
    "watch_decision": src_watch_decisions,
    "assumption_edit": src_assumption_edits,
    "line_link": src_line_links,
    "impact_declaration": src_impact_declarations,
    "assigned_feedback": src_assigned_feedback,
    "issue_state": src_issue_states,
    "axis_link": src_axis_links,
    "raci": src_raci,
}

# ⭐ ATTRIBUTED, BUT AUTHORSHIP RATHER THAN DECISION — named with the reason,
# because a silent omission and a considered exclusion look identical.
NOT_A_DECISION = {
    # ⭐ THE GROUPING IS AN ASSERTION, NOT A JUDGEMENT ABOUT THE COMPANY. Saying
    # two comments name the same friction is editorial work on evidence; the
    # DECISION is what the company then does about the issue, which `issue_state`
    # carries. Same reasoning as the four link tables above.
    "IssueComment": "declaring two comments the same finding is editorial "
                    "grouping of evidence, not a decision about the company",
    "Objective": "authoring an objective is drafting, not deciding",
    "KeyResult": "same — the DECISION is the initiative or disposition it drives",
    "KpiPlan": "a plan row is a target, not a decision about one",
    "KpiDefinition": "defining a metric is configuration",
    "KpiInitiativeLink": "a link is a relationship, not a judgement",
    "KpiObjectiveLink": "a link is a relationship, not a judgement",
    "KrInitiativeLink": "a link is a relationship, not a judgement",
    "GoalInitiativeLink": "a link is a relationship, not a judgement",
    "Thread": "a discussion, not a resolution",
    "Document": "uploading evidence is not deciding on it",
    "FinancialDataset": "an upload is data arriving; the DECISIONS about it are "
                        "the changeset items and overrides",
    "Invite": "an invitation is access administration",
    "PilotViewer": "inviting a named pilot viewer is access administration — the "
                   "DECISION is what the pilot's own results lead the company to "
                   "do, not who was given read access to them",
    "AssessmentInvite": "an invitation is access administration",
    "InitiativeAssignment": "assignment follows the approval already carried",
    "StrategicMove": "a move in the library is an option, not a decision to take it",
    "FrontierJob": "job bookkeeping",
    "PilotCompany": "commercial lifecycle, not a company's own decision",
    "TransferOffer": "commercial lifecycle, not a company's own decision",
    "ReportIssue": "issuing a report is a publication act; the Pack release "
                   "carries the decision",
    "ReportShare": "sharing is distribution; the release carries the decision",
    "Pack": "publication is automatic and non-suppressible — by construction NOT "
            "a decision (§7s Stage 2)",
    "PackRecipient": "adding a recipient is list administration",
    "PackAutoRelease": "standing auto-release IS a decision, and is carried via "
                       "the releases it produces rather than twice",
    "Changeset": "the parent; its ITEMS carry the per-change decisions",
}


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ DECIDED BUT NOT ATTRIBUTED — reported, never inferred
# ═══════════════════════════════════════════════════════════════════════════

ATTRIBUTION_GAPS = [
    {
        "decision": "plan change (dataset payload edited in place)",
        "actor_recoverable": False,
        "evidence": ("FinancialDataset carries `uploaded_by_user_id`, which "
                     "attributes an UPLOAD. §7v added `data_written_at`, which "
                     "records WHEN a payload was rewritten in place — and no "
                     "column records WHO. The showcase backfills mutate via "
                     "flag_modified with no actor in scope at all."),
        "capture_lane": "later; not this one",
    },
    {
        "decision": "assumption change (company assumptions inside the payload)",
        "actor_recoverable": False,
        "evidence": ("Same vehicle as a plan change, and already demonstrated: "
                     "eight datasets carry `size_premium = 0.2` with "
                     "`uploaded_by_user_id`, `original_filename` and "
                     "`template_version` all null. Whether it was an error or a "
                     "deliberate entry is undetermined and unrecoverable."),
        "capture_lane": "later; not this one",
    },
    {
        "decision": "valuation-basis change",
        "actor_recoverable": False,
        "evidence": ("ValuationRun has NO actor column of any kind. §7v's "
                     "`provenance` records `basis_label` and the full input set, "
                     "so WHAT was chosen is recoverable and WHO chose it is not."),
        "capture_lane": "later; not this one",
    },
]

# ⭐ NO INFERRED ACTORS. Per the provenance law, an unrecorded fact is
# UNRECOVERABLE, not false — and attributing one of these to "the company's
# admin" because that is the only name available would put a fabricated actor
# into the diligence artefact this record exists to be.


# ═══════════════════════════════════════════════════════════════════════════
# THE PROJECTION
# ═══════════════════════════════════════════════════════════════════════════

def project(db, cid, *, start=None, end=None):
    """Every decision for a company, newest first. Reads sources in place."""
    out = []
    for name, fn in SOURCES.items():
        try:
            out.extend(fn(db, cid))
        except Exception as exc:
            # ⭐ A FAILING SOURCE IS DECLARED, NOT SKIPPED. A projection quietly
            # missing a source would under-report decisions in a diligence
            # artefact, which is the most expensive place for a plausible
            # absence.
            out.append(_d(name, 0, cid=cid, type_="source_unavailable",
                          decided_at=None, author="",
                          statement=f"decisions from '{name}' could not be read",
                          rationale=f"{type(exc).__name__}: {exc}",
                          realised_absent="the source could not be read"))
    def _key(d):
        return d["decided_at"] or ""
    out = [d for d in out if _in_window(d, start, end)]
    return sorted(out, key=_key, reverse=True)


def _in_window(d, start, end):
    when = d.get("decided_at")
    if when is None:
        return True             # undated rows are never filtered out silently
    if start is not None and when < _iso(start):
        return False
    if end is not None and when > _iso(end):
        return False
    return True


def _iso(v):
    return v.isoformat() if isinstance(v, datetime) else str(v)


def taken_in_period(decisions, start, end):
    """Decisions taken this period."""
    return [d for d in decisions
            if d.get("decided_at") and _iso(start) <= d["decided_at"] <= _iso(end)]


def realised_from_earlier(decisions, start):
    """⭐ THE COMPOUNDING HALF: decisions taken in EARLIER periods whose effect is
    now measurable. Invisible in month one by construction — a design judged on
    its first pack will undervalue it."""
    return [d for d in decisions
            if d.get("realised_effect") is not None
            and d.get("decided_at") and d["decided_at"] < _iso(start)]


def unmeasured(decisions):
    """Decisions whose effect is not yet measurable. ⭐ A LEGITIMATE STATE, not a
    gap to fill — and counted, so a reader can see how much is still open."""
    return [d for d in decisions if d.get("realised_effect") is None]
