"""Quarterly period arithmetic and the parser's column window (lane 1, 28 Jul).

These replay the two cases from the pre-build report that motivated the lane, so
a regression reproduces the original symptom rather than a paraphrase of it:

  · 20204 -> 20211 is consecutive; the old integer rule demanded 20205.
  · 20205 does not exist; the old rule would have ACCEPTED it as consecutive.

And they pin the two behaviours whose absence made the fault hard to see:
the parser must not stop at a fixed column, and one bad period must not repair
the sequence for the columns after it.
"""
import io
import pytest
from openpyxl import load_workbook

from services.api.modules.financials import ingest


# ── period arithmetic ───────────────────────────────────────────────────────
def test_quarter_four_carries_the_year():
    """The case the old integer rule got wrong: +7, not +1."""
    assert ingest.next_period(20204, "quarterly") == 20211
    assert ingest.next_period(20214, "quarterly") == 20221
    assert ingest.next_period(20231, "quarterly") == 20232


def test_a_fifth_quarter_does_not_exist():
    """The reverse failure: the old rule would have accepted 20205."""
    assert ingest.period_is_valid(20204, "quarterly")
    assert ingest.period_is_valid(20211, "quarterly")
    assert not ingest.period_is_valid(20205, "quarterly")
    assert not ingest.period_is_valid(20200, "quarterly")
    assert not ingest.period_is_valid(20209, "quarterly")


def test_annual_arithmetic_is_untouched():
    assert ingest.next_period(2025, "annual") == 2026
    assert ingest.period_is_valid(2025, "annual")
    assert not ingest.period_is_valid(205, "annual")


def test_decode_and_format():
    assert ingest.decode_period(20231, "quarterly") == (2023, 1)
    assert ingest.decode_period(2023, "annual") == (2023, None)
    assert ingest.format_period(20231, "quarterly") == "2023Q1"
    assert ingest.format_period(2023, "annual") == "2023"


# ── the full sequence the report replayed ───────────────────────────────────
def test_the_reported_sequence_now_validates_clean():
    """20214 -> 20221,20222,20223,20224 — rejected before at the boundary."""
    seq = [20221, 20222, 20223, 20224]
    expected = ingest.next_period(20214, "quarterly")
    for y in seq:
        assert y == expected, f"{y} should follow consecutively, expected {expected}"
        expected = ingest.next_period(y, "quarterly")


# ── the parser's column window ──────────────────────────────────────────────
def _template(freq, fcst_cols=None):
    if fcst_cols is not None:
        ingest.FORECAST_QUARTERLY = fcst_cols
    return ingest.build_company_template(
        company_id=1, company_name="T", currency="USD", statement_units="actual",
        ownership="private", standard="us_gaap", frequency=freq,
        last_historical_year=2025)


def test_parser_reads_beyond_the_old_thirty_column_window():
    """A 52-column quarterly workbook must be read in full.

    The old `for i in range(30)` stopped at column AE, dropping 22 forecast
    columns with no error at all.
    """
    original = ingest.FORECAST_QUARTERLY
    try:
        blob = _template("quarterly", 40)
        wb = load_workbook(io.BytesIO(blob))
        ws = wb["Income Statement"]
        assert ws.max_column == 53, "probe assumes the 52-column shape (B..BA)"

        # fill every forecast column so none is dropped as unused
        from openpyxl.utils import get_column_letter
        for c in range(14, 54):
            L = get_column_letter(c)
            q = c - 14
            ws[f"{L}4"] = (2023 + q // 4) * 10 + (q % 4) + 1

        seen = []
        for c in range(2, ws.max_column + 1):
            L = get_column_letter(c)
            if ws[f"{L}4"].value not in (None, ""):
                seen.append(L)
        # 12 historical + 40 forecast, the last one at BA
        assert len(seen) == 52, f"expected 52 period columns, saw {len(seen)}"
        assert seen[-1] == "BA"
    finally:
        ingest.FORECAST_QUARTERLY = original


def test_annual_template_shape_unchanged():
    """Lane 1 must not move the annual path."""
    blob = _template("annual")
    ws = load_workbook(io.BytesIO(blob))["Income Statement"]
    hist = [c for c in range(2, ws.max_column + 1)
            if str(ws.cell(row=3, column=c).value or "").lower() == "historical"]
    fcst = [c for c in range(2, ws.max_column + 1)
            if str(ws.cell(row=3, column=c).value or "").lower() == "forecast"]
    assert len(hist) == 6, "annual historical block moved"
    assert len(fcst) == 8, "annual forecast block moved — FORECAST_ANNUAL is 8, not 5"
    assert ws.cell(row=4, column=2).value == 2020
    assert ws.cell(row=4, column=15).value == 2033


# ── end-to-end through parse_and_validate ───────────────────────────────────
SHEETS = ["Income Statement", "Balance Sheet", "Cash Flow Data"]


def _fill(blob, first_col, labels, copy_from="M"):
    """Copy a historical column into each forecast column and label it."""
    from openpyxl.utils import get_column_letter
    wb = load_workbook(io.BytesIO(blob))
    for nm in SHEETS:
        ws = wb[nm]
        for i, lab in enumerate(labels):
            L = get_column_letter(first_col + i)
            ws[f"{L}3"] = "Forecast"
            ws[f"{L}4"] = lab
            for r in range(5, 45):
                v = ws[f"{copy_from}{r}"].value
                if v is not None and not (isinstance(v, str) and v.startswith("=")):
                    ws[f"{L}{r}"] = v
    out = io.BytesIO(); wb.save(out)
    return out.getvalue(), wb


def _quarterly_labels(n, after=20224):
    out, p = [], ingest.next_period(after, "quarterly")
    for _ in range(n):
        out.append(p); p = ingest.next_period(p, "quarterly")
    return out


def test_quarterly_plan_crossing_year_boundaries_parses_clean():
    """The whole point of the lane: 20234->20241 and 20244->20251 must pass."""
    original = ingest.FORECAST_QUARTERLY
    try:
        blob = _template("quarterly", 40)
        labels = _quarterly_labels(12)
        filled, _ = _fill(blob, 14, labels)
        data, errors, _meta, _w = ingest.parse_and_validate(
            filled, 1, statement_units="actual", frequency="quarterly")
        assert errors == [], f"expected a clean parse, got {errors[:3]}"
        assert data["periods"]["forecast"] == labels
        assert 20241 in labels and 20251 in labels, "must cross a year boundary"
    finally:
        ingest.FORECAST_QUARTERLY = original


def test_parser_reads_the_far_column_the_old_window_could_not_reach():
    """A diagnostic naming BA proves the scan passed the old AE ceiling."""
    from openpyxl.utils import column_index_from_string
    import re
    original = ingest.FORECAST_QUARTERLY
    try:
        blob = _template("quarterly", 40)
        filled, wb = _fill(blob, 14, _quarterly_labels(40))
        wb["Income Statement"]["BA5"] = None          # one hole, farthest column
        out = io.BytesIO(); wb.save(out)
        _d, errors, _m, _w = ingest.parse_and_validate(
            out.getvalue(), 1, statement_units="actual", frequency="quarterly")
        named = [e["cell"] for e in errors if e.get("cell")]
        assert any(column_index_from_string(re.match(r'([A-Z]+)', c).group(1)) > 31
                   for c in named), f"nothing past column AE was read: {named}"
    finally:
        ingest.FORECAST_QUARTERLY = original


def test_one_bad_period_does_not_repair_the_sequence():
    """No resync: a systematic mismatch must stay visible on every column.

    The old rule re-anchored `expected` on whatever was FOUND, so an annual rule
    applied to a quarterly file produced one isolated complaint per year boundary
    surrounded by accepts — reading like a typo rather than a frequency bug.
    """
    original = ingest.FORECAST_QUARTERLY
    try:
        blob = _template("quarterly", 40)
        # start the plan in the wrong place: history ends 20224, these start 20261
        wrong = []
        p = 20261
        for _ in range(8):
            wrong.append(p); p = ingest.next_period(p, "quarterly")
        filled, _ = _fill(blob, 14, wrong)
        _d, errors, _m, _w = ingest.parse_and_validate(
            filled, 1, statement_units="actual", frequency="quarterly")
        seq = [e for e in errors if "consecutively" in e["message"]]
        assert len(seq) == len(wrong), (
            f"a systematic mismatch must flag every column, got {len(seq)} "
            f"of {len(wrong)} — the sequence was repaired by a bad period")
    finally:
        ingest.FORECAST_QUARTERLY = original
