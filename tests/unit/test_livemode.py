"""G13 — the Stripe livemode flag, persisted and classified.

⭐⭐ THE ELEVENTH WRONG ENTRY IS THE SPEC. A test-mode subscription was recorded
identically to a real one, so the ledger recorded the operator's own test account
as a live paying customer — and NO MEASUREMENT AGAINST THE CODEBASE COULD HAVE
CAUGHT IT, because the data said exactly what the ledger said.

⭐ THESE TESTS ASSERT THE THREE THINGS THAT WOULD HAVE PREVENTED IT: the flag is
persisted from the event, absence stays absent, and the mode is never re-derived
from the API key.
"""
import ast
import os
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest

from services.api.modules.billing import engine as B
from tests.codeonly import code_only


class _U:
    """A user stand-in — apply_subscription_state is pure w.r.t. Stripe."""
    def __init__(self, **kw):
        self.plan = "free"
        self.companies_allowed = 0
        self.stripe_customer_id = None
        self.stripe_subscription_id = None
        self.subscription_status = None
        self.subscription_livemode = None
        self.livemode_source = None
        self.__dict__.update(kw)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE FLAG IS PERSISTED FROM THE EVENT
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("livemode", [True, False])
def test_livemode_is_persisted_with_its_source(livemode):
    u = _U()
    out = B.apply_subscription_state(u, status="active", quantity=1,
                                     livemode=livemode,
                                     livemode_source="webhook")
    assert u.subscription_livemode is livemode
    assert u.livemode_source == "webhook"
    assert out["livemode"] is livemode


def test_a_TEST_subscription_is_now_DISTINGUISHABLE_from_a_real_one():
    """⭐⭐ THE WHOLE POINT. Two accounts identical on every field the ledger
    read, separated only by the flag that was never stored."""
    live = _U(); test = _U()
    B.apply_subscription_state(live, status="active", quantity=1,
                               livemode=True, livemode_source="webhook")
    B.apply_subscription_state(test, status="active", quantity=1,
                               livemode=False, livemode_source="webhook")
    # everything the eleventh wrong entry looked at is IDENTICAL…
    assert live.plan == test.plan == "business"
    assert live.subscription_status == test.subscription_status == "active"
    # …and the accounts are now distinguishable
    assert live.subscription_livemode is not test.subscription_livemode


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ ABSENCE PROPAGATES — NULL MEANS UNKNOWN, NEVER FALSE
# ═══════════════════════════════════════════════════════════════════════════

def test_an_event_without_the_flag_leaves_it_UNKNOWN_not_false():
    """⭐⭐ WRITING False HERE WOULD ASSERT 'THIS IS A TEST ACCOUNT' ON NO
    EVIDENCE — the same inference-from-appearance that caused the error, run
    backwards. An unknown account must not be classed as test."""
    u = _U()
    B.apply_subscription_state(u, status="active", quantity=1)   # no livemode
    assert u.subscription_livemode is None, \
        "an absent flag was resolved to a value"
    assert u.livemode_source is None


def test_an_established_flag_is_not_erased_by_a_later_event_that_lacks_one():
    u = _U()
    B.apply_subscription_state(u, status="active", quantity=1,
                               livemode=True, livemode_source="webhook")
    B.apply_subscription_state(u, status="past_due", quantity=1)  # no flag
    assert u.subscription_livemode is True, \
        "a flagless event erased an established mode"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ NEVER INFERRED FROM THE KEY
# ═══════════════════════════════════════════════════════════════════════════

def test_the_engine_never_derives_the_mode_from_the_API_KEY():
    """⭐⭐ INFERRING IT AT READ TIME WOULD REPEAT THE CLASS THIS CLOSES. The key
    can be rotated or the environment rebuilt; only the flag Stripe sent WITH THE
    EVENT records what the subscription actually was."""
    src = code_only(B)
    for banned in ("sk_test", "sk_live", "rk_test", "rk_live"):
        assert banned not in src, \
            f"billing engine inspects the key mode ({banned}) to decide livemode"


def test_every_apply_call_site_passes_the_EVENTS_flag_not_the_objects():
    """⭐ `event['livemode']`, not `obj['livemode']`. The event is the envelope
    Stripe signs; the object is payload that a replayed or crafted body could
    disagree with."""
    src = code_only(B)
    tree = ast.parse(src)
    calls = [n for n in ast.walk(tree)
             if isinstance(n, ast.Call)
             and getattr(n.func, "id", None) == "apply_subscription_state"]
    assert calls, "no call sites found — the guard would pass vacuously"
    passed = 0
    for c in calls:
        for kw in c.keywords:
            if kw.arg == "livemode":
                passed += 1
                got = ast.unparse(kw.value)
                assert got.startswith("event."), \
                    f"livemode taken from {got!r}, not from the event"
    assert passed == len(calls), \
        f"{len(calls) - passed} of {len(calls)} call sites pass no livemode"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE MODELS
# ═══════════════════════════════════════════════════════════════════════════

def test_both_subscription_surfaces_carry_the_flag():
    """⭐ TWO SURFACES, ONE CONCEPT — fixing one would leave the other able to
    reproduce the defect."""
    from services.api.accounts import Account
    from services.api.modules.identity.models import User
    assert User.__table__.c.subscription_livemode.nullable is True
    assert User.__table__.c.livemode_source is not None
    assert Account.__table__.c.livemode.nullable is True
    assert Account.__table__.c.livemode_source is not None


def test_the_columns_have_NO_server_default():
    """⭐⭐ A DEFAULT OF False WOULD CLASSIFY EVERY PRE-EXISTING ROW AS TEST on no
    evidence. Existing rows must come out of the migration UNKNOWN."""
    from services.api.accounts import Account
    from services.api.modules.identity.models import User
    for col in (User.__table__.c.subscription_livemode,
                Account.__table__.c.livemode):
        assert col.server_default is None, f"{col} carries a server default"
        assert col.default is None, f"{col} carries a default"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE GUARD, AND ITS KNOWN POSITIVE
# ═══════════════════════════════════════════════════════════════════════════

def _guard():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "ccc", "scripts/check-customer-counts.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_the_guard_FLAGS_an_unconstrained_customer_count():
    """⭐⭐ THE KNOWN POSITIVE. This is the exact shape that produced the
    eleventh wrong entry, and a guard that cannot flag it is decoration."""
    g = _guard()
    problems, sites = g.scan_source(g._CONTROL_BAD, "<t>")
    assert sites == 1, "the shape was not even recognised as a billing aggregate"
    assert problems, "the guard did not flag an unconstrained customer count"


def test_the_guard_ACCEPTS_a_livemode_constrained_count():
    g = _guard()
    problems, sites = g.scan_source(g._CONTROL_OK_FILTER, "<t>")
    assert sites == 1 and not problems


def test_the_guard_ACCEPTS_a_count_that_DECLARES_it_includes_test_accounts():
    """⭐ The rule is not 'exclude them', it is 'never do it silently'. A guard
    forbidding the honest case would be routed around."""
    g = _guard()
    problems, sites = g.scan_source(g._CONTROL_OK_MARKER, "<t>")
    assert sites == 1 and not problems


def test_the_guard_REPORTS_ITS_COVERAGE_because_zero_sites_exist_today():
    """⭐⭐ III.4 — '0 problems in 0 files' and '0 problems in 400 files' print
    the same tick. There are currently NO billing aggregates, so the guard must
    say so rather than print a bare pass."""
    src = open("scripts/check-customer-counts.py", encoding="utf-8").read()
    assert "aggregate(s) examined" in src
    assert "ZERO billing aggregates" in src, \
        "the guard does not disclose that it has no real site to protect"
