"""§7.31 in the board pack — one formatter, asserted across BOTH artifacts.

The PDF and the PPTX render the same `board_report()` payload and each had its
own money formatter. They disagreed, and a board reads both documents:

    payload 4.07   ->  PDF "$4.1M"   PPTX "$4M"
    payload 82.64  ->  PDF "$82.6M"  PPTX "$83M"

⭐ THE CROSS-ARTIFACT ASSERTION IS THE POINT. Testing each renderer's formatter
"correct in isolation" is what allowed the divergence: both were self-consistent.
The tests below take one payload through BOTH entry points and require the
strings to be equal.
"""
import pytest

from services.api import report_format as rf
from services.api.report_pdf import _money as pdf_money, _pc as pdf_pct, _num as pdf_num
from services.api.reporting import _big as pptx_money, _fmt as pptx_fmt


# ── the discriminating cases ────────────────────────────────────────────────
@pytest.mark.parametrize("a,b", [(3.6, 4.0), (4.0, 4.4), (3.6, 4.4),
                                 (4.01, 4.99), (17.4, 17.5)])
def test_values_a_reader_must_tell_apart_render_distinctly(a, b):
    """`_big`'s zero decimals collapsed 3.6, 4.0 and 4.4 into "$4M" — the same
    information loss `shortMoney` produced on Scenario Analysis."""
    assert rf.money(a, "$") != rf.money(b, "$"), \
        f"{a} and {b} both render {rf.money(a, '$')!r}"


def test_the_three_collapsed_values_are_now_three_strings():
    got = {rf.money(v, "$") for v in (3.6, 4.0, 4.4)}
    assert len(got) == 3, got
    assert got == {"$3.60M", "$4.00M", "$4.40M"}


# ── the cross-artifact identity ─────────────────────────────────────────────
PAYLOAD = [4.07, 4.99, 4.01, 3.6, 4.4, 82.64, 17.5, 0.5, -12.75, 1250.0, 0.0, None]


@pytest.mark.parametrize("v", PAYLOAD)
def test_pdf_and_pptx_render_the_same_money_string(v):
    assert pdf_money(v, "$") == pptx_money(v, "$"), (
        f"payload {v}: PDF {pdf_money(v, '$')!r} vs PPTX {pptx_money(v, '$')!r}")


@pytest.mark.parametrize("v", [0.134, 0.0, -0.052, 1.0, None])
def test_pdf_and_pptx_render_the_same_percent_string(v):
    assert pdf_pct(v) == pptx_fmt(v, pct=True), (
        f"ratio {v}: PDF {pdf_pct(v)!r} vs PPTX {pptx_fmt(v, pct=True)!r}")


def test_both_artifacts_use_the_same_function_object():
    """⭐ EQUAL OUTPUT IS NOT ONE DEFINITION. Two functions agreeing today is the
    state this whole lane exists to remove, so assert identity of the callee, not
    of the strings."""
    import services.api.reporting as rep
    # ⭐ ASSERT THE NAME THE RENDERER CALLS, NOT THE IMPORT BESIDE IT. The first
    # version checked `rep._big_money is rf.money` — the import — which stays
    # true while `_big` is quietly redefined below it. A mutation that re-grew a
    # local `_big` survived exactly there.
    assert rep._big is rf.money, "the PPTX has its own money formatter again"
    assert pdf_money is rf.money, "the PDF has its own money formatter again"
    assert pdf_pct is rf.percent
    assert rep._pct is rf.percent


# ── the shared primitives ───────────────────────────────────────────────────
def test_money_is_two_decimals_and_carries_the_unit():
    assert rf.money(4.07, "$") == "$4.07M"
    assert rf.money(82.64, "$") == "$82.64M"


def test_the_billion_tier_divides_by_a_thousand_because_input_is_millions():
    assert rf.money(1250.0, "$") == "$1.25B"
    assert rf.money(999.99, "$") == "$999.99M"


def test_none_is_a_dash_everywhere():
    assert rf.money(None, "$") == "—"
    assert rf.percent(None) == "—"
    assert rf.number(None) == "—"
    assert rf.kpi_value({"format": "percent", "current": None}) == "—"


def test_negatives_put_the_sign_BEFORE_the_symbol_as_the_screen_does():
    """The frontend writes `${sign}${sym}${body}`. This emitted "$-4.40M" — the
    same number in a third spelling, on the most authoritative artifact."""
    assert rf.money(-4.4, "$") == "-$4.40M"
    assert rf.money(-1250.0, "$") == "-$1.25B"
    assert rf.money(-0.5, "$") == "-$500.00k"


def test_percent_takes_a_RATIO_not_a_scaled_percentage():
    assert rf.percent(0.134) == "13.4%"
    assert rf.percent(13.4) == "1340.0%", "the failure mode worth pinning"


def test_currency_symbols_are_one_map_and_cover_what_the_pdf_knew():
    for code, want in (("USD", "$"), ("EUR", "€"), ("GBP", "£"),
                       ("JPY", "¥"), ("CHF", "CHF "), ("CAD", "$"), ("AUD", "$")):
        assert rf.currency_symbol(code) == want, code


def test_an_unknown_currency_is_labelled_not_left_bare():
    """The PPTX's old inline map returned "" for anything outside USD/EUR/GBP, so
    a SEK figure rendered with no unit at all."""
    assert rf.currency_symbol("SEK") == "SEK "
    assert rf.money(4.4, rf.currency_symbol("SEK")) == "SEK 4.40M"


# ── rank 2: per-metric format SELECTION ─────────────────────────────────────
def test_kpi_selection_routes_each_declared_format_to_its_own_shape():
    """⭐ A MARGIN RENDERED AS MONEY READS '$0.13M'; MONEY AS A PERCENT READS
    '13.4%'. Both plausible, both wrong by orders of magnitude."""
    assert rf.kpi_value({"format": "percent", "current": 0.134}, "$") == "13.4%"
    assert rf.kpi_value({"format": "ratio", "current": 1.2345}, "$") == "1.234"
    assert rf.kpi_value({"format": "money", "current": 4.07}, "$") == "$4.07M"


def test_an_unknown_kpi_format_falls_through_to_money_as_it_always_did():
    assert rf.kpi_value({"format": "widgets", "current": 4.07}, "$") == "$4.07M"
    assert rf.kpi_value({"current": 4.07}, "$") == "$4.07M"


def test_ratio_keeps_three_decimals_and_percent_one():
    assert rf.kpi_value({"format": "ratio", "current": 1.0}, "$") == "1.000"
    assert rf.kpi_value({"format": "percent", "current": 0.5}, "$") == "50.0%"


def test_plan_selection_reads_the_block_its_kind_names():
    st = {"stochastic": {"revenue": {"plan": 100.0}},
          "deterministic": {"revenue": 55.0}}
    assert rf.plan_value(st, "revenue", "stoch") == 100.0
    assert rf.plan_value(st, "revenue", "det") == 55.0
    assert rf.plan_value(st, "revenue", None) == 55.0


def test_the_pdf_uses_the_shared_kpi_and_plan_selectors():
    import services.api.report_pdf as rp
    assert rp._kpi_value is rf.kpi_value
    assert rp._plan_value is rf.plan_value


# ── tier boundaries, asserted against the FRONTEND's rule ───────────────────
def _frontend_tier(actual: float) -> str:
    """`formatWithCode` in src/lib/currency.ts, transcribed. The board pack takes
    MILLIONS, so the assertions below convert; the boundaries themselves are the
    screen's and must not be restated in a form that could drift from it."""
    a = abs(actual)
    if a >= 1e9:
        return "B"
    if a >= 1e6:
        return "M"
    if a >= 1e3:
        return "k"
    return ""


@pytest.mark.parametrize("millions", [
    0.0, 0.0009, 0.001, 0.5, 0.999999, 1.0, 4.07, 999.99, 1000.0, 1250.0,
    -0.5, -1.0, -1250.0,
])
def test_the_pack_lands_in_the_same_tier_as_the_screen(millions):
    actual = millions * 1_000_000
    want = _frontend_tier(actual)
    got = rf.money(millions, "$")
    suffix = got[-1] if got[-1] in "BMk" else ""
    assert suffix == want, f"{millions}M -> {got!r}, screen tier {want!r}"


def test_the_k_tier_matches_the_screen_value_not_just_the_letter():
    """0.5M is 500,000 actual; the screen renders (abs/1e3).toFixed(2) + 'k'."""
    assert rf.money(0.5, "$") == "$500.00k"
    assert rf.money(0.001, "$") == "$1.00k"


def test_sub_thousand_amounts_drop_the_tier_entirely():
    assert rf.money(0.0005, "$") == "$500.00"
    assert rf.money(0.0, "$") == "$0.00"


# ── item 2: a non-USD payload, end to end through both artifacts ────────────
@pytest.mark.parametrize("code,sym", [("EUR", "€"), ("GBP", "£"), ("JPY", "¥"),
                                      ("CHF", "CHF "), ("SEK", "SEK ")])
def test_a_non_usd_payload_renders_identically_in_both_artifacts(code, sym):
    s = rf.currency_symbol(code)
    assert s == sym, f"{code} -> {s!r}"
    for v in (4.07, 0.5, 1250.0, -4.4):
        assert pdf_money(v, s) == pptx_money(v, s), code
        assert s in pdf_money(v, s), f"{code} rendered without its marker"


def test_no_currency_ever_renders_a_bare_number():
    """The PPTX's old map returned "" for anything outside USD/EUR/GBP, so a SEK
    figure carried no marker at all — indistinguishable from a unitless score."""
    for code in ("USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "SEK", "ZAR", "XYZ"):
        out = rf.money(4.07, rf.currency_symbol(code))
        assert not out[0].isdigit(), f"{code} rendered bare: {out!r}"
        assert out.rstrip("M0123456789.,") != "", f"{code} has no marker: {out!r}"


def test_an_empty_currency_code_is_the_only_bare_case_and_is_deliberate():
    assert rf.currency_symbol("") == ""
    assert rf.currency_symbol(None) == ""


# ── item 4: the score formatter ─────────────────────────────────────────────
def test_score_is_not_money_and_carries_no_symbol_or_tier():
    assert rf.score(4.07) == "4.1"
    assert rf.score(1250.0) == "1,250.0"
    assert "M" not in rf.score(4.07) and "$" not in rf.score(4.07)


def test_score_precision_is_a_caller_choice_but_the_function_is_not():
    assert rf.score(1.234, 0) == "1"
    assert rf.score(1.234, 2) == "1.23"
    assert rf.score(None) == "—"


def test_chart_bars_uses_the_shared_score_formatter():
    import services.api.reporting as rep
    import inspect
    assert rep._score is rf.score
    sig = inspect.signature(rep.chart_bars)
    assert "decimals" in sig.parameters, "chart_bars still takes a format string"
    assert "fmt" not in sig.parameters


def test_no_raw_number_format_strings_remain_in_the_deck_builder():
    """Six spellings of 'how to render a score' lived at call sites."""
    import services.api.reporting as rep, re
    src = inspect_source(rep)
    assert not re.search(r'fmt\s*=\s*"\{', src), "a call-site format string is back"


def inspect_source(mod):
    import inspect
    return inspect.getsource(mod)
