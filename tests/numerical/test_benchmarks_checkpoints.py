"""Phase 7.5 checkpoint battery — Benchmarking engine. Index and implied
values certified by independent hand computation. REQ-TEST-011."""
import math
import pytest
from tests.fixtures.refcases import meridian, halcyon
from services.api.modules.benchmarks import engines as bm, data


PEERS = [
    {"name": "PeerA", "revenue": 1000, "ebit": 130, "net_income": 80,
     "total_assets": 1100, "total_equity": 500, "total_debt": 350, "cash": 90,
     "current_assets": 380, "current_liabilities": 240, "capex": 55,
     "revenue_prior": 950},
    {"name": "PeerB", "revenue": 1600, "ebit": 200, "net_income": 120,
     "total_assets": 1500, "total_equity": 700, "total_debt": 500, "cash": 120,
     "current_assets": 520, "current_liabilities": 330, "capex": 95,
     "revenue_prior": 1500},
    {"name": "PeerC", "revenue": 800, "ebit": 90, "net_income": 55,
     "total_assets": 750, "total_equity": 380, "total_debt": 200, "cash": 60,
     "current_assets": 260, "current_liabilities": 170, "capex": 40},
]


def test_meridian_vs_industrials_certified():
    r = bm.compare(meridian(), sector="Industrials")
    assert abs(r["benchmark_performance_index"] - 142.62) < 0.05
    assert r["verdict"] == "outperforming"
    rows = {x["kpi"]: x for x in r["kpis"]}
    # implied EBIT = 0.12 * 1380 = 165.6; excess = 234.6 - 165.6 = 69.0
    assert abs(rows["ebit_margin"]["implied_value"] - 165.6) < 1e-6
    assert abs(rows["ebit_margin"]["excess"] - 69.0) < 1e-6
    assert rows["ebit_margin"]["score"] == round(0.17 / 0.12, 4)
    assert r["all_checkpoints_pass"] is True


def test_index_is_weighted_geometric_mean():
    r = bm.compare(meridian(), sector="Industrials")
    scored = [x for x in r["kpis"] if x["status"] == "scored"]
    ws = sum(x["weight"] for x in scored)
    idx = 100 * math.exp(sum(x["weight"] * math.log(x["score"])
                             for x in scored) / ws)
    assert abs(r["benchmark_performance_index"] - round(idx, 2)) < 0.01


def test_direction_inversion_lower_is_better():
    r = bm.compare(meridian(), sector="Industrials")
    de = [x for x in r["kpis"] if x["kpi"] == "debt_to_equity"][0]
    # lower D/E than sector -> score = bench/actual = 0.9/0.668693 > 1 -> green
    assert de["score"] == round(0.9 / 0.668693, 4)
    assert de["rag"] == "green"


def test_scores_clamped_and_context_unscored():
    r = bm.compare(meridian(), sector="Industrials")
    for x in r["kpis"]:
        if x["status"] == "scored":
            assert 0.5 <= x["score"] <= 1.5
    capex = [x for x in r["kpis"] if x["kpi"] == "capex_pct_revenue"][0]
    assert capex["status"] == "context" and capex["rag"] is None


def test_rag_thresholds_published_rule():
    """Halcyon vs Technology - Software: weaker on most KPIs -> reds appear
    and the published thresholds hold row by row."""
    r = bm.compare(halcyon(), sector="Technology — Software")
    for x in r["kpis"]:
        if x["status"] != "scored":
            continue
        s = x["score"]
        expected = ("green" if s >= data.RAG_GREEN
                    else "amber" if s >= data.RAG_AMBER else "red")
        assert x["rag"] == expected
    assert r["benchmark_performance_index"] < 100
    assert r["verdict"] in ("underperforming", "in line with")


def test_custom_peer_set_certified():
    r = bm.compare(meridian(), peers=PEERS)
    assert r["source"]["kind"] == "peers"
    rows = {x["kpi"]: x for x in r["kpis"]}
    # hand: peer EBIT margins 0.13, 0.125, 0.1125 -> mean 0.1225
    assert abs(rows["ebit_margin"]["benchmark"] - 0.1225) < 1e-6
    # growth only from PeerA (50/950) and PeerB (100/1500); PeerC lacks prior
    g = (50/950 + 100/1500) / 2
    assert abs(rows["revenue_growth"]["benchmark"] - round(g, 6)) < 1e-6
    assert rows["revenue_growth"]["peer_coverage"] == 2
    assert abs(r["benchmark_performance_index"] - 124.01) < 0.05


def test_peer_set_needs_two():
    with pytest.raises(ValueError):
        bm.compare(meridian(), peers=[PEERS[0]])


def test_unknown_sector_raises():
    with pytest.raises(KeyError):
        bm.compare(meridian(), sector="Zeppelin Manufacturing")


def test_narrative_words_match_numbers():
    r = bm.compare(meridian(), sector="Industrials")
    text = " ".join(r["narrative"])
    assert "142.62" in text and "outperforming" in text
    assert "implies EBIT of USD 165.6" in text and "234.6" in text
    assert "not scored" in text          # context KPI explained in words
