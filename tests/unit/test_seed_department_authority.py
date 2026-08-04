"""The authority seed must produce a state the product itself can produce.

⭐⭐ THE FAILURE MODE THIS GUARDS. `ax_department_authority` held zero rows, so
the obvious seed is a few INSERTs. That would bypass `grant_department()`'s two
refusals — a platform-staff actor, and an admin granting themselves — and seed a
state THE UI CANNOT CREATE. The demo would then show sign-off working in a
configuration no customer could ever reach.

⛔ AND IT MUST NOT WRITE A CREDENTIAL. The seeded CXOs are identities that hold
authority; they are not logins.
"""
import ast
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEED = os.path.join(ROOT, "scripts", "seed-department-authority.py")
SRC = open(SEED, encoding="utf-8").read()
TREE = ast.parse(SRC)


def _calls():
    return {n.func.id for n in ast.walk(TREE)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}


# ── 1 · it goes through the production writer ──────────────────────────────

def test_it_calls_grant_department_rather_than_inserting_rows():
    """⭐ THE PRODUCTION PATH, NOT A REIMPLEMENTATION OF IT."""
    assert "grant_department" in _calls(), \
        "the seed does not call the production writer"


def test_it_never_constructs_a_DepartmentAuthority_row_directly():
    """⛔ A direct construction is exactly the bypass — it would skip the
    self-grant and platform-staff refusals the writer enforces."""
    assert "DepartmentAuthority" not in _calls(), \
        "the seed builds an authority row itself, bypassing the writer's refusals"


# ── 2 · the §7.1 separation is satisfied, not worked around ────────────────

def test_the_granter_is_not_among_the_grantees():
    """⭐ §7.1: the admin decides who speaks for a department and can never
    speak for one. `grant_department` refuses `user_id == granted_by`; the seed
    must be ARRANGED to satisfy that rather than to evade it."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("seed_da", SEED)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    admin_email = m.ADMIN[0]
    grantee_emails = {g[1] for g in m.GRANTS}
    assert admin_email not in grantee_emails, \
        "the granter is also a grantee — the separation is inverted"
    assert len(grantee_emails) == len(m.GRANTS), "duplicate grantee"


def test_it_seeds_a_department_with_a_holder_and_one_without():
    """⭐ A department with NO holder cannot be signed off by anyone, including
    the admin, and that refusal is half the demonstration. A seed that filled
    every department would hide it."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("seed_da", SEED)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert len(m.GRANTS) >= 1, "no department gets a holder"
    assert len(m.LEFT_VACANT) >= 1, "every department gets a holder"
    held = {g[0] for g in m.GRANTS}
    assert not (held & set(m.LEFT_VACANT)), \
        "a department is both granted and listed as deliberately vacant"


# ── 3 · no credential is written ───────────────────────────────────────────

def test_no_password_or_token_is_written():
    """⛔ THE HARD RULE. Nothing here may create a credential."""
    banned = ("password_hash=hash", "set_password", "make_password",
              "bcrypt", "generate_token", "secrets.token")
    for b in banned:
        assert b not in SRC, f"the seed writes a credential: {b}"
    assert "password_hash=None" in SRC, \
        "the seeded users must carry an explicit null password"
    assert "link_only=True" in SRC, \
        "the seeded users must be shadow identities, not logins"


# ── 4 · scope and reversibility ────────────────────────────────────────────

def test_it_writes_nothing_without_an_explicit_flag():
    """⭐ A seed that runs on import or on a bare invocation is how a demo write
    lands on the wrong database."""
    assert "Refusing to guess" in SRC
    assert '"--apply"' in SRC and '"--dry-run"' in SRC


def test_it_deletes_nothing():
    """⛔ CORE's cleanup rule: a cleanup once destroyed report issues
    unrecoverably. This script inserts and nothing else."""
    lowered = SRC.lower()
    for verb in (".delete(", "delete from", "truncate", ".drop("):
        assert verb not in lowered, f"the seed contains a destructive verb: {verb}"


def test_it_verifies_the_company_by_name_not_only_by_id():
    """⭐ AN INTEGER ALONE IS NOT AN IDENTITY. Keyed on id only, this would write
    into whatever company holds id 20 on the database it is pointed at."""
    assert "COMPANY_NAME" in SRC
    assert "ent.name != COMPANY_NAME" in SRC
