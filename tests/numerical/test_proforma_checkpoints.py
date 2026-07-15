"""Phase 17 battery: the stochastic three-statement pro forma. REQ-TEST-023."""
from tests.fixtures.refcases import meridian, halcyon
from services.api.modules.financials import proforma as pf


def test_statements_balance_every_year():
    r = pf.stochastic_statements(meridian())
    assert all(s["balance_ok"] for s in r["statements"])
    assert r["all_checkpoints_pass"] is True
    assert r["forecast_years"] == [2026, 2027, 2028, 2029, 2030]


def test_plan_line_probabilities_near_half():
    """The plan sits at the simulated median, so single-year attainment of
    each line is roughly a coin toss (seeded, so exact)."""
    r = pf.stochastic_statements(meridian())
    s1 = r["statements"][0]["stochastic"]
    for line in ("revenue", "net_income", "fcff", "ebit"):
        p = s1[line]["p_meets_plan"]
        assert 0.40 < p < 0.60, (line, p)
    # expected ~ plan for the first year
    assert abs(s1["revenue"]["expected"] - s1["revenue"]["plan"]) < 5.0


def test_cumulative_far_below_annual():
    r = pf.stochastic_statements(meridian())
    ann = r["statements"][0]["stochastic"]["revenue"]["p_meets_plan"]
    cum = r["cumulative_attainment"]["revenue"]["p_meets_plan_every_year"]
    assert cum < ann                     # every-year is much harder
    assert 0.0 <= cum <= 0.10            # ~0.5^5-ish, seeded


def test_income_statement_articulates():
    """EBIT = revenue - cogs - opex - D&A; net income = EBT - tax; on plan."""
    r = pf.stochastic_statements(meridian())
    s = r["statements"][0]
    st, det = s["stochastic"], s["deterministic"]
    ebit_check = st["revenue"]["plan"] - det["cogs"] - det["opex"] - det["da"]
    assert abs(ebit_check - st["ebit"]["plan"]) < 0.1
    ni_check = det["ebt"] - det["tax"]
    assert abs(ni_check - st["net_income"]["plan"]) < 0.1


def test_private_company_projects():
    r = pf.stochastic_statements(halcyon())
    assert r["mode"] == "auto_forecast"
    assert all(s["balance_ok"] for s in r["statements"])
    assert r["all_checkpoints_pass"] is True


def test_cagr_reasonable():
    r = pf.stochastic_statements(meridian())
    assert abs(r["plan_cagr"]["revenue"] - 0.07) < 0.005    # 7% plan growth
