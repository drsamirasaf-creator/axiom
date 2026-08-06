"""§8A — a date that moves leaves a record with an actor, a time and both values.

⭐⭐ THIS IS THE PROVENANCE LAW, NOT A FEATURE. Every other defect class this era
was eventually measurable; this one is not. When the movement was never recorded,
*"this milestone has moved three times"* is not merely hard to answer — the answer
does not exist, and effort does not produce it. That is why the cost of leaving
this open is strictly monotonic and why it was built before the surface that
reads it.

⭐⭐ "MOVED THREE TIMES" IS STRONGER THAN "AMBER". A RAG badge is somebody's
judgement about a date; a count of movements is the date's own record, and the
reader can check it. The badge tells you how the leader feels; the count tells you
what happened.

⛔ NOTHING IS BACKFILLED. Rows that moved before this lane left no from/to, and
inventing one would make an unrecoverable movement LOOK recoverable — the one
outcome worse than an honestly absent record, and undetectable afterwards.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="slip-", suffix=".db"))

import ast
import inspect

import pytest

from services.api import accounts as A


# ── 1 · the event carries what a movement IS ──────────────────────────────

def test_the_event_model_can_name_a_milestone_and_freezes_its_label():
    """⭐ A MOVEMENT NEEDS A SUBJECT. `InitiativeEvent` is keyed on the initiative,
    so without a milestone id the record would say 'a date moved on this project'
    and never which one.

    ⭐⭐ AND THE LABEL IS FROZEN TEXT, NEVER A JOIN — the §4x `author_label`
    precedent. A milestone may be renamed or revoked; an event that resolved its
    subject at read time would lose it exactly when the history matters most."""
    cols = {c.name for c in A.InitiativeEvent.__table__.columns}
    assert "milestone_id" in cols, "an event cannot name which milestone moved"
    assert "subject_label" in cols, "the subject is resolved at read time and can vanish"
    assert A.InitiativeEvent.__table__.c.milestone_id.nullable is True
    assert A.InitiativeEvent.__table__.c.subject_label.nullable is True


def test_the_two_date_event_types_are_declared_and_distinct():
    """⛔ ONE TYPE FOR BOTH WOULD MAKE THE SUBJECT KIND A NULL CHECK. An
    initiative's own target date and a milestone's are different facts about
    different objects, and a reader scanning a history must see which without
    inspecting a nullable column."""
    assert A.EV_TARGET_DATE_CHANGED == "target_date_changed"
    assert A.EV_MILESTONE_DATE_CHANGED == "milestone_date_changed"
    assert A.EV_TARGET_DATE_CHANGED != A.EV_MILESTONE_DATE_CHANGED


def test_a_milestone_event_carries_a_milestone_and_an_initiative_event_does_not():
    """⭐ THE INVARIANT THAT MAKES THE TWO TYPES MEAN SOMETHING. A type naming a
    milestone with no milestone id, or an initiative event carrying one, would
    make the discriminator decorative."""
    assert A.date_event_is_wellformed(
        A.EV_MILESTONE_DATE_CHANGED, milestone_id=7, subject_label="Vendor selected")
    assert not A.date_event_is_wellformed(
        A.EV_MILESTONE_DATE_CHANGED, milestone_id=None, subject_label="x")
    assert A.date_event_is_wellformed(
        A.EV_TARGET_DATE_CHANGED, milestone_id=None, subject_label=None)
    assert not A.date_event_is_wellformed(
        A.EV_TARGET_DATE_CHANGED, milestone_id=7, subject_label=None)


# ── 2 · the writers emit it ───────────────────────────────────────────────

def _body(fn):
    """⛔ §III.9 — read the AST, never the source text. A guard matching the WORD
    `target_date_changed` would fire on the docstring that explains the rule, and
    this file has now watched that happen twelve times."""
    src = inspect.getsource(fn)
    tree = ast.parse(inspect.cleandoc(src))
    fnode = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    body = list(fnode.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]                      # drop the docstring
    return ast.Module(body=body, type_ignores=[])


def _etype(node):
    """Resolve an event-type argument to its VALUE, whether it is a literal or a
    module constant.

    ⭐⭐ THE FIRST VERSION OF THIS RECOGNISER MATCHED `ast.Constant` ONLY, and the
    writers name their types (`EV_TARGET_DATE_CHANGED`) precisely so two call
    sites cannot spell one event differently. So the guard reported "no
    conditional emits the date event" about code that emits it — §7r-G exactly,
    where a scan *"said SHAPE and meant VARIABLE NAME"* and was fixed by resolving
    names to what they were bound from. **The guard was wrong, not the code**, and
    tightening the code to satisfy it would have replaced a named constant with a
    literal to please a test.
    """
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return getattr(A, node.id, None)
    return None


def _event_types_emitted(fn):
    """Every event type handed to `_ini_event` as its `etype` argument."""
    out = set()
    for n in ast.walk(_body(fn)):
        if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "_ini_event":
            if len(n.args) >= 4:
                out.add(_etype(n.args[3]))
            for kw in n.keywords:
                if kw.arg == "etype":
                    out.add(_etype(kw.value))
        # the milestone writer calls the milestone-specific helper
        if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "_milestone_date_event":
            out.add(A.EV_MILESTONE_DATE_CHANGED)
    return out - {None}


def test_the_patch_path_emits_a_date_event():
    """⭐ THE INITIATIVE'S OWN `target_date` IS ONE OF THIRTEEN FIELDS THE PATCH
    ACCEPTS, and it was the only consequential one with no event of its own."""
    assert "target_date_changed" in _event_types_emitted(A.patch_initiative)


def test_the_milestone_writer_emits_a_date_event():
    assert "milestone_date_changed" in _event_types_emitted(A.put_milestones)


def test_a_date_change_is_never_swallowed_by_the_priority_branch():
    """⭐⭐ THE SHARPEST HALF OF THIS DEFECT, AND IT IS NOT THE MISSING VALUES.

    The PATCH's event selection was an `if / elif / elif` chain: a priority change
    won, an impact change came second, and everything else fell to a generic
    `note`. So a request moving BOTH the priority AND the target date recorded
    only the priority — the date left no trace at all, not even its field name.

    ⛔ The date event must therefore be emitted from a branch that CANNOT be
    reached past by another field's change."""
    tree = _body(A.patch_initiative)

    def calls_date_event(node):
        return any(
            isinstance(n, ast.Call)
            and getattr(n.func, "id", None) == "_ini_event"
            and len(n.args) >= 4
            and _etype(n.args[3]) == A.EV_TARGET_DATE_CHANGED
            for n in ast.walk(node))

    # find the If whose body emits it, and require that no `orelse` chain above it
    # can prevent it — i.e. it is not in the orelse of a test about another field.
    hosts = [n for n in ast.walk(tree) if isinstance(n, ast.If) and calls_date_event(n)]
    assert hosts, "no conditional emits the date event"
    for h in hosts:
        # the emitting If must not itself sit inside another If's orelse
        for other in ast.walk(tree):
            if isinstance(other, ast.If) and other is not h:
                assert h not in other.orelse, \
                    "the date event sits in an elif — another field's change hides it"


def test_the_note_no_longer_claims_the_date_it_cannot_describe():
    """⭐ THE `note` EVENT WAS THE FALLBACK FOR EVERY FIELD WITH NO EVENT OF ITS
    OWN, and its `to_value` is a comma-joined list of field NAMES with no values.
    That is honest for a title or a currency. It is not honest for a date, because
    'target_date was among the things that changed' reads as a record of the
    change while carrying none of it.

    Now that the date has its own event, it must leave the note's list — or one
    movement would produce two rows, one of which says less than the other.

    ⚠ AND THE FIRST VERSION OF THIS TEST PASSED AGAINST THE PRE-LANE CODE. It
    asserted that a `.join` existed and that the string `target_date` appeared
    somewhere in the function — both true before this lane, because `target_date`
    has always been in the PATCH's field list. **The assertion was right and the
    input could not discriminate** (§7.43 entry 4). It now names the thing that
    actually changed: what the note is joined OVER.

    ⭐ SCOPED TO THE NOTE EVENT, NOT TO EVERY `join` IN THE FUNCTION. A first
    version asserted over all of them and caught the AUDIT detail, which
    legitimately lists every touched field — that is the audit trail's job, and it
    makes no claim to describe the change. **Two records, two jobs**; a guard that
    cannot tell them apart would have forced the audit to lie by omission.
    """
    tree = _body(A.patch_initiative)
    notes = [n for n in ast.walk(tree)
             if isinstance(n, ast.Call)
             and getattr(n.func, "id", None) == "_ini_event"
             and len(n.args) >= 6 and _etype(n.args[3]) == "note"]
    assert notes, "the note event is gone entirely — it still has a job"
    for call in notes:
        arg = call.args[5]                       # the `to` value
        assert isinstance(arg, ast.Call) and getattr(arg.func, "attr", None) == "join", \
            "the note's to-value is no longer a joined field list"
        joined = arg.args[0]
        # ⛔ THE DEFECT IS `",".join(changed)` — the raw list, date included.
        assert not (isinstance(joined, ast.Name) and joined.id == "changed"), \
            "the note still joins the RAW changed list, so it re-reports the date " \
            "as a bare field name beside the event that carries its values"
        assert isinstance(joined, ast.Name), \
            "the joined collection is not a named list — the exclusion is unreadable"
        excl = [n for n in ast.walk(tree)
                if isinstance(n, ast.Assign)
                and any(getattr(t, "id", None) == joined.id for t in n.targets)
                and isinstance(n.value, ast.ListComp)]
        assert excl, f"`{joined.id}` is not derived by filtering `changed`"
        assert "target_date" in ast.unparse(excl[0].value), \
            "the filtered list does not name the field it excludes"


# ── 3 · absence stays absence ─────────────────────────────────────────────

def test_a_first_date_is_distinguishable_from_an_unrecorded_one():
    """⭐⭐ `from_value` NULL MEANS THE MILESTONE HAD NO DATE — a fact — and it
    means that ONLY because every movement from now on is recorded. For rows that
    moved before this lane, nothing was written at all, and there is no event to
    misread.

    ⛔ The distinction is the `prior_absent` precedent from B12: a first entry and
    a change from nothing are different events, and collapsing them would let a
    reader infer a date that never existed."""
    assert A.date_event_is_wellformed(
        A.EV_MILESTONE_DATE_CHANGED, milestone_id=3, subject_label="x",
        from_value=None, to_value="2026-03-15")
    # ⛔ AND A NO-OP IS NOT AN EVENT. A save that changes nothing must not
    # manufacture a movement — three saves would then read as three slips.
    assert not A.date_event_is_wellformed(
        A.EV_MILESTONE_DATE_CHANGED, milestone_id=3, subject_label="x",
        from_value="2026-03-15", to_value="2026-03-15")


def test_nothing_is_backfilled():
    """⛔ NO WRITER MAY SYNTHESISE A MOVEMENT FOR A ROW THAT MOVED BEFORE THIS
    LANE. An invented from-value would make an unrecoverable movement look
    recoverable, which is worse than the absence and undetectable afterwards.

    ⭐ §III.4 — THE DENOMINATOR IS PRINTED AND AN EMPTY CORPUS FAILS. A guard
    phrased *"X is never done to F"* is satisfied by F not existing, and this one
    would have passed on a module with no backfills at all.
    """
    tree = ast.parse(inspect.getsource(A))
    fns = [n for n in ast.walk(tree)
           if isinstance(n, ast.FunctionDef) and "backfill" in n.name.lower()]
    assert len(fns) >= 3, \
        f"corpus too small to mean anything: {len(fns)} backfill functions"
    for n in fns:
        body = ast.unparse(ast.Module(body=n.body, type_ignores=[]))
        assert A.EV_TARGET_DATE_CHANGED not in body and \
               A.EV_MILESTONE_DATE_CHANGED not in body, \
               f"{n.name} synthesises a date movement"


# ── 4 · the record is readable ────────────────────────────────────────────

def test_the_history_endpoint_returns_the_new_fields():
    """⭐ AN EVENT WRITTEN AND UNREADABLE IS THE BUILT-BUT-NOT-WIRED CLASS —
    eighteen instances are recorded in ONBOARDING. The endpoint that already
    renders this initiative's events must carry the subject with them."""
    tree = _body(A.initiative_history)
    src = ast.unparse(tree)
    assert "milestone_id" in src, "the history cannot say WHICH milestone moved"
    assert "subject_label" in src, "the history cannot say what it was called"


# ── 4b · behaviour, not declaration ───────────────────────────────────────

@pytest.fixture()
def db():
    """⭐ THE STANDING PRINCIPLE — assert behaviour against a real session, never
    a declaration. An AST guard proves the writer CONTAINS the call; only a write
    proves a row lands, and this codebase has shipped a declared-but-unbound
    clause six times."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    eng = create_engine("sqlite://")
    A.Base.metadata.create_all(eng)
    s = sessionmaker(bind=eng)()
    try:
        yield s
    finally:
        s.close()


def _seed(db):
    ini = A.Initiative(company_id=1, ref_code="A1", title="ERP migration",
                       status="in_progress", importance="high", urgency="high",
                       current_priority="high", created_by=1)
    db.add(ini)
    db.flush()
    m = A.InitiativeMilestone(initiative_id=ini.id, title="Vendor selected",
                              target_date="2026-03-15", status="pending",
                              criterion="a signed contract")
    db.add(m)
    db.flush()
    return ini, m


def test_a_movement_writes_a_row_carrying_both_values_and_its_subject(db):
    ini, m = _seed(db)
    assert A._milestone_date_event(db, ini, 42, m, m.target_date, "2026-05-01") is True
    db.flush()
    ev = db.query(A.InitiativeEvent).one()
    assert ev.event_type == A.EV_MILESTONE_DATE_CHANGED
    assert ev.from_value == "2026-03-15" and ev.to_value == "2026-05-01"
    assert ev.milestone_id == m.id
    assert ev.subject_label == "Vendor selected"
    assert ev.actor_user_id == 42 and ev.created_at is not None


def test_three_movements_read_as_three(db):
    """⭐⭐ THIS IS THE FINDING THE LANE EXISTS FOR — and it is a count a reader
    can check, not a badge somebody chose."""
    ini, m = _seed(db)
    for new in ("2026-05-01", "2026-07-01", "2026-09-30"):
        A._milestone_date_event(db, ini, 42, m, m.target_date, new)
        m.target_date = new
    db.flush()
    evs = (db.query(A.InitiativeEvent)
             .filter_by(milestone_id=m.id, event_type=A.EV_MILESTONE_DATE_CHANGED)
             .order_by(A.InitiativeEvent.id).all())
    assert len(evs) == 3
    assert [e.from_value for e in evs] == ["2026-03-15", "2026-05-01", "2026-07-01"]
    assert [e.to_value for e in evs] == ["2026-05-01", "2026-07-01", "2026-09-30"]


def test_a_save_that_moves_nothing_writes_nothing(db):
    """⛔ THREE SAVES MUST NOT READ AS THREE SLIPS. The bulk writer receives the
    whole list on every save, so most rows arrive unchanged; a writer keyed on
    'was this row submitted' rather than 'did this value move' would manufacture
    a movement per save and destroy the count above."""
    ini, m = _seed(db)
    assert A._milestone_date_event(db, ini, 42, m, "2026-03-15", "2026-03-15") is False
    db.flush()
    assert db.query(A.InitiativeEvent).count() == 0


def test_a_first_date_records_an_absent_prior_rather_than_a_guess(db):
    """⭐ NULL ON THE FROM SIDE MEANS THE MILESTONE HAD NO DATE — a fact, because
    every movement from here is recorded. It is not the same as the silence left
    by a row that moved before this lane, and nothing invents a value for those."""
    ini, m = _seed(db)
    m.target_date = None
    assert A._milestone_date_event(db, ini, 7, m, None, "2026-04-01") is True
    db.flush()
    ev = db.query(A.InitiativeEvent).one()
    assert ev.from_value is None and ev.to_value == "2026-04-01"


# ── 5 · the controls — each guard, against its own defect, in memory ───────
#
# ⭐⭐ §III.11 — A KNOWN-NEGATIVE ALONE PROVES NOTHING: a matcher that can never
# match anything satisfies every absence assertion in a suite. Each control below
# plants the exact defect this lane removed and requires the recogniser to see
# it, PAIRED with the correct shape which it must not flag.
#
# ⭐ §III.10 — planted IN MEMORY. Nothing is written to the tree; four guards have
# stranded a live NameError in production source by planting into a file and
# being killed before the `finally` ran.

def _fn(src, name):
    """Parse a source string and return the named function's body as a Module."""
    t = ast.parse(inspect.cleandoc(src))
    f = next(n for n in ast.walk(t) if isinstance(n, ast.FunctionDef) and n.name == name)
    body = list(f.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]
    return ast.Module(body=body, type_ignores=[])


_THE_DEFECT_AS_IT_SHIPPED = '''
def patch_initiative(x):
    if "current_priority" in changed:
        _ini_event(db, ini, user.id, "priority_changed", a, b, note)
    elif "expected_impact_amount" in changed:
        _ini_event(db, ini, user.id, "impact_updated", c, d, note)
    elif changed:
        _ini_event(db, ini, user.id, "note", None, ",".join(changed), note)
'''

_THE_ELIF_TRAP = '''
def patch_initiative(x):
    if "current_priority" in changed:
        _ini_event(db, ini, user.id, "priority_changed", a, b, note)
    elif "target_date" in changed:
        _ini_event(db, ini, user.id, EV_TARGET_DATE_CHANGED, o, n, note)
'''

_THE_FIX = '''
def patch_initiative(x):
    if "target_date" in changed:
        _ini_event(db, ini, user.id, EV_TARGET_DATE_CHANGED, o, n, note)
    other = [f for f in changed if f != "target_date"]
    if "current_priority" in other:
        _ini_event(db, ini, user.id, "priority_changed", a, b, note)
    elif other:
        _ini_event(db, ini, user.id, "note", None, ",".join(other), note)
'''


def _emits_date_event(mod):
    return any(isinstance(n, ast.Call)
               and getattr(n.func, "id", None) == "_ini_event"
               and len(n.args) >= 4
               and _etype(n.args[3]) == A.EV_TARGET_DATE_CHANGED
               for n in ast.walk(mod))


def _date_event_is_reachable_past(mod):
    """True when the emitting `if` sits in another `if`'s orelse — i.e. an elif."""
    hosts = [n for n in ast.walk(mod) if isinstance(n, ast.If) and _emits_date_event(n)]
    for h in hosts:
        for other in ast.walk(mod):
            if isinstance(other, ast.If) and other is not h and h in other.orelse:
                return True
    return False


def test_CONTROL_the_recogniser_sees_the_defect_as_it_shipped():
    """⛔ THE ABSENCE CASE — no date event at all, which is what production had."""
    assert not _emits_date_event(_fn(_THE_DEFECT_AS_IT_SHIPPED, "patch_initiative"))


def test_CONTROL_the_recogniser_sees_the_elif_trap():
    """⭐⭐ THE SUBTLE CASE, AND THE ONE THE OBVIOUS FIX WOULD HAVE SHIPPED. The
    event exists, the field name is right, and a priority change still hides it.
    A guard that only asked *"is the event emitted?"* would have passed this."""
    mod = _fn(_THE_ELIF_TRAP, "patch_initiative")
    assert _emits_date_event(mod), "the control does not even emit — it tests nothing"
    assert _date_event_is_reachable_past(mod), \
        "the recogniser cannot tell an elif from an independent branch"


def test_CONTROL_the_recogniser_passes_the_shipped_fix():
    """⭐ THE PAIRED POSITIVE. Without it the two controls above are satisfied by
    a recogniser that flags everything."""
    mod = _fn(_THE_FIX, "patch_initiative")
    assert _emits_date_event(mod)
    assert not _date_event_is_reachable_past(mod)


def test_CONTROL_the_wellformedness_predicate_fails_on_each_of_its_own_defects():
    """⭐ FOUR DEFECTS, FOUR REFUSALS, AND THE CORRECT SHAPE ACCEPTED."""
    ok = dict(milestone_id=5, subject_label="Vendor selected",
              from_value="2026-03-15", to_value="2026-05-01")
    assert A.date_event_is_wellformed(A.EV_MILESTONE_DATE_CHANGED, **ok)
    # a milestone event that names no milestone
    assert not A.date_event_is_wellformed(A.EV_MILESTONE_DATE_CHANGED,
                                          **{**ok, "milestone_id": None})
    # an initiative event that names one
    assert not A.date_event_is_wellformed(A.EV_TARGET_DATE_CHANGED, **ok)
    # a save that moved nothing
    assert not A.date_event_is_wellformed(A.EV_MILESTONE_DATE_CHANGED,
                                          **{**ok, "to_value": ok["from_value"]})
    # an event type nobody declared
    assert not A.date_event_is_wellformed("rag_changed", **ok)


def test_CONTROL_the_etype_resolver_reads_a_constant_and_a_literal_alike():
    """⭐⭐ THE RECOGNISER'S OWN DEFECT, PLANTED. Its first version matched
    `ast.Constant` only and reported the shipped fix as emitting nothing — because
    the writers NAME their event types so two call sites cannot spell one event
    differently. **The guard was wrong and the code was right**, and the cheap fix
    would have been to replace a named constant with a literal to please a test."""
    lit = ast.parse('f(a, b, c, "target_date_changed")').body[0].value.args[3]
    nam = ast.parse('f(a, b, c, EV_TARGET_DATE_CHANGED)').body[0].value.args[3]
    assert _etype(lit) == A.EV_TARGET_DATE_CHANGED
    assert _etype(nam) == A.EV_TARGET_DATE_CHANGED
    # ⭐ and a name that resolves to nothing is None, never a false match
    unk = ast.parse("f(a, b, c, EV_NO_SUCH_THING)").body[0].value.args[3]
    assert _etype(unk) is None
