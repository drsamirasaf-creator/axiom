"""Phase 10 battery: platform content, the value-risk frontier, and the
re-forecast proposal. Frontier values certified from the seeded run.
REQ-TEST-014."""
import pytest
from tests.fixtures.refcases import meridian, halcyon
from services.api.modules.intelligence import engines as intel
from services.api.modules.twin import engines as twin
from services.api.modules.platform import content
from tests.numerical.test_twin_checkpoints import ACTUALS_2026


def test_frontier_certified_shape_and_values():
    f = intel.frontier(meridian())
    pareto = [p["de"] for p in f["points"] if p["pareto_efficient"]]
    assert pareto == [0.0, 0.25, 0.5, 0.75, 1.0, 1.25]
    by_de = {p["de"]: p for p in f["points"]}
    assert abs(by_de[1.25]["value_mean_ev"] - 2601.8) < 0.5      # seeded
    assert abs(by_de[0.0]["safety_tail_margin"] - 2089.1) < 0.5
    assert by_de[2.0]["pareto_efficient"] is False               # dominated
    assert f["all_checkpoints_pass"] is True


def test_frontier_lambda_spans_the_frontier():
    assert intel.frontier(meridian(), risk_aversion=0.0)["recommended"]["de"] == 1.25
    assert intel.frontier(meridian(), risk_aversion=1.0)["recommended"]["de"] == 0.0


def test_frontier_tradeoff_is_monotone_on_pareto_set():
    f = intel.frontier(meridian())
    ps = [p for p in f["points"] if p["pareto_efficient"]]
    values = [p["value_mean_ev"] for p in ps]
    margins = [p["safety_tail_margin"] for p in ps]
    assert values == sorted(values) and margins == sorted(margins, reverse=True)


def test_frontier_works_for_private_auto_forecast():
    f = intel.frontier(halcyon(), n_paths=400)
    assert f["mode"] == "auto_forecast"
    assert any(p["pareto_efficient"] for p in f["points"])


def test_frontier_validation():
    with pytest.raises(ValueError):
        intel.frontier(meridian(), risk_aversion=1.5)
    with pytest.raises(ValueError):
        intel.frontier(meridian(), de_grid=[0.5])


def test_reforecast_proposal_certified():
    child, _ = twin.sync(meridian(), 2026, ACTUALS_2026)
    rp = twin.reforecast_proposal(child)
    assert rp["remaining_years"] == [2027, 2028, 2029, 2030]
    # refit growth carries the 2026 miss: 0.077144, and proposed FCFF_2027
    # sits below the committed plan's
    assert abs(rp["drivers"]["revenue_growth"] - 0.077144) < 5e-5
    c0 = rp["comparison"][0]
    assert c0["fcff_proposed"] < c0["fcff_committed"]
    assert rp["all_checkpoints_pass"] is True


def test_reforecast_requires_remaining_years():
    with pytest.raises(ValueError):
        twin.reforecast_proposal(meridian() | {"periods": {
            "historical": meridian()["periods"]["historical"], "forecast": []}})


def test_platform_copy_complete():
    a = content.ABOUT
    assert a["contact"]["email"] == "samir@theregentfinancial.com"
    assert a["contact"]["firm"] == "Regent Financial"
    assert len(a["for_organizations"]["benefits"]) == 5
    assert "digital twin" in a["for_organizations"]["definition"]
    assert "Dynamic Corporate Transformation" in a["for_dct"]["definition"]
    # every nav page has the three explainer fields
    for key, page in content.PAGES.items():
        for field in ("title", "what", "benefit", "start"):
            assert page.get(field), f"{key}.{field}"
    assert content.intro_video_url() is None       # env unset -> honest null
