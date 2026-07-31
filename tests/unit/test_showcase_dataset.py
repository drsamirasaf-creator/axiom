"""The showcase resolves the dataset its published packs are frozen against.

⭐⭐ THE REGRESSION THIS CLOSES WAS MINE. At `9d708c3` I routed the showcase seed
through the new single writer and passed THE SEED'S OWN ROW, so every boot cleared
the real upload and activated the seed. Five demo surfaces went blank, the
valuation halved — and EVERY GATE STAYED GREEN, because the single-active
invariant was perfectly satisfied. ⭐ A constraint on CARDINALITY cannot catch an
error of IDENTITY.
"""
import importlib.util
import os
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest


def _guard():
    spec = importlib.util.spec_from_file_location(
        "sd", "scripts/check-showcase-dataset.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE GUARD AND ITS KNOWN POSITIVE
# ═══════════════════════════════════════════════════════════════════════════

def test_the_guard_FLAGS_the_exact_1_Aug_shape():
    """⭐ Active = the seed row while the packs pin the upload."""
    g = _guard()
    bad = g.mismatches([{"company_id": 20, "active_dataset_id": 3,
                         "pack_dataset_ids": [45]}])
    assert len(bad) == 1
    assert "not among" in bad[0]["why"]


def test_the_guard_ACCEPTS_agreement():
    g = _guard()
    assert g.mismatches([{"company_id": 20, "active_dataset_id": 45,
                          "pack_dataset_ids": [45]}]) == []


def test_packs_with_NOTHING_active_is_flagged():
    g = _guard()
    bad = g.mismatches([{"company_id": 20, "active_dataset_id": None,
                         "pack_dataset_ids": [45]}])
    assert bad and "no dataset is active" in bad[0]["why"]


def test_a_showcase_company_with_NO_PACKS_is_not_a_mismatch():
    """⭐ A demo that has never published has nothing to disagree with, and
    failing on it would make the gate unpassable for a new showcase."""
    g = _guard()
    assert g.mismatches([{"company_id": 21, "active_dataset_id": 9,
                          "pack_dataset_ids": []}]) == []


def test_control_and_live_check_share_the_same_function():
    src = open("scripts/check-showcase-dataset.py", encoding="utf-8").read()
    assert "def mismatches(companies)" in src
    # def + control + live call = 3; the point is that ONE function serves both
    assert src.count("mismatches(") >= 3


def test_the_control_touches_no_file():
    """⭐ The guard-planting cleanup failure has happened twice."""
    src = open("scripts/check-showcase-dataset.py", encoding="utf-8").read()
    body = src.split("def main(")[0]          # the control half
    for banned in ("open(", "write(", "Path(", "shutil"):
        assert banned not in body, f"the control touches the filesystem ({banned})"


def test_the_guard_prints_its_coverage():
    src = open("scripts/check-showcase-dataset.py", encoding="utf-8").read()
    assert "checked {len(rows)} showcase" in src
    assert "a broken selector, not a" in src


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE SEED RULE — the fix that survives a boot
# ═══════════════════════════════════════════════════════════════════════════

def test_the_seed_activates_ONLY_when_nothing_is_active():
    """⭐⭐ A SEED CREATES WHAT IS MISSING; IT DOES NOT RE-DECIDE WHAT IS CURRENT.
    Fixing the flag alone is undone by the next boot — the lesson from the prior
    is_active lane, applied to that lane's own fix."""
    src = open("services/api/core/seed.py", encoding="utf-8").read()
    assert "if _active_company_dataset(db, ent.id) is None:" in src
    assert "A SEED CREATES WHAT IS MISSING" in src
    assert "deterministic AND WRONG" in src, \
        "the seed does not record why this was wrong the second time"


def test_the_seed_no_longer_passes_its_own_row_unconditionally():
    src = open("services/api/core/seed.py", encoding="utf-8").read()
    # ⭐ ASSERT THE LINE ORDER, not a character window — a long comment block
    # between the guard and the call made the window test brittle without
    # making the code wrong.
    lines = src.splitlines()
    # ⭐ SKIP COMMENTS. The fix's own explanatory comment QUOTES the call, and
    # matching it found the comment rather than the code — the third time this
    # era a guard matched the text describing a rule instead of the rule.
    def _code(pred):
        return next(i for i, l in enumerate(lines)
                    if pred(l) and not l.strip().startswith("#"))
    call = _code(lambda l: "set_active_dataset(db, ent.id, ds.id)" in l)
    guard = _code(lambda l: "if _active_company_dataset(db, ent.id) is None:" in l)
    assert guard < call, \
        "set_active_dataset is not guarded — every boot would clear the real upload"
    assert call - guard <= 2, \
        f"the guard is {call - guard} lines from the call it protects"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE CRAWLER — wired, and targeted by NAME
# ═══════════════════════════════════════════════════════════════════════════

def test_the_crawler_is_on_an_automated_path():
    """⭐⭐ EIGHTH BUILT-BUT-NOT-WIRED INSTANCE, and the first on the standing
    VERIFICATION METHOD. A guard nobody runs fails open on everything it exists
    to catch."""
    import pathlib
    wf = pathlib.Path(".github/workflows/demo-rot.yml")
    assert wf.exists(), "the demo-rot crawl is on no workflow"
    y = wf.read_text(encoding="utf-8")
    assert "auth-regression.py" in y
    assert "schedule:" in y and "cron:" in y


def test_the_crawler_REFUSES_TO_PASS_SILENTLY_when_unconfigured():
    """⭐⭐ A green tick from a job that checked nothing is the exact failure this
    guard is about."""
    y = open(".github/workflows/demo-rot.yml", encoding="utf-8").read()
    assert "exit 1" in y
    assert "checked nothing" in y


def test_the_crawler_targets_MERIDIAN_BY_NAME_not_by_position():
    """⭐ `companies[0]` silently follows whatever sorts first, so the guard
    protected an arbitrary company while the showcase rotted."""
    src = open("scripts/auth-regression.py", encoding="utf-8").read()
    assert 'if "meridian" in str(c.get("name", "")).lower()' in src
    assert "companies[0].get(\"company_id\")" not in src.split("_named")[0][-800:], \
        "a positional target remains on the demo-rot path"
    assert "no company named Meridian is visible" in src


def test_the_demo_rot_predicate_asserts_POPULATION_not_reachability():
    """⭐ An empty surface returns 200. `has_data` is the only thing that
    distinguishes 'rendered' from 'rendered empty'."""
    src = open("scripts/auth-regression.py", encoding="utf-8").read()
    assert 'lambda d: bool(d.get("has_data"))' in src
    assert "EMPTY — demo surface not populated" in src
