"""CXO metric overrides — the immutable data model and the read path (§4x Stage 1).

THE NON-NEGOTIABLE LINE. A CXO may override the DISPLAYED figure. AXIOM's
computed value is never destroyed, is always available beside it, and the fact
of authorship is always visible. That line is what makes this trust-building
(the CFO's owned, signed, defensible numbers) rather than number-laundering
(silent edits that eventually destroy board trust in AXIOM).

Stage 1 builds the model and the resolver ONLY. There is deliberately no write
endpoint: the provenance-travel property has to be proven before anyone can
create an override through the product.

DEFAULT-NO-CHANGE IS THE RESTING STATE. With zero override rows every surface
behaves exactly as it did before this module existed — same values, and no
attribution anywhere, because there is nothing to attribute. `resolve_many`
short-circuits on an empty query, so the cost of the feature to a company that
never uses it is one indexed SELECT returning nothing.

WHAT THE SCHEMA GUARANTEES, as opposed to what code remembers to do:
  * author_user_id, author_label, reason_category, override_value and
    computed_value_at_override are all NOT NULL. An unattributed or unreasoned
    override cannot be represented. This is the anti-laundering guarantee, and
    it is enforced by the database rather than by a validator someone can
    bypass with a direct insert.
  * There is no UPDATE path. A change is a NEW ROW; the prior row is marked
    superseded and keeps its own author, reason and timestamp. Editing an
    override in place would destroy the audit trail of the override itself,
    which is a different immutability violation from destroying the computed
    value and no less damaging in front of a board.
  * computed_value_at_override is a SNAPSHOT, not a mirror. The dataset can be
    re-uploaded; what AXIOM said AT THE MOMENT the CXO overrode it is a
    permanent fact about that decision and cannot be re-derived later.

Persistence rides accounts.py's Base/engine (ax_* tables, auto-created by
`Base.metadata.create_all` at boot — no Alembic for new ax_ tables).
"""
from datetime import datetime

import re

import json

from sqlalchemy import (Boolean, CheckConstraint, Column, DateTime, Index,
                        Integer, JSON, String, Text, text)

from .accounts import Base, Department, Membership

# ── reason categories (§4l B.5, amended by user ruling 27 Jul) ───────────────
# `private_info` REMOVED. Combined with a nullable reason_note it let an override
# tell a board: this number was changed, by the CFO, for reasons we are not
# giving. That is attributed number-laundering — the attribution is real and the
# reason is a refusal to give one — and it would have been the most-selected
# category precisely because it demanded nothing.
#
# Every remaining category is substantive and stateable, which is what lets
# reason_note stay nullable per B.5: with the laundering option gone, the
# category alone IS an explanation. "Wrong input data" tells a reader where the
# defect is; "private CXO information" tells them only that they may not ask.
#
# The four that remain also each name a place a fix belongs, which is what Stage
# 3's reason-routing acts on. A category that routes nowhere was never carrying
# its weight.
REASON_CATEGORIES = ("calc_error", "data_error", "definition", "other")

REASON_LABEL = {
    "calc_error": "calculation error",
    "data_error": "wrong input data",
    "definition": "definition disagreement",
    "other": "other",
}

# SQL-side form, so a DIRECT INSERT cannot resurrect the removed value. The
# write path is not the only way rows arrive.
_REASON_SQL_CHECK = "reason_category IN ('calc_error','data_error','definition','other')"

# ── target scopes — ONLY what the resolver actually covers (Stage 1b item 3) ──
# `enterprise` was representable and UNRESOLVED. Determined empirically:
# resolve_many() has exactly one call site, _serialize_kpis, whose refs are built
# by _kpi_scope_key(department_id, name). No enterprise surface — kpi_strip,
# CEI, valuation — passes through the resolver at all. An enterprise-scope row
# was therefore storable, would satisfy every NOT NULL constraint, and would
# change nothing on any screen: an override the author believes is in force and
# that silently is not. That is the same leak as a bare figure, at a
# higher-visibility surface, so the scope is REMOVED until its read path exists.
TARGET_SCOPES = ("department",)

# ── metric_ref whitelist (Stage 1b item 2) — LOAD-BEARING, not precautionary ──
# The resolver covers department KPIs and nothing else. `kpi_strip` financial
# KPIs DO reach reports, PDF and Ask AXIOM as rendered numbers, and they do NOT
# pass through the resolver — so an override targeting one of them would render
# a bare adjusted figure in a board PDF. The export disclosure section is not
# cover for that: it discloses that SOME figure was adjusted, while the figure
# itself is printed elsewhere on the page with no marker.
#
# Fail closed: a ref that does not match a covered kind is refused at BOTH the
# schema (CheckConstraint below) and the write path (validate_new).
METRIC_KINDS = {
    # Department KPI. Exactly the shape _kpi_scope_key emits:
    # "{department_id}|{normalised name}", with 0 as the null-department sentinel.
    "dept_kpi": re.compile(r"^\d+\|.+$"),
}
# SQL-side form of the same rule. Deliberately simple and PORTABLE (SQLite and
# Postgres both honour LIKE): the schema check is the backstop against a direct
# INSERT, not the full validation. A dialect-specific GLOB would silently become
# a no-op on the other engine, which is the worst outcome for a fail-closed
# guard — present in the DDL, enforcing nothing.
_METRIC_REF_SQL_CHECK = "metric_ref LIKE '%|%'"


def metric_kind(metric_ref: str) -> str | None:
    """Which resolver-covered kind this ref is, or None if it is not covered."""
    for kind, pat in METRIC_KINDS.items():
        if pat.match(metric_ref or ""):
            return kind
    return None


def is_resolver_covered(metric_ref: str) -> bool:
    return metric_kind(metric_ref) is not None


class MetricOverride(Base):
    """An attributed layer OVER a computed value. Never a destructive write.

    The live computed value stays exactly where it always was — KpiPlan.ytd_actual
    and its siblings are untouched by this table's existence, and every existing
    reader of them still returns the same number. This row records that someone
    asserts a different DISPLAY value, who they are, why, and what AXIOM said at
    the time.
    """
    __tablename__ = "ax_metric_overrides"
    __table_args__ = (
        # ── AT MOST ONE ACTIVE OVERRIDE PER METRIC (Stage 1b items 1 + 2) ─────
        # This was a UniqueConstraint(company_id, metric_ref, superseded_at) and
        # it enforced NOTHING on the rows that matter. SQL treats NULLs as
        # distinct, so every active row (superseded_at IS NULL) inserted
        # cleanly; two consecutive INSERTs on one metric_ref both committed and
        # the active count came back 2. The resolver's .first() would then pick
        # arbitrarily between two contradictory live assertions about the same
        # board figure.
        #
        # THE SAME TRAP _kpi_scope_key ALREADY DEFENDS AGAINST with its literal
        # 0 sentinel for a null department_id — known, written down in this
        # codebase, and reintroduced one table later. Rule, generally: any
        # uniqueness key containing a nullable column is wrong by default.
        #
        # A PARTIAL UNIQUE INDEX fixes it properly: the predicate restricts the
        # index to active rows, so supersession still releases the slot and
        # history still accumulates, but two live assertions cannot coexist.
        # department_id is in the key (item 2) so two departments cannot collide
        # or resolve ambiguously on the same metric_ref, and target_scope is
        # there so a future scope cannot silently share a slot with this one.
        Index("uq_active_metric_override",
              "company_id", "target_scope", "department_id", "metric_ref",
              unique=True,
              sqlite_where=text("superseded_at IS NULL"),
              postgresql_where=text("superseded_at IS NULL")),
        Index("ix_override_lookup", "company_id", "superseded_at"),
        # ── fail-closed schema backstops ─────────────────────────────────────
        # These bind a DIRECT INSERT, which is the whole point: validate_new()
        # protects the write path, and the write path is not the only way rows
        # arrive (a migration, a console session, a future importer).
        CheckConstraint(_METRIC_REF_SQL_CHECK, name="ck_override_metric_ref_shape"),
        CheckConstraint(_REASON_SQL_CHECK, name="ck_override_reason_category"),
        CheckConstraint("target_scope = 'department'", name="ck_override_scope"),
        # department_id is nullable in the column definition only because the
        # enterprise scope once existed. With that scope removed there is no
        # legitimate NULL, and a NULL here would also re-open the uniqueness
        # hole above by making the index key non-comparable.
        CheckConstraint("department_id IS NOT NULL", name="ck_override_has_department"),
    )
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)

    # ── target ────────────────────────────────────────────────────────────────
    # scope + department_id together define WHOSE number this is, which is what
    # the authority rule is checked against. department_id is NULL only for
    # enterprise-scope overrides.
    target_scope = Column(String(16), nullable=False)          # enterprise | department
    department_id = Column(Integer, index=True, nullable=True)
    # Stable metric identity. For department KPIs this is the existing
    # _kpi_scope_key shape ("{department_id}|{normalised name}"), already proven
    # alias-stable across renames by the §4m linkage lane — a name-keyed ref
    # would orphan the moment a KPI or department is renamed, which is exactly
    # how an override could silently detach from the number it explains.
    metric_ref = Column(String(200), nullable=False)
    metric_label = Column(String(300), nullable=True)          # human-readable, for the audit export

    # ── the assertion — every column NOT NULL, by design ──────────────────────
    override_value = Column(JSON, nullable=False)
    computed_value_at_override = Column(JSON, nullable=False)
    reason_category = Column(String(24), nullable=False)
    reason_note = Column(Text, nullable=True)                  # free text is optional; the CATEGORY is not

    # ── authorship — frozen, never a join ─────────────────────────────────────
    # author_label is stored text rather than resolved at read time: titles
    # change and people leave, and a board reading a two-year-old figure needs
    # "CFO — J. Chen" AS IT WAS THEN. A live join would silently relabel history.
    author_user_id = Column(Integer, nullable=False)
    author_label = Column(String(160), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── supersession — the append-only mechanism ──────────────────────────────
    superseded_at = Column(DateTime, nullable=True)            # NULL = active
    superseded_by_id = Column(Integer, nullable=True)
    # Why it stopped applying: superseded (a newer assertion) or withdrawn (the
    # CXO retracted it). A withdrawn override still exists in the trail — "this
    # was adjusted and then un-adjusted" is itself board-relevant.
    supersession_kind = Column(String(16), nullable=True)      # superseded | withdrawn


def ensure_override_schema(engine):
    """Rebuild ax_metric_overrides if it predates the partial unique index.

    create_all() never ALTERs an existing table, so the Stage 1 DDL — carrying
    the non-binding UniqueConstraint and no CheckConstraints — would survive
    unchanged on an already-deployed database. The guard that matters would then
    exist in the model and not in the database.

    REBUILD, NOT PATCH, and only when the table is EMPTY. A destructive path is
    acceptable here for exactly one reason, which is checked rather than
    assumed: Stage 1 shipped no write endpoint, so there is no way rows could
    exist. If any row is present the rebuild is REFUSED and the condition is
    raised — better a loud failure at boot than a silent drop of the one table
    whose entire purpose is being an immutable audit trail.
    """
    from sqlalchemy import inspect as _inspect
    insp = _inspect(engine)
    if not insp.has_table("ax_metric_overrides"):
        return {"action": "none", "reason": "table does not exist yet"}

    # EVERY guard, not just the first one added. The initial version of this
    # function checked only for the partial index — so when the reason-category
    # CheckConstraint landed a commit later, the table already had the index,
    # the rebuild was skipped, and the new constraint never reached the
    # database. It existed in the model and enforced nothing, which is the exact
    # failure mode Stage 1b item 1 was about. Caught by a test that inserted the
    # forbidden value and saw it commit.
    #
    # So: name every guard that must be present, and rebuild if ANY is missing.
    required_indexes = {"uq_active_metric_override"}
    required_checks = {"ck_override_metric_ref_shape", "ck_override_scope",
                       "ck_override_has_department", "ck_override_reason_category"}
    have_idx = {i["name"] for i in insp.get_indexes("ax_metric_overrides")}
    try:
        have_chk = {c["name"] for c in insp.get_check_constraints("ax_metric_overrides")}
    except NotImplementedError:
        have_chk = set()          # dialect cannot introspect; index check still applies
    missing = (required_indexes - have_idx) | (required_checks - have_chk)
    if not missing:
        return {"action": "none", "reason": "all guards present"}
    with engine.begin() as conn:
        n = conn.exec_driver_sql("SELECT COUNT(*) FROM ax_metric_overrides").scalar()
        if n:
            raise RuntimeError(
                f"ax_metric_overrides holds {n} row(s) but is missing guards "
                f"{sorted(missing)}. Refusing to rebuild: this table is an "
                f"immutable audit trail and must be migrated deliberately, not "
                f"dropped.")
        conn.exec_driver_sql("DROP TABLE ax_metric_overrides")
    MetricOverride.__table__.create(engine)
    return {"action": "rebuilt", "rows_preserved": 0, "was_missing": sorted(missing)}


# ── the grant model (§4x §7, Stage 2) ────────────────────────────────────────

class DepartmentAuthority(Base):
    """Who may speak for a department. §4x §7, built to the locked design.

    GRANTS ARE ROWS, NOT A ROLE FIELD (§7.2). Each grant carries its own
    lifecycle — granted_by, granted_at, revoked_at — and REVOCATION IS A
    TIMESTAMP, NOT A DELETION. Two consequences fall out for free rather than
    needing code: history is untouched BY CONSTRUCTION, and one person holding
    several departments (§7.3) is simply several rows, so revoking one cannot
    disturb another.

    ⭐ REVOCATION NEVER TOUCHES HISTORY (§7.4). Nothing here cascades. Past
    sign-offs and overrides keep their frozen author_label exactly as made. A
    board figure that LOSES its attester is worse than one that never had an
    attester — the first reads as covered-up authorship, the second merely as
    unsigned. Test-pinned behaviourally: revoke, then assert prior rows are
    byte-identical.

    NO UNIQUE CONSTRAINT ON (company, user, department). Deliberate: the same
    person may be granted a department, revoked, and granted again later, and
    each of those is a distinct historical fact. The ACTIVE-row uniqueness that
    matters is enforced by grant_department() refusing to issue a second live
    grant, not by a constraint that would also forbid the history.
    """
    __tablename__ = "ax_department_authority"
    __table_args__ = (
        Index("ix_dept_authority_lookup", "company_id", "user_id",
              "department_id", "revoked_at"),
    )
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    department_id = Column(Integer, index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    # cxo | delegate. Reserved for §7.5's "then CHRO" display: the title is
    # frozen at grant time for the same reason author_label is frozen on an
    # override — a board reading a two-year-old sign-off needs the role AS IT
    # WAS, not as the org chart is now.
    role = Column(String(24), default="cxo", nullable=False)
    role_label = Column(String(160), nullable=True)
    granted_by = Column(Integer, nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(Integer, nullable=True)
    revoke_reason = Column(String(32), nullable=True)   # replaced | departed | corrected


# Fill the slot Stage 1 already reads. department_authority() looks this up on
# Base and fails closed when absent — it is now present, so the fail-closed
# default becomes a real lookup without that function changing.
Base._department_authority_model = DepartmentAuthority


class GrantError(Exception):
    """Refused grant/revoke. Distinct from AuthorityError, which is about
    EXERCISING authority; this is about ISSUING it."""


def grant_department(db, company_id, department_id, *, user_id, granted_by,
                     role="cxo", role_label=None, actor=None):
    """Issue a grant. §7.1: THE COMPANY ADMIN GRANTS.

    `actor` is the granting user, checked so the admin-may-grant-but-never-
    exercise rule cannot be inverted by a caller that forgets it. Platform staff
    are refused here too — being unable to AUTHOR is worthless if we can grant
    ourselves authority a moment earlier.
    """
    if actor is not None and getattr(actor, "is_staff", False):
        raise GrantError(
            "Platform staff cannot issue department authority — granting is how "
            "authoring is obtained, so the exclusion has to hold at both steps.")
    dep = db.get(Department, department_id)
    if dep is None or dep.company_id != company_id:
        raise GrantError("That department does not belong to this company.")
    live = (db.query(DepartmentAuthority)
              .filter_by(company_id=company_id, department_id=department_id,
                         user_id=user_id, revoked_at=None).first())
    if live:
        return live                       # idempotent: re-granting is a no-op
    row = DepartmentAuthority(
        company_id=company_id, department_id=department_id, user_id=user_id,
        role=role, role_label=role_label, granted_by=granted_by)
    db.add(row)
    db.flush()
    return row


def revoke_department(db, company_id, department_id, *, user_id, revoked_by,
                      reason="departed", now=None):
    """Retire a grant. §7.4: A TIMESTAMP, NOT A DELETION.

    Touches the grant row and NOTHING ELSE — no cascade to sign-offs, no cascade
    to overrides. That is the whole point, and it is a property of what this
    function does not do."""
    row = (db.query(DepartmentAuthority)
             .filter_by(company_id=company_id, department_id=department_id,
                        user_id=user_id, revoked_at=None).first())
    if row is None:
        raise GrantError("No live grant to revoke.")
    row.revoked_at = now or datetime.utcnow()
    row.revoked_by = revoked_by
    row.revoke_reason = reason
    db.flush()
    return row


def grants_for(db, company_id, *, department_id=None, user_id=None,
               include_revoked=False):
    q = db.query(DepartmentAuthority).filter_by(company_id=company_id)
    if department_id is not None:
        q = q.filter_by(department_id=department_id)
    if user_id is not None:
        q = q.filter_by(user_id=user_id)
    if not include_revoked:
        q = q.filter(DepartmentAuthority.revoked_at.is_(None))
    return q.order_by(DepartmentAuthority.granted_at.asc()).all()


def department_state(db, company_id, department_id):
    """§7.6: VACANT and UNSIGNED are DIFFERENT STATES and must render
    differently. This is the source of that distinction — a department with
    nobody accountable is not a department whose CXO simply has not acted yet,
    and an unsigned dashboard identical in both cases silently converts an
    organisational gap into an apparent individual failure."""
    live = grants_for(db, company_id, department_id=department_id)
    if live:
        return {"state": "assigned", "holders": len(live),
                "user_ids": [g.user_id for g in live]}
    ever = grants_for(db, company_id, department_id=department_id,
                      include_revoked=True)
    if ever:
        last = max(ever, key=lambda g: g.revoked_at or g.granted_at)
        return {"state": "vacant", "holders": 0,
                "since": last.revoked_at.isoformat() if last.revoked_at else None,
                "reason": last.revoke_reason}
    return {"state": "never_assigned", "holders": 0}


# ── sign-off (§4x §7, Stage 2 of 4) ──────────────────────────────────────────

class DashboardSignoff(Base):
    """A CXO's attestation to a department dashboard AS SHOWN.

    Sign-off is the CXO's primary action: REVIEW THEN ATTEST, one act. It is not
    editing — the override write path is a separate thing, and a signature that
    doubled as an edit would make "the CFO's owned number" mean two different
    claims at once.

    ⭐ WHAT IT PERSISTS, AND WHY THE OBVIOUS SHAPE WOULD BLOCK STAGE 4.
    The natural design is a digest: hash the signed figures, compare later,
    invalidate on mismatch. That is enough for §8.1 (did anything change?) and
    NOT enough for §8.3 (show which values changed and by how much). A digest
    answers "something moved"; the re-sign-off diff has to answer "these three
    moved, by this much". Storing only a digest would mean stage 4 could not be
    built without a migration — and worse, without the PRE-CHANGE VALUES, which
    by then would be unrecoverable because the whole point is that they changed.

    So the signature persists BOTH:
      * `signed_state` — the actual displayed values at sign time, per metric,
        including each one's provenance. This is what the stage-4 diff is
        computed against.
      * `state_digest` — sha256 over the same, for cheap change detection
        without loading the snapshot.

    §8.2 — THE DEPENDENCY SET IS COMPUTED, NEVER HAND-MAINTAINED. `signed_state`
    is built by `signed_dashboard_state()`, which reads the SAME serializer the
    dashboard renders from. A hand-listed set of "things that invalidate" would
    be correct the day it was written and silently stale after the next panel is
    added — the defect class already recorded twice in this ledger.

    §7.5 — signer_label is FROZEN TEXT, never a join. A board reading a
    two-year-old sign-off needs "CFO — J. Chen" and the role AS IT WAS
    ("then CHRO"), not as the org chart is now.
    """
    __tablename__ = "ax_dashboard_signoffs"
    __table_args__ = (
        # One ACTIVE signature per department. Same partial-index discipline as
        # the override table — a plain unique constraint including the nullable
        # superseded column would enforce nothing on live rows.
        Index("uq_active_signoff", "company_id", "department_id", unique=True,
              sqlite_where=text("superseded_at IS NULL"),
              postgresql_where=text("superseded_at IS NULL")),
        Index("ix_signoff_lookup", "company_id", "superseded_at"),
    )
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    department_id = Column(Integer, index=True, nullable=False)

    # WHO — frozen at signature time (§7.5)
    signer_user_id = Column(Integer, nullable=False)
    signer_label = Column(String(160), nullable=False)      # "J. Chen"
    signer_role_label = Column(String(160), nullable=True)  # "CHRO" -> "then CHRO"
    grant_id = Column(Integer, nullable=True)               # the grant relied on

    # WHEN
    signed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # WHAT — the dashboard state attested to
    dataset_id = Column(Integer, nullable=True)
    signed_state = Column(JSON, nullable=False)
    state_digest = Column(String(64), nullable=False)
    # Derived, never self-declared: true when any displayed value carried an
    # override at signature time.
    with_adjustments = Column(Boolean, default=False, nullable=False)

    # Supersession — a re-signature never overwrites its predecessor.
    superseded_at = Column(DateTime, nullable=True)
    superseded_by_id = Column(Integer, nullable=True)


def signed_dashboard_state(db, company_id, department_id):
    """The dependency set: the values the dashboard DISPLAYS, from the resolver.

    §8.1 scopes invalidation to displayed values and nothing else — too broad
    and executives re-sign for reasons they cannot see, which destroys the
    feature more quietly than a bug would; too narrow and a signed number
    changes silently. §8.2 requires that set be DERIVED. This reads
    `company_kpi_variance`, the one serializer the department dashboard renders
    from, so the set cannot drift as the dashboard grows.
    """
    from .accounts import company_kpi_variance
    out = {}
    payload = company_kpi_variance(company_id, department=department_id,
                                   member=None, db=db)
    for k in payload.get("kpis", []):
        prov = k.get("provenance_override")
        out[str(k.get("id"))] = {
            "metric": k.get("kpi_name"),
            "display": k.get("ytd_actual"),
            "plan": k.get("ytd_plan"),
            "target": k.get("full_year_target"),
            "variance": (k.get("variance") or {}).get("status"),
            "adjusted": bool(prov),
            "computed": (prov or {}).get("computed_value"),
            "adjusted_by": (prov or {}).get("adjusted_by"),
        }
    return {"dataset_id": payload.get("dataset_id"), "metrics": out}


def state_digest(state) -> str:
    """Stable hash of the signed state. Sorted keys so an unrelated ordering
    change cannot read as a data change and trigger a spurious re-sign-off —
    §8.1's too-broad failure, which trains executives to click without
    reviewing."""
    import hashlib
    return hashlib.sha256(
        json.dumps(state, sort_keys=True, default=str).encode()).hexdigest()


def sign_off(db, company_id, department_id, *, user, signer_label,
             signer_role_label=None, now=None):
    """Attest to the dashboard as shown. AUTHORITY-CHECKED — can_author() is the
    same gate the override write path uses, so a signature and an adjustment can
    never disagree about who may act on a department."""
    can_author(db, company_id, user, "department", department_id)   # raises
    grants = grants_for(db, company_id, department_id=department_id,
                        user_id=getattr(user, "id", None))
    state = signed_dashboard_state(db, company_id, department_id)
    prev = active_signoff(db, company_id, department_id)
    ts = now or datetime.utcnow()
    if prev is not None:
        prev.superseded_at = ts
        db.flush()
    row = DashboardSignoff(
        company_id=company_id, department_id=department_id,
        signer_user_id=user.id, signer_label=signer_label,
        signer_role_label=signer_role_label or (grants[0].role_label if grants else None),
        grant_id=(grants[0].id if grants else None),
        signed_at=ts, dataset_id=state.get("dataset_id"),
        signed_state=state, state_digest=state_digest(state),
        with_adjustments=any(m.get("adjusted") for m in state["metrics"].values()))
    db.add(row); db.flush()
    if prev is not None:
        prev.superseded_by_id = row.id
        db.flush()
    return row


def active_signoff(db, company_id, department_id):
    return (db.query(DashboardSignoff)
              .filter_by(company_id=company_id, department_id=department_id)
              .filter(DashboardSignoff.superseded_at.is_(None)).first())


def signoff_state(db, company_id, department_id):
    """⭐ THREE STATES AT THE DATA LAYER, not a boolean (§7.6).

    `signed` / `unsigned` / `vacant` are distinct facts and must be
    distinguishable without inference. The vacancy-versus-unsigned pair is the
    one whose failure is SILENT and visually similar: both are "no signature",
    and an unsigned dashboard that renders identically in both cases converts an
    organisational gap into an apparent individual failure — it reads as
    executive inattention when the real condition is an unfilled role.

    So the distinction is produced here, from the grant state, rather than left
    to a caller to derive from a null signature.
    """
    dep_state = department_state(db, company_id, department_id)
    sig = active_signoff(db, company_id, department_id)
    if sig is not None:
        return {
            "state": "signed_with_adjustments" if sig.with_adjustments else "signed",
            "signed": True,
            "signer": sig.signer_label,
            "signer_role": sig.signer_role_label,
            "signed_at": sig.signed_at.isoformat() if sig.signed_at else None,
            "with_adjustments": bool(sig.with_adjustments),
            "signoff_id": sig.id,
            # §7.5 — the board-visible artifact, with the role AS IT WAS.
            "attestation": _attestation_line(sig),
            "authority": dep_state["state"],
        }
    if dep_state["state"] in ("vacant", "never_assigned"):
        return {
            "state": "vacant", "signed": False,
            "authority": dep_state["state"],
            "since": dep_state.get("since"),
            "reason": dep_state.get("reason"),
            # Named explicitly so no surface has to infer it from a null.
            "note": ("No CXO is assigned to this department, so there is no one "
                     "to sign off. This is not an unsigned dashboard."),
        }
    return {
        "state": "unsigned", "signed": False, "authority": dep_state["state"],
        "note": "Assigned but not yet signed off.",
    }


def _attestation_line(sig) -> str:
    """The board-visible artifact. §7.5: a signer since moved renders as
    "then CHRO", because without it a CEO wonders why the head of Operations
    signed HR's numbers — the attestation looks wrong precisely because the
    display shows today's org chart against a historical act."""
    when = sig.signed_at.strftime("%d %b %Y") if sig.signed_at else "unknown date"
    role = f", then {sig.signer_role_label}" if sig.signer_role_label else ""
    adj = " (with adjustments)" if sig.with_adjustments else ""
    return f"Signed off by {sig.signer_label}{role}, {when}{adj}"


# ── the read path ────────────────────────────────────────────────────────────

class Resolved:
    """{computed_value, override?} — value and provenance as ONE unit.

    Deliberately not a bare number and deliberately not a dict: a surface that
    wants to render this has to go through `.display` (the number to show) and
    can reach `.attribution` for free, but there is no attribute that yields an
    overridden figure stripped of its authorship. Losing the label on any
    surface is the failure mode this whole feature exists to prevent, so the
    return type is shaped to make it awkward rather than trusting 19 call sites
    to remember.
    """
    __slots__ = ("computed", "override")

    def __init__(self, computed, override=None):
        self.computed = computed
        self.override = override

    @property
    def overridden(self) -> bool:
        return self.override is not None

    @property
    def display(self):
        """The number a surface should render. Identical to `computed` when
        there is no override — that is the whole of default-no-change."""
        return self.override.override_value if self.override else self.computed

    @property
    def attribution(self) -> dict | None:
        """None when nothing was overridden, so a surface that spreads this into
        its payload adds no keys at all in the default case."""
        o = self.override
        if o is None:
            return None
        return {
            "adjusted": True,
            "adjusted_by": o.author_label,
            "reason_category": o.reason_category,
            "reason_label": REASON_LABEL.get(o.reason_category, o.reason_category),
            "reason_note": o.reason_note,
            "adjusted_at": o.created_at.isoformat() if o.created_at else None,
            "computed_value": o.computed_value_at_override,
            "override_id": o.id,
        }

    def to_dict(self, value_key: str = "value") -> dict:
        """Serialize value + provenance together. With no override this is a
        single key and the payload is byte-identical to what it was before."""
        out = {value_key: self.display}
        if self.override is not None:
            out["provenance"] = self.attribution
        return out

    def sentence(self, label: str) -> str:
        """One line stating both figures, for surfaces that emit prose rather
        than JSON — Ask AXIOM's context and the export disclosure. A surface
        that can only render text must still be unable to state an overridden
        number as bare fact."""
        if self.override is None:
            return f"{label}: {self.computed}"
        o = self.override
        return (f"{label}: {o.override_value} — ADJUSTED by {o.author_label} "
                f"({REASON_LABEL.get(o.reason_category, o.reason_category)}"
                f"{'; ' + o.reason_note if o.reason_note else ''}); "
                f"AXIOM computed {o.computed_value_at_override}.")


def _active_q(db, company_id: int):
    return (db.query(MetricOverride)
              .filter(MetricOverride.company_id == company_id,
                      MetricOverride.superseded_at.is_(None)))


def resolve_many(db, company_id: int, computed: dict) -> dict:
    """{metric_ref: computed_value} -> {metric_ref: Resolved}.

    ONE query for the whole page rather than one per metric — a resolver that
    costs a round trip per KPI would tempt call sites into skipping it for the
    "hot" paths, and a resolver that is skipped anywhere is not a guarantee.

    With no overrides on the company this returns Resolved(computed) for every
    key, whose .display IS the computed value and whose .attribution is None.
    """
    if not computed:
        return {}
    rows = {}
    for o in _active_q(db, company_id).filter(
            MetricOverride.metric_ref.in_(list(computed.keys()))).all():
        rows[o.metric_ref] = o
    return {ref: Resolved(val, rows.get(ref)) for ref, val in computed.items()}


def resolve_one(db, company_id: int, metric_ref: str, computed) -> Resolved:
    o = _active_q(db, company_id).filter(
        MetricOverride.metric_ref == metric_ref).first()
    return Resolved(computed, o)


def active_overrides(db, company_id: int, department_id: int | None = None):
    """Every live override, for the export disclosure and the audit view."""
    q = _active_q(db, company_id)
    if department_id is not None:
        q = q.filter(MetricOverride.department_id == department_id)
    return q.order_by(MetricOverride.created_at.desc()).all()


def has_any_override(db, company_id: int) -> bool:
    """Cheap gate so a surface can skip its disclosure section entirely when
    there is nothing to disclose — default-no-change, visibly."""
    return _active_q(db, company_id).first() is not None


# ── authority ────────────────────────────────────────────────────────────────
# Modelled and tested now, enforced at the Stage 2 write path. Defining the rule
# before the write endpoint exists is the point: retrofitting authority after
# overrides are already authored means migrating figures with no way to know who
# was entitled to write them.

class AuthorityError(Exception):
    """Raised when an author is not entitled to override the target."""


def department_authority(db, company_id: int, user_id: int, department_id: int) -> bool:
    """Is this user the CXO of THIS department?

    EXPLICIT GRANT ONLY — deliberately NOT an email match against
    Department.head_email. _on_behalf_suffix matches head by email string, which
    is fine for a LABEL and unacceptable for a PERMISSION: an admin editing a
    department's head email would silently transfer the right to author board
    figures. Stage 2 adds ax_department_authority rows; until it exists this
    returns False for everyone, which fails closed — no one can author anything.
    """
    grant = getattr(Base, "_department_authority_model", None)
    if grant is None:
        return False                      # Stage 2 not yet built: fail closed
    row = (db.query(grant)
             .filter_by(company_id=company_id, user_id=user_id,
                        department_id=department_id, revoked_at=None).first())
    return row is not None


def can_author(db, company_id: int, user, target_scope: str, department_id: int | None):
    """THE AUTHORITY RULE. A CFO must not be able to override HR's numbers.

    Three refusals, each deliberate:

    1. NO CROSS-DEPARTMENT AUTHORING. Authority is granted per department; being
       the CXO of Finance says nothing about HR. This is the requirement the
       §4l spec omitted entirely and the one most likely to be discovered by a
       customer rather than by us.

    2. COMPANY ADMIN CANNOT AUTHOR. An admin may GRANT authority but never
       exercise it — otherwise "the CFO's owned number" is unfalsifiable,
       because an admin could have written it under the CFO's name.

    3. PLATFORM STAFF ARE EXCLUDED, explicitly, even though the operator bypass
       grants them require_company_admin everywhere else. We must never be able
       to author a customer's signed board figure; that would be indefensible
       if discovered, whatever the intent.
    """
    if getattr(user, "is_staff", False) or getattr(user, "_operator_bypass", False):
        raise AuthorityError(
            "Platform staff cannot author a customer's override — the figure "
            "must be the executive's own.")
    if target_scope not in TARGET_SCOPES:
        # `enterprise` lands here now (Stage 1b item 3). It is refused for a
        # reason worth stating in the error rather than a bare "unknown scope":
        # nothing on an enterprise surface passes through the resolver, so such
        # an override would store cleanly, satisfy every NOT NULL column, be
        # believed in force by its author, and change nothing anyone can see.
        raise AuthorityError(
            f"Unsupported target scope {target_scope!r}; only {TARGET_SCOPES} "
            f"have a read path that resolves.")
    if department_id is None:
        raise AuthorityError("A department-scope override needs a department.")
    dep = db.get(Department, department_id)
    if dep is None or dep.company_id != company_id:
        raise AuthorityError("That department does not belong to this company.")
    if not department_authority(db, company_id, user.id, department_id):
        raise AuthorityError(
            f"Not authorised to override {dep.name}'s figures. Department "
            f"overrides may be authored only by that department's CXO.")
    return True


def validate_new(*, override_value, computed_value, reason_category, author_label,
                 metric_ref=None, target_scope="department", department_id=None):
    """What the DB constraints cannot express in full: category membership, a
    non-whitespace label, and — the load-bearing one — that the metric is
    actually covered by the resolver.

    Called by the Stage 2 write path. Defined here so the rule lives with the
    model it protects rather than in the endpoint that happens to call it first.
    """
    if override_value is None:
        raise ValueError("override_value is required — an override with no value is not one.")
    if computed_value is None:
        raise ValueError(
            "computed_value_at_override is required — without it the audit trail "
            "cannot say what AXIOM had said, which is the whole point of keeping it.")
    if reason_category not in REASON_CATEGORIES:
        raise ValueError(f"reason_category must be one of {REASON_CATEGORIES}.")
    if not (author_label or "").strip():
        raise ValueError("author_label is required — an override cannot be anonymous.")
    if target_scope not in TARGET_SCOPES:
        raise ValueError(
            f"target_scope must be one of {TARGET_SCOPES}. `enterprise` is not "
            f"accepted: no enterprise surface passes through the resolver, so "
            f"such an override would be stored, believed to be in force, and "
            f"change nothing on any screen.")
    if department_id is None:
        raise ValueError("department_id is required — every override is department-scoped.")
    # THE WHITELIST. Refusing here is what prevents an override on a kpi_strip
    # metric, which would render as a bare adjusted figure in a board PDF
    # because that family never passes through the resolver.
    if not is_resolver_covered(metric_ref or ""):
        raise ValueError(
            f"metric_ref {metric_ref!r} is not a resolver-covered metric. Only "
            f"department KPIs resolve today; overriding anything else would "
            f"produce an adjusted figure with no provenance marker on the "
            f"surfaces that render it.")
    return True


# ── audit export ─────────────────────────────────────────────────────────────

def audit_rows(db, company_id: int, include_superseded: bool = True) -> list[dict]:
    """The board-defensibility record. Every override that has EVER existed by
    default — an audit trail that shows only current state is not one."""
    q = db.query(MetricOverride).filter_by(company_id=company_id)
    if not include_superseded:
        q = q.filter(MetricOverride.superseded_at.is_(None))
    out = []
    for o in q.order_by(MetricOverride.created_at.asc()).all():
        out.append({
            "override_id": o.id,
            "scope": o.target_scope,
            "department_id": o.department_id,
            "metric_ref": o.metric_ref,
            "metric": o.metric_label,
            "computed_value": o.computed_value_at_override,
            "displayed_value": o.override_value,
            "reason_category": o.reason_category,
            "reason_label": REASON_LABEL.get(o.reason_category),
            "reason_note": o.reason_note,
            "author": o.author_label,
            "author_user_id": o.author_user_id,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "active": o.superseded_at is None,
            "superseded_at": o.superseded_at.isoformat() if o.superseded_at else None,
            "supersession_kind": o.supersession_kind,
        })
    return out
