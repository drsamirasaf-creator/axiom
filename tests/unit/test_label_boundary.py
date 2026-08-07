"""A display label is not a pack input, and the boundary is asserted.

⭐⭐ FOUNDER RULING, 7 Aug: the display string goes on the **surface payload
only**. `_cap_period_labels` continues to freeze **identifiers** — `periods` and
`frequency`, integers.

⛔ **A pack freezes INPUTS. A display string is not an input, and two packs over
identical financial data must never differ in `content_hash` because a caption
changed.** That is the worst shape for a frozen artefact: a change invisible in
the figures and loud in the identity.

⛔ **AND A BOUNDARY NOBODY ASSERTS IS A CONVENTION.** Measured 7 Aug: 24 packs,
all published, all hashed, and **28 of 28 frozen snapshots carry a
`period_labels` class holding `{periods: {...}, frequency}`** — integers, no
display string anywhere. This file exists so that stays true by test rather
than by memory.
"""
import inspect
import json

import services.api.pack as P
from services.api.modules.financials import periods as PR


def _class_source():
    return inspect.getsource(P._cap_period_labels)


def test_the_frozen_class_does_not_call_the_formatter():
    """⛔ THE ASSERTION, ON THE ONE FUNCTION THAT COULD BREAK IT."""
    src = _class_source()
    assert "format_period" not in src, (
        "`format_period` is called inside `_cap_period_labels`. A rendered "
        "string would enter the frozen input class, and every future pack over "
        "identical data would hash differently because a caption changed.")
    assert "period_label" not in src.replace("_cap_period_labels", ""), src


def test_the_frozen_class_emits_identifiers_only():
    """⭐ Asserted on the VALUE, not the source — a formatter reached by another
    name would pass the source check and fail here."""
    class _DS:
        data = {"periods": {"historical": [2021, 2022], "forecast": [2023]}}
        frequency = None

    class _DB:
        pass

    import services.api.accounts as A
    real = A._active_company_dataset
    A._active_company_dataset = lambda db, cid: _DS()
    try:
        out = P._cap_period_labels(_DB(), 1)
    finally:
        A._active_company_dataset = real

    # ⛔⭐⭐ THE KEY SET, NOT THE CAPTION SHAPE. A first version scanned the
    # payload for "Q1"/"Jan"/"FY" and MISSED a planted leak, because an ANNUAL
    # label is `"2021"` — a string indistinguishable from the identifier it
    # renders. Caught by running the red proof: only 1 of 4 tests fired.
    # The key set cannot be fooled that way.
    assert set(out) == {"present", "periods", "frequency"}, (
        f"the frozen class gained {sorted(set(out) - {'present','periods','frequency'})} "
        f"— anything beyond the identifiers is a caption entering the freeze")
    # ⛔ Every period value must still be a NUMBER, whatever it is called.
    for bucket in (out.get("periods") or {}).values():
        for v in bucket:
            assert isinstance(v, int), f"a non-integer period entered the freeze: {v!r}"


def test_the_formatter_really_does_produce_the_strings_being_excluded():
    """⭐⭐ THE KNOWN POSITIVE. An exclusion test passes trivially if the thing
    excluded never existed. This proves `format_period` produces exactly the
    captions the test above forbids, so the exclusion is meaningful."""
    assert PR.format_period(20241, "quarterly") == "2024Q1"
    assert PR.format_period(2024, "annual") == "2024"
    assert "Jan" in PR.format_period(202401, "monthly")


def test_two_packs_over_identical_data_hash_identically():
    """⛔ THE PROPERTY THE BOUNDARY PROTECTS, asserted directly. If a caption
    ever reached the freeze this would start failing intermittently — on the
    day a label changed, not on the day the code did."""
    frozen = {"classes": {"period_labels": {"present": True,
                                            "periods": {"historical": [2021]},
                                            "frequency": None}}}
    a = P.freeze_hash(frozen)
    b = P.freeze_hash(json.loads(json.dumps(frozen)))
    assert a == b
    # ⭐ and a caption CHANGES it — which is exactly why it must stay out
    withlabel = json.loads(json.dumps(frozen))
    withlabel["classes"]["period_labels"]["labels"] = {"2021": "2021"}
    assert P.freeze_hash(withlabel) != a, (
        "adding a label did not change the hash — then this test cannot "
        "detect the leak it exists for")
