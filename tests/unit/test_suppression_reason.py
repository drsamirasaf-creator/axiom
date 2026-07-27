"""Three states, never conflated: scored · withheld · absent.

The department trend reported n=0 / no_responses / "No responses from this
department in this cycle" for Meridian's HR and Supply Chain in cycle 37. Both
DID respond (n=3 and n=2); both were withheld for anonymity. The suppression was
correct — no value leaked — but the explanation was false, and a false
explanation of a real absence is its own defect: it tells a manager their team
ignored the survey when in fact it answered and was protected.

Root cause: the complement-inference branch hid the value by writing
`cei_val, npart = None, 0`, and the reason was then derived from `npart == 0`.
Suppression destroyed the evidence it needed to explain itself.
"""
import pytest
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.assessment_engine import (
    KFLOOR, suppression_reason, suppression_block, SUPPRESSION_NOTE,
    _apply_dept_kfloor, _partition_status,
)


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


def _code_of(fn_name: str) -> str:
    """Source of a function with comments and docstrings stripped.

    These guards assert that a bad line is ABSENT, and the comment explaining
    why it was removed necessarily quotes it — so a plain substring search over
    the source flags the explanation as the defect. Dropping comment lines
    leaves the code the assertion is actually about, byte-for-byte."""
    import inspect
    from services.api import accounts
    src = inspect.getsource(getattr(accounts, fn_name))
    lines = [ln.split("#", 1)[0] if "#" in ln and '"' not in ln and "'" not in ln else ln
             for ln in src.splitlines()
             if not ln.strip().startswith("#")]
    return "\n".join(lines)


def test_zero_is_the_only_no_responses(_app):
    assert suppression_reason(0) == "no_responses"


def test_below_the_floor_is_a_privacy_fact_not_a_participation_one(_app):
    """n=1,2 with KFLOOR=3. They answered. The reason must not say otherwise."""
    for n in range(1, KFLOOR):
        assert suppression_reason(n) == "below_anonymity_floor", n
        assert "No responses" not in SUPPRESSION_NOTE[suppression_reason(n)]


def test_at_or_above_the_floor_and_still_hidden_is_complement_inference(_app):
    """MERIDIAN'S HR: n=3 with KFLOOR=3 — AT the floor, not below it. It is
    hidden only because Supply Chain's n=2 would otherwise be recoverable by
    subtraction. Calling that 'below the anonymity floor' is a second mislabel,
    quieter than the first and just as untrue."""
    assert suppression_reason(3, by_partition=True) == "complement_inference"
    assert suppression_reason(30, by_partition=True) == "complement_inference"
    note = SUPPRESSION_NOTE["complement_inference"]
    assert "derivable by subtraction" in note


def test_a_withheld_slice_still_publishes_its_count(_app):
    """`n` is what makes 'withheld' credible rather than indistinguishable from
    silence, and it discloses nothing alone — the complement guard already
    guarantees two or more hidden slices, so the counts leave two unknowns
    against one total-equation."""
    b = suppression_block(3, by_partition=True)
    assert b["suppressed"] is True and b["n"] == 3
    assert b["reason"] == "complement_inference" and b["note"]


def test_every_reason_has_a_note_and_no_note_is_reused(_app):
    for r in ("no_responses", "below_anonymity_floor", "complement_inference"):
        assert SUPPRESSION_NOTE[r].strip()
    assert len(set(SUPPRESSION_NOTE.values())) == 3, "two states sharing a sentence is the bug"


def test_meridian_cycle_37_partition_reproduced(_app):
    """The exact shape that produced the false annotation: Supply Chain n=2 is
    the only slice under the floor, which forces HR (n=3, the smallest shown) to
    be hidden too. Each must now explain itself with its OWN reason."""
    depts = {
        "Finance": {"n_participants": 9, "cei": 6.0233},
        "Operations": {"n_participants": 6, "cei": 6.3816},
        "Sales & Marketing": {"n_participants": 6, "cei": 6.6658},
        "Technology": {"n_participants": 4, "cei": 6.5085},
        "HR": {"n_participants": 3, "cei": 6.72},
        "Supply Chain": {"n_participants": 2, "cei": 5.9},
    }
    status = _partition_status(depts)
    assert status["Supply Chain"] == "suppress" and status["HR"] == "suppress"
    assert sum(1 for s in status.values() if s == "suppress") >= 2, "complement guard"

    out = _apply_dept_kfloor(depts)
    assert out["Supply Chain"]["reason"] == "below_anonymity_floor"
    assert out["HR"]["reason"] == "complement_inference", \
        "HR is AT the floor (3 == KFLOOR); it is hidden to cover Supply Chain"
    for k in ("HR", "Supply Chain"):
        assert out[k].get("cei") is None, "the VALUE must still be gone"
        assert "No responses" not in out[k]["note"]
    for k in ("Finance", "Operations", "Sales & Marketing", "Technology"):
        assert out[k]["cei"] == depts[k]["cei"], "scored departments unchanged"
        assert out[k].get("suppressed") is not True


def test_the_trend_no_longer_zeroes_the_count_to_hide_a_value(_app):
    """Guards the exact regression. `cei_val, npart = None, 0` in the
    complement branch is what made the annotation lie; the value is hidden via
    `forced` now, and npart keeps the truth."""
    # CODE only — the comment explaining the old line quotes it verbatim, and a
    # naive substring search over the source flags the explanation as the bug.
    assert "cei_val, npart = None, 0" not in _code_of("assessment_summary"), \
        "zeroing the count is back"
    assert "cei_val, forced = None, True" in _code_of("assessment_summary")


def test_the_trend_derives_its_reason_from_the_shared_helper(_app):
    """Fixed at the source once — the trend, the slice and the CEI cards to come
    all read the same function, so the three states cannot drift apart again."""
    src = _code_of("assessment_summary")
    assert "suppression_block(npart" in src
    assert '"no_responses" if npart == 0' not in src, "the local ternary is back"
