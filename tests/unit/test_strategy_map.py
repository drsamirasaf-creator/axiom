"""§4v — the departmental strategy map: a constrained hierarchy, auto-laid-out.

⭐⭐ POSITION IS NOT DATA. On a free canvas position becomes meaning, and the
picture would carry information the model does not. Nodes belong to LAYERS —
objective → key result → KPI → initiative — and the layer is the only spatial
claim the map makes.

⭐⭐ UNCONNECTED NODES ARE THE FINDING, NOT AN OMISSION. A KPI serving no
objective and a KR nobody resourced are exactly what a CXO needs to see; a map
that quietly dropped them would report a tidier company than exists.

⛔ EDGES ARE DECLARED, NEVER INFERRED. `KeyResult.kpi_key` was designed for text
matching and is NULL ON ALL 82 ROWS — inference-by-name has produced nothing
here. Every edge carries an actor and a date, and removing one is a REVOKE.
"""
import os
import tempfile
from datetime import datetime

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="smap-", suffix=".db"))

import pytest

from services.api import strategy_map as S

OBJ = [{"obj_key": "O1", "objective": "Grow", "key_results": [
            {"kr_key": "K1", "name": "ARR +20%"},
            {"kr_key": "K2", "name": "Churn -2pt"}]},
       {"obj_key": "O2", "objective": "Harden", "key_results": []}]
KPI = [{"id": 11, "name": "ARR"}, {"id": 12, "name": "Uptime"}]
INI = [{"id": 21, "ref_code": "A1", "title": "Billing rebuild"},
       {"id": 22, "ref_code": "A2", "title": "SRE hiring"}]
# declared edges, each with an actor and a date
EDGES = [
    {"kind": "kpi_objective", "src": "kpi:11", "dst": "obj:O1",
     "declared_by": 7, "declared_at": "2026-08-01", "revoked_at": None},
    {"kind": "kr_initiative", "src": "kr:K1", "dst": "ini:21",
     "declared_by": 7, "declared_at": "2026-08-01", "revoked_at": None},
    {"kind": "kr_initiative", "src": "kr:K2", "dst": "ini:22",
     "declared_by": 7, "declared_at": "2026-08-02", "revoked_at": "2026-08-03"},
]


def _map(**kw):
    return S.build_map(objectives=OBJ, kpis=KPI, initiatives=INI,
                       edges=kw.pop("edges", EDGES), **kw)


# ── 1 · the constrained hierarchy ─────────────────────────────────────────

def test_every_node_carries_a_layer_and_the_layers_are_ordered():
    m = _map()
    assert S.LAYERS == ("objective", "key_result", "kpi", "initiative")
    for n in m["nodes"]:
        assert n["layer"] in S.LAYERS
        assert n["layer_index"] == S.LAYERS.index(n["layer"])


def test_no_node_carries_a_free_position():
    """⛔ POSITION WOULD BECOME MEANING. The map publishes a layer and an order
    WITHIN it; where that lands on screen is the renderer's business."""
    for n in _map()["nodes"]:
        assert "x" not in n and "y" not in n


def test_ordering_is_stable_and_does_not_depend_on_input_order():
    """⭐⭐ REFLOW IS THE COST OF AUTO-LAYOUT. If order moved when an unrelated
    edge was declared, every reader would lose their place on every edit."""
    a = [n["id"] for n in _map()["nodes"]]
    shuffled = list(reversed(OBJ)), list(reversed(KPI)), list(reversed(INI))
    b = [n["id"] for n in S.build_map(objectives=shuffled[0], kpis=shuffled[1],
                                      initiatives=shuffled[2],
                                      edges=EDGES)["nodes"]]
    assert a == b, "node order depends on input order — the map would reflow"


def test_order_within_a_layer_is_deterministic_across_runs():
    assert [n["id"] for n in _map()["nodes"]] == [n["id"] for n in _map()["nodes"]]


# ── 2 · declared edges, and revocation ────────────────────────────────────

def test_a_revoked_edge_is_not_drawn():
    """⭐ §4v.1 ruling 1 — removal is a revoke, and a revoked link must stop
    connecting. The row survives; the edge does not."""
    m = _map()
    pairs = {(e["src"], e["dst"]) for e in m["edges"]}
    assert ("kr:K1", "ini:21") in pairs
    assert ("kr:K2", "ini:22") not in pairs, "a revoked edge is still drawn"


def test_every_drawn_edge_carries_its_actor_and_date():
    """⛔ AN EDGE WITH NO DECLARER IS AN INFERENCE WEARING A DECLARATION'S
    CLOTHES."""
    for e in _map()["edges"]:
        assert e.get("declared_by") is not None, e
        assert e.get("declared_at"), e


def test_an_edge_to_a_node_that_is_not_on_the_map_is_dropped_and_counted():
    """⭐ A DANGLING EDGE WOULD DRAW A LINE TO NOWHERE. It is dropped, and the
    count is REPORTED rather than silently swallowed."""
    edges = EDGES + [{"kind": "kpi_objective", "src": "kpi:99", "dst": "obj:O1",
                      "declared_by": 7, "declared_at": "2026-08-01",
                      "revoked_at": None}]
    m = _map(edges=edges)
    assert all(e["src"] != "kpi:99" for e in m["edges"])
    assert m["dropped_edges"] == 1


def test_an_edge_with_no_actor_is_refused_not_drawn():
    """⛔ AN UNATTRIBUTED EDGE IS AN INFERENCE. Drawing it would put an
    unattributed claim on a map whose whole premise is attribution."""
    edges = EDGES + [{"kind": "kpi_objective", "src": "kpi:12", "dst": "obj:O2",
                      "declared_by": None, "declared_at": None,
                      "revoked_at": None}]
    m = _map(edges=edges)
    assert all(e["src"] != "kpi:12" for e in m["edges"])
    assert m["dropped_edges"] == 1
    # ⭐ AND THE REFUSAL DOES NOT SILENTLY CONNECT THE NODES — they remain the
    # finding they were.
    by = {n["id"]: n for n in m["nodes"]}
    assert by["kpi:12"]["connected"] is False


# ── 3 · unconnected nodes are the finding ─────────────────────────────────

def test_unconnected_nodes_are_flagged_not_omitted():
    """⭐⭐ 8 OF 49 KPIs AND 41 OF 82 KRs ARE DELIBERATELY UNRESOURCED. A map
    that dropped them would report a tidier company than exists."""
    m = _map()
    ids = {n["id"] for n in m["nodes"]}
    assert "kpi:12" in ids and "obj:O2" in ids
    by = {n["id"]: n for n in m["nodes"]}
    assert by["kpi:12"]["connected"] is False
    assert by["obj:O2"]["connected"] is False
    assert by["kpi:11"]["connected"] is True


def test_the_unconnected_count_is_published_per_layer():
    """⭐ THE FINDING IS COUNTABLE. A CXO asks 'how much of this is unresourced',
    and the answer must not require counting dots."""
    u = _map()["unconnected"]
    assert u["kpi"] == 1 and u["objective"] == 1
    # ⭐ K2's only edge was revoked, so it is unconnected again — revocation
    # changes the FINDING, not just the picture.
    assert u["key_result"] >= 1


# ── 4 · who may edit ──────────────────────────────────────────────────────

def test_the_authority_holder_may_edit():
    p = S.map_permission(has_authority=True, is_platform_staff=False)
    assert p["may_edit"] is True


def test_platform_staff_are_refused_even_though_they_can_see_it():
    """⛔ §4v.1 ruling 3 — platform staff refused in both. Declaring a link is a
    claim about someone else's business."""
    p = S.map_permission(has_authority=True, is_platform_staff=True)
    assert p["may_edit"] is False
    assert "platform" in p["why"].lower()


def test_a_department_with_no_holder_reads_as_read_only_not_broken():
    """⭐⭐ FIVE OF SEVEN MERIDIAN DEPARTMENTS HAVE NO HOLDER. The map must say
    'nobody holds authority here' — an admin seeing a disabled control with no
    reason would read the feature as broken."""
    p = S.map_permission(has_authority=False, is_platform_staff=False)
    assert p["may_edit"] is False
    why = p["why"].lower()
    assert "authority" in why and ("nobody" in why or "no one" in why)
    assert "error" not in why and "unavailable" not in why


# ── 5 · no node is a dead end ─────────────────────────────────────────────

def test_every_node_carries_a_destination():
    """⭐ §4v — the destinations shipped at cc49b2a; the map must use them."""
    for n in _map()["nodes"]:
        assert n.get("to"), f"{n['id']} opens nowhere"
        assert n["to"].startswith("/")
