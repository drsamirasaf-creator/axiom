"""The model-column gate's negative control, as a test rather than a one-off run.

⭐ A GATE VERIFIED ONCE IN A THROWAWAY WORKTREE IS A GATE NOBODY WILL RE-VERIFY.
The check was proved against the real defect commit by hand — it named
`ax_initiatives.links_considered_at` and `links_considered_by` and exited 1. That
run is gone. This file keeps the proof, so a future edit that quietly defangs the
gate fails here instead of passing silently and waiting for the next outage.

The fixtures are synthetic source strings rather than git revisions on purpose:
the assertion is about the RULE, and pinning it to a commit hash would make the
test rot the first time history is rewritten.
"""
import importlib.util
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GATE = os.path.join(ROOT, "scripts", "check-model-columns.py")


@pytest.fixture(scope="module")
def gate():
    spec = importlib.util.spec_from_file_location("model_column_gate", GATE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BEFORE = '''
class Initiative(Base):
    __tablename__ = "ax_initiatives"
    id = Column(Integer, primary_key=True)
    title = Column(String(300), nullable=False)
'''

# the real defect: two columns added to an EXISTING table, no _add() lines
AFTER_BROKEN = '''
class Initiative(Base):
    __tablename__ = "ax_initiatives"
    id = Column(Integer, primary_key=True)
    title = Column(String(300), nullable=False)
    links_considered_at = Column(DateTime, nullable=True)
    links_considered_by = Column(Integer, nullable=True)

def _ensure_ax_columns(engine):
    _add("ax_initiatives", "rag", "rag VARCHAR(8)")
'''

AFTER_FIXED = AFTER_BROKEN.replace(
    '    _add("ax_initiatives", "rag", "rag VARCHAR(8)")',
    '    _add("ax_initiatives", "rag", "rag VARCHAR(8)")\n'
    '    _add("ax_initiatives", "links_considered_at", "links_considered_at TIMESTAMP")\n'
    '    _add("ax_initiatives", "links_considered_by", "links_considered_by INTEGER")')

# a NEW table needs no _add(): create_all() makes it whole
AFTER_NEW_TABLE = BEFORE + '''
class KrAlias(Base):
    __tablename__ = "ax_kr_aliases"
    id = Column(Integer, primary_key=True)
    kr_key = Column(String(64), nullable=False)
'''


def _missing(gate, before_src, after_src):
    """Columns the gate would flag, given a before/after pair."""
    import ast
    base = gate.model_columns(ast.parse(before_src))
    now = gate.model_columns(ast.parse(after_src))
    migrated = gate.migrated_columns(after_src)
    out = []
    for table, cols in now.items():
        if table not in base:
            continue
        for col in sorted(cols - base[table]):
            if (table, col) not in migrated:
                out.append((table, col))
    return out


def test_it_catches_the_defect_that_took_the_demo_down(gate):
    """⭐ THE NEGATIVE CONTROL. Two columns added to a pre-existing table with no
    migration line — the exact shape of d08ecce."""
    found = _missing(gate, BEFORE, AFTER_BROKEN)
    assert ("ax_initiatives", "links_considered_at") in found
    assert ("ax_initiatives", "links_considered_by") in found
    assert len(found) == 2, found


def test_it_passes_once_the_migration_lines_exist(gate):
    assert _missing(gate, BEFORE, AFTER_FIXED) == []


def test_a_brand_new_table_needs_no_add_line(gate):
    """create_all() creates missing TABLES; only columns on tables production
    ALREADY HAS need a migration. Flagging a new table's columns would be the
    421-finding noise that got the first formulation discarded."""
    assert _missing(gate, BEFORE, AFTER_NEW_TABLE) == []


def test_an_unchanged_column_is_not_flagged(gate):
    """The gate is diff-scoped. A column that existed before this change is not
    its business, however it was created."""
    assert _missing(gate, BEFORE, BEFORE) == []


def test_the_gate_reads_the_real_accounts_module(gate):
    """Smoke: the parser survives the actual file, which is 12k lines and has six
    routers and dozens of models. A gate that only works on fixtures is a fixture."""
    import ast
    src = open(os.path.join(ROOT, "services", "api", "accounts.py"), encoding="utf-8").read()
    models = gate.model_columns(ast.parse(src))
    assert len(models) > 30, "the model parser found suspiciously few ax_* tables"
    assert "ax_initiatives" in models
    assert "links_considered_at" in models["ax_initiatives"]
    migrated = gate.migrated_columns(src)
    assert ("ax_initiatives", "links_considered_at") in migrated, \
        "the live file has lost the migration line that fixed the outage"
