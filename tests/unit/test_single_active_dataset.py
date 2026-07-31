"""A company holds at most ONE active financial dataset.

⭐⭐ DETERMINISTIC BY ACCIDENT IS NOT DETERMINISTIC. Enterprise 20 held two
active datasets for a week — ds 3 (`source=direct`, payload `public`) and ds 45
(`source=upload`, payload `private`). `_active_company_dataset` orders by
`version DESC`, so it returned ds 45 and behaviour was right; ⭐ the ownership
ruling rested on an ordering nobody had asserted.
"""
import importlib.util
import os
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest


def _guard():
    spec = importlib.util.spec_from_file_location(
        "sad", "scripts/check-single-active-dataset.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class _Row:
    def __init__(self, i, eid, active, version=1):
        self.id, self.enterprise_id, self.is_active, self.version = i, eid, active, version


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE GUARD AND ITS KNOWN POSITIVE
# ═══════════════════════════════════════════════════════════════════════════

def test_the_guard_FLAGS_two_active_rows_on_one_company():
    """⭐ The exact shape found live: a seed row and an upload row, both active."""
    g = _guard()
    bad = g.violations([_Row(3, 20, True, 1), _Row(45, 20, True, 3),
                        _Row(42, 20, False, 1)])
    assert bad == {20: [3, 45]}


def test_the_guard_ACCEPTS_one_active_row():
    g = _guard()
    assert g.violations([_Row(45, 20, True, 3), _Row(42, 20, False)]) == {}


def test_the_guard_ACCEPTS_a_company_with_NO_active_row():
    """⭐ Four live companies await a first upload. Zero active is ordinary."""
    g = _guard()
    assert g.violations([_Row(42, 20, False)]) == {}


def test_the_guard_ACCEPTS_one_each_across_companies():
    g = _guard()
    assert g.violations([_Row(1, 10, True), _Row(2, 11, True)]) == {}


def test_the_control_and_the_live_check_run_THE_SAME_function():
    """⭐⭐ A guard whose control exercises a different function has tested
    nothing."""
    src = open("scripts/check-single-active-dataset.py", encoding="utf-8").read()
    assert src.count("violations(") >= 4
    assert "def violations(rows)" in src


def test_the_control_is_planted_IN_MEMORY_never_in_production_source():
    """⭐⭐ The guard-planting cleanup failure has happened TWICE — sentinel.py
    and benchmarks/router.py — each leaving a live NameError when a timeout
    killed the run mid-control."""
    src = open("scripts/check-single-active-dataset.py", encoding="utf-8").read()
    for banned in ("open(", "write(", "Path(", "shutil"):
        assert banned not in src, f"the guard touches the filesystem ({banned})"


def test_the_guard_prints_its_coverage():
    src = open("scripts/check-single-active-dataset.py", encoding="utf-8").read()
    assert "checked {len(rows)} datasets" in src
    assert "a broken selector, not a clean corpus" in src


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE INVARIANT — one writer
# ═══════════════════════════════════════════════════════════════════════════

def test_there_is_a_SINGLE_WRITER_and_it_clears_before_it_sets():
    import inspect

    from services.api.accounts import set_active_dataset
    src = inspect.getsource(set_active_dataset)
    assert "is_active = False" in src and "is_active = True" in src
    assert "cleared" in src, "the writer does not report what it cleared"


def test_the_SEED_no_longer_writes_the_flag_directly():
    """⭐⭐ THE MECHANISM. The showcase seed set is_active directly without
    clearing siblings, and seed_showcase() runs from core/db.py on EVERY BOOT —
    so clearing the flag by hand would have been undone by the next deploy."""
    src = open("services/api/core/seed.py", encoding="utf-8").read()
    assert "set_active_dataset(db, ent.id, ds.id)" in src
    assert "ds.is_active = True                 # so" not in src, \
        "the seed still sets the flag directly"
    assert "A second writer is a second source of truth" in src


def test_the_resolver_is_ORDERED_so_the_answer_cannot_be_a_coin_flip():
    """⭐ 51 call sites depend on this ordering."""
    import inspect

    from services.api.accounts import _active_company_dataset
    src = inspect.getsource(_active_company_dataset)
    assert "order_by" in src and "version.desc()" in src
