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

from sqlalchemy import (CheckConstraint, Column, DateTime, Index, Integer, JSON,
                        String, Text, text)

from .accounts import Base, Department, Membership

# Reason categories (§4l B.5). `private_info` is the only one that is purely a
# display override; the others name a defect somewhere upstream and Stage 3
# routes them to where the fix belongs. Stage 1 stores the category and nothing
# else acts on it.
REASON_CATEGORIES = ("calc_error", "data_error", "definition", "private_info", "other")

REASON_LABEL = {
    "calc_error": "calculation error",
    "data_error": "wrong input data",
    "definition": "definition disagreement",
    "private_info": "private CXO information",
    "other": "other",
}

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
    idx = {i["name"] for i in insp.get_indexes("ax_metric_overrides")}
    if "uq_active_metric_override" in idx:
        return {"action": "none", "reason": "partial index already present"}
    with engine.begin() as conn:
        n = conn.exec_driver_sql("SELECT COUNT(*) FROM ax_metric_overrides").scalar()
        if n:
            raise RuntimeError(
                f"ax_metric_overrides holds {n} row(s) but predates the partial "
                f"unique index. Refusing to rebuild: this table is an immutable "
                f"audit trail and must be migrated deliberately, not dropped.")
        conn.exec_driver_sql("DROP TABLE ax_metric_overrides")
    MetricOverride.__table__.create(engine)
    return {"action": "rebuilt", "rows_preserved": 0}


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
