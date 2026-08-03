"""A per-unit price that rounds to zero is not a small price — it is no answer.

⭐⭐ THE FIGURE ITSELF WAS NEVER MISSING. Meridian's Value / share arrived in
every payload, on every surface, correct for the data it was given. What reached
the reader was "$0.00", because a two-decimal formatter collapses anything under
half a cent — and a zero share price does not read as "check this number", it
reads as a finished answer.

⭐ THREE SURFACES RENDERED THE SAME ZERO: the valuation card, the board report
and the PDF. Each formatted correctly by its own lights. The class is the
formatter's contract, not any one call site, which is why the rule lives in
`report_format` rather than at three call sites.
"""
from services.api.report_format import DASH, number, per_unit

# Meridian's own figure: 2,784.740355m of nonmarketable equity over a share
# count stored in the wrong unit. See tests/unit/test_value_per_share_units.py.
MERIDIAN_PER_SHARE = 0.002785


def test_the_old_formatter_really_did_render_a_zero():
    """⭐ THE DEFECT, PINNED. If this ever stops being true the rule below has
    lost its reason and should be re-argued, not quietly kept."""
    assert number(MERIDIAN_PER_SHARE, 2) == "0.00"


def test_a_nonzero_price_never_renders_as_zero():
    out = per_unit(MERIDIAN_PER_SHARE, 2)
    assert out != "0.00"
    assert float(out.replace(",", "")) != 0.0


def test_it_widens_to_four_significant_figures_not_to_one():
    """⭐ "$0.003" clears the never-a-zero bar and is still useless: it cannot
    distinguish a unit error from a genuinely small price."""
    assert per_unit(MERIDIAN_PER_SHARE, 2) == "0.002785"


def test_an_ordinary_price_is_left_alone():
    """A value that does not round to zero keeps its normal precision — the rule
    must not turn every price into a wall of decimals."""
    assert per_unit(0.50, 2) == "0.50"
    assert per_unit(10.593758, 2) == "10.59"
    assert per_unit(2784.740355, 2) == "2,784.74"


def test_a_true_zero_stays_zero():
    """⭐ Widening the precision of a real zero would state a certainty nobody
    has. Zero is a fact; the defect was zero standing in for something else."""
    assert per_unit(0.0, 2) == "0.00"


def test_absence_is_still_absence():
    assert per_unit(None, 2) == DASH


def test_negative_values_keep_their_sign_and_their_magnitude():
    out = per_unit(-MERIDIAN_PER_SHARE, 2)
    assert out.startswith("-")
    assert out != "-0.00"


def test_the_pdf_value_per_share_row_uses_the_rule():
    """⭐ A rule nothing calls is not a rule. Asserted at the call site, by
    reading the source, because the PDF builder needs a full report to run."""
    import inspect

    from services.api import report_pdf

    src = inspect.getsource(report_pdf)
    row = [ln for ln in src.splitlines() if '"Value / share"' in ln]
    assert row, "the Value / share row has moved or been renamed"
    assert any("_per_unit(" in ln for ln in row), (
        f"the PDF still formats value per share with a plain number: {row}")
