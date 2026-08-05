"""§7e — initiative leadership: one concept, one table, three endpoints widened.

⭐⭐ THE CANONICAL NAME IS LEADER. Four words named one idea — `leader`,
`Initiative.owner_name`, RACI's Accountable, and "Project Manager". Only the first
grants anything; the last is a teaching word that must never become a model word.

⛔ AND PROJECT MANAGER IS NOT A DISTINCT GRANT. Two people editing one execution
record with no rule for disagreement is undecidable, not merely redundant.

⭐ REVOCATION CARRIES AN ACTOR (§4v.1), AND STEPPING DOWN IS ITSELF A DECLARATION —
today the only revoke is `reassign-leader`, which forces a replacement, so "X left
and nobody took over" is unrecordable.
"""
import ast
import inspect
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="lead-", suffix=".db"))

import pytest

from services.api import accounts as A

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = open(os.path.join(ROOT, "services", "api", "accounts.py"),
           encoding="utf-8").read()
TREE = ast.parse(SRC)

# ⭐ The three the leader could not reach. `post_cadence_update` is NOT here — it
# already resolved through `_leader_or_admin`, and asserting it would claim credit
# this lane did not earn.
WIDENED = ("put_milestones", "put_actions", "put_blockers")
# ⭐ Already leader-reachable before this lane. Asserted so a later edit cannot
# quietly narrow them back to admin.
ALREADY = ("set_initiative_rag", "leader_set_status", "set_csf_status",
           "propose_csf_text", "post_cadence_update")


def _fn(name):
    for n in ast.walk(TREE):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n
    raise AssertionError(f"{name} not found")


def _deps(node):
    """Dependency callables named in the signature — an AST read, not a text scan
    (§III.9): this file states the token `require_company_admin` in its own prose
    and a substring search would strike itself."""
    out = []
    for a in list(node.args.args) + list(node.args.kwonlyargs):
        pass
    for d in list(node.args.defaults) + [d for d in node.args.kw_defaults if d]:
        if isinstance(d, ast.Call) and getattr(d.func, "id", "") == "Depends":
            f = d.args[0] if d.args else None
            out.append(getattr(f, "id", None) or getattr(f, "attr", None))
    return [x for x in out if x]


def _calls(node):
    return {getattr(c.func, "id", None) or getattr(c.func, "attr", None)
            for c in ast.walk(node) if isinstance(c, ast.Call)}


# ── 1 · the three widened, and what each now tests ────────────────────────

@pytest.mark.parametrize("name", WIDENED)
def test_the_three_execution_writes_resolve_through_the_leader_check(name):
    """⭐ WHAT IT NOW TESTS: a company admin, platform staff, OR the initiative's
    ACTIVE leader — and only on THIS initiative. Previously: any company admin."""
    node = _fn(name)
    assert "require_company_admin" not in _deps(node), \
        f"{name} still binds the admin dependency — a leader cannot reach it"
    assert "_leader_or_admin" in _calls(node), \
        f"{name} does not resolve through the leadership check"


@pytest.mark.parametrize("name", ALREADY)
def test_the_five_already_leader_reachable_stay_that_way(name):
    """⛔ A KNOWN-POSITIVE FOR THE SAME PREDICATE. If `_calls` were broken, every
    assertion above would pass vacuously; these five must be FOUND."""
    assert "_leader_or_admin" in _calls(_fn(name))


def test_the_leader_check_is_per_initiative_and_scope_refusing():
    """⭐⭐ PER-INITIATIVE IS THE WHOLE POINT. A per-company answer would make the
    leader a weaker admin. And a magic-link scope never writes."""
    src = inspect.getsource(A._leader_or_admin)
    assert "iid" in inspect.signature(A._leader_or_admin).parameters
    assert "_token_scope" in src, "a view-only link is not refused"


def test_no_new_table_and_no_new_vocabulary():
    """⛔ ONE CONCEPT, ONE TABLE. `InitiativePM` was the previous dispatch's
    instruction and would have been the two-owners class."""
    assert not hasattr(A, "InitiativePM")
    names = {n.name for n in ast.walk(TREE) if isinstance(n, ast.ClassDef)}
    assert "InitiativePM" not in names and "ProjectManager" not in names
    # ⭐ AST-read of assignment targets, never a text scan — this file's own
    # docstring says "Project Manager" and must not strike itself (§III.9).
    strings = {t.value for n in ast.walk(TREE) if isinstance(n, ast.Assign)
               for t in ast.walk(n) if isinstance(t, ast.Constant)
               and isinstance(t.value, str)}
    assert "project_manager" not in strings, \
        "'project_manager' became a model word; it is a teaching word only"


# ── 2 · revoked_by ────────────────────────────────────────────────────────

def test_the_assignment_carries_a_revoking_actor():
    """⭐ §4v.1 — a revocation is a declaration and declarations carry actors.
    `revoked_at` alone records that it happened, never who did it."""
    cols = {c.name for c in A.InitiativeAssignment.__table__.columns}
    assert "revoked_at" in cols
    assert "revoked_by" in cols, "revocation has no actor"


def test_revoked_by_is_migrated_not_only_modelled():
    """⛔ create_all() CREATES MISSING TABLES, NEVER MISSING COLUMNS — the class
    that once took the demo down. A model column with no migration line is a 500
    on every read of the table."""
    assert '_add("ax_initiative_assignments", "revoked_by"' in SRC, \
        "the column exists on the model and not in the migration"


def test_every_revoke_path_on_THIS_table_stamps_the_actor():
    """⭐ THE SWEEP, PAID UP FRONT. Adding a column and leaving one writer setting
    only `revoked_at` produces rows that are silently attributionless.

    ⭐⭐ CLASSIFIED BY WHAT IT REVOKES, NOT BY THE WORD. A first draft matched any
    function mentioning `revoked_at` and named five — report shares, assessment
    invites, transfer offers. Those revoke DIFFERENT tables with different
    schemas: a missing actor and an actor that table never had look identical
    from the token. This one asks which model the function touches.

    ⛔ `revoke_assess_invite` genuinely stamps no actor. That is `ax_assessment_
    invites`, out of this lane's scope, and is reported rather than silently
    swept in — the guard must not be widened until that table has the column.
    """
    writers, bad = [], []
    for n in ast.walk(TREE):
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        d = ast.dump(n)
        touches = ("InitiativeAssignment" in d or "_active_assignment" in d)
        sets_revoked = any(
            isinstance(t, ast.Attribute) and t.attr == "revoked_at"
            for a in ast.walk(n) if isinstance(a, ast.Assign) for t in a.targets)
        if not (touches and sets_revoked):
            continue
        writers.append(n.name)
        if "revoked_by" not in d:
            bad.append(n.name)
    # ⭐ §III.4 — the denominator, printed, and a floor. A recogniser that matches
    # nothing passes this assertion for free.
    print(f"leadership revoke writers: {len(writers)} — {writers}")
    assert len(writers) >= 2, \
        f"recogniser found {len(writers)} writers; it has stopped matching"
    assert bad == [], f"leadership revoke paths that stamp no actor: {bad}"


# ── 3 · self-revoke, and the self-assign refusal ──────────────────────────

def test_a_leader_may_revoke_their_own_assignment():
    assert A.may_revoke_leadership(leader_user_id=7, actor_user_id=7,
                                   actor_is_admin=False) is True


def test_a_leader_may_not_revoke_someone_elses():
    assert A.may_revoke_leadership(leader_user_id=7, actor_user_id=9,
                                   actor_is_admin=False) is False


def test_an_admin_may_revoke_anyones():
    assert A.may_revoke_leadership(leader_user_id=7, actor_user_id=9,
                                   actor_is_admin=True) is True


def test_an_unclaimed_invite_is_revocable_by_an_admin_only():
    """⭐ `leader_user_id` IS NULL UNTIL CLAIMED. Nobody can match a null, so a
    pending invite must not become unrevokable — and must not match everybody."""
    assert A.may_revoke_leadership(leader_user_id=None, actor_user_id=9,
                                   actor_is_admin=True) is True
    assert A.may_revoke_leadership(leader_user_id=None, actor_user_id=9,
                                   actor_is_admin=False) is False
    # ⭐⭐ THE INPUT THAT ACTUALLY DISTINGUISHES THE TWO IMPLEMENTATIONS. Dropping
    # the `is not None` guard leaves `None == None` true; every case above passes
    # either way, so they proved nothing about it. Measured: the control did not
    # bite until this line existed.
    # ⛔ AND IT IS DEFENSIVE ONLY — `actor_user_id` is `user.id`, a primary key,
    # so a null actor is unreachable today. Stated rather than implied, because a
    # later caller passing a resolved-or-None id would make it reachable silently.
    assert A.may_revoke_leadership(leader_user_id=None, actor_user_id=None,
                                   actor_is_admin=False) is False, \
        "a pending invite matched a null actor — nobody would be everybody"


def test_the_standalone_revoke_does_not_create_a_replacement():
    """⭐⭐ THE WHOLE REASON IT EXISTS. `reassign-leader` forces a successor, so
    'X stepped down and nobody took over' is unrecordable today."""
    node = _fn("revoke_leader")
    assert "_create_assignment" not in _calls(node), \
        "the standalone revoke mints a replacement — it is reassign by another name"
    assert "send_lead_invite" not in _calls(node)


def test_a_leader_cannot_assign_a_leader():
    """⛔ THE SELF-GRANT REFUSAL IS STRUCTURAL HERE, not a body check: both assign
    paths bind the admin dependency, so a non-admin leader has no route to them."""
    for name in ("assign_leader", "reassign_leader"):
        assert "require_company_admin" in _deps(_fn(name)), \
            f"{name} is no longer admin-gated — a leader could self-assign"


# ── 4 · the reader sweep ──────────────────────────────────────────────────

def test_the_live_lookup_excludes_revoked_and_history_deliberately_does_not():
    """⭐ A REVOKED LEADER MUST STOP RESOLVING, and the history must keep showing
    them — those are opposite requirements on the same table, so the test names
    both rather than asserting one rule everywhere."""
    assert "revoked" in inspect.getsource(A._active_assignment)
    hist = _fn("assignment_history") if any(
        isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and n.name == "assignment_history" for n in ast.walk(TREE)) else None
    if hist is not None:
        assert "revoked" not in ast.dump(hist), \
            "history filters revoked rows — the audit trail is the point of it"


def test_the_claim_paths_refuse_a_revoked_invite():
    """⛔ A REVOKED INVITE WHOSE TOKEN STILL WORKS re-grants write access to
    somebody the company removed."""
    bad = []
    for n in ast.walk(TREE):
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        d = ast.dump(n)
        if "jti" not in d or "InitiativeAssignment" not in d:
            continue
        if "revoked" not in d and "status" not in d:
            bad.append(n.name)
    assert bad == [], f"jti paths that do not check status: {bad}"
