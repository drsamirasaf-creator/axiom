"""§7j.2 ruling 3 — the Resilience Field: the region, rendered from stored work."""
import ast
import os

import pytest

import services.api.resilience_field as RF

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = open(os.path.join(ROOT, "services/api/resilience_field.py"),
           encoding="utf-8").read()
FE = "/Users/samirasaf/dev/optimization-anchor"

RAYS = {"revenue": {"revenue": 1.0}, "margin": {"margin": 1.0},
        "rate": {"rate": 1.0}, "working_capital": {"wc": 1.0},
        "recession": {"revenue": 1.0, "margin": 1.0}}
REF = {"revenue": 0.5, "margin": 0.1, "rate": 0.05, "wc": 0.5}


def _payload(distances, **kw):
    p = {"distances": distances, "shock_reference": REF, "band": "STABLE",
         "overall_distance": min(distances.values()) if distances else None,
         "thresholds": {"stable_min": 0.2, "fragile_min": 0.08}}
    p.update(kw)
    return p


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 1 · THE FIELD IS THE REGION, NOT A NUMBER
# ═══════════════════════════════════════════════════════════════════════════

def test_each_axis_carries_a_BOUNDARY_IN_NATURAL_UNITS():
    """⭐⭐ 'revenue can fall 47% before the band breaks' is checkable;
    'resilience 0.63' is not."""
    f = RF.field(_payload({"revenue": 0.9453}), rays=RAYS)
    d = next(x for x in f["dimensions"] if x["ray"] == "revenue")
    assert d["state"] == "measured"
    b = d["boundary"]["revenue"]
    assert b["label"] == "revenue decline"
    assert b["magnitude"] == round(0.9453 * 0.5, 4) == 0.4727
    assert b["unit"] == "fraction"


def test_the_reader_can_see_WHERE_THEY_SIT_inside_the_region():
    """⭐ A region with no position in it is a diagram, not a statement about
    this company."""
    f = RF.field(_payload({"revenue": 0.9453, "recession": 0.6367},
                          nearest_breach={"ray": "recession", "distance": 0.6367,
                                          "plain": "a 32% revenue decline"}),
                 rays=RAYS)
    assert f["position"]["ray"] == "recession"
    assert "32%" in f["position"]["plain"]


def test_axes_and_COMBINATIONS_are_distinguished():
    """⭐ Conflating them would suggest seven independent dimensions of room."""
    f = RF.field(_payload({"revenue": 0.5, "recession": 0.4}), rays=RAYS)
    kinds = {d["ray"]: d["kind"] for d in f["dimensions"]}
    assert kinds["revenue"] == "axis"
    assert kinds["recession"] == "combination"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 2 · CENSORING — the finding this module exists to get right
# ═══════════════════════════════════════════════════════════════════════════

def test_A_RAY_THAT_NEVER_FAILED_IS_CENSORED_not_a_boundary():
    """⭐⭐ `_nearest_t` returns T_MAX when a ray does NOT fail. Rendering 1.0 as
    a boundary would tell a CEO their margin can compress exactly 10pp when the
    truth is IT WAS NEVER MADE TO FAIL. Four of Meridian's seven are censored,
    so this is the common case."""
    f = RF.field(_payload({"revenue": 0.5, "margin": 1.0}), rays=RAYS)
    m = next(x for x in f["dimensions"] if x["ray"] == "margin")
    assert m["state"] == "censored"
    assert "boundary" not in m, "a censored ray must not present a boundary"
    assert m["at_least"]["margin"]["magnitude"] == 0.1
    assert "beyond this, not at it" in m["absent"]


def test_a_censored_ray_is_NOT_counted_as_measured():
    f = RF.field(_payload({"revenue": 0.5, "margin": 1.0, "rate": 1.0}), rays=RAYS)
    assert f["coverage"] == {"total": 3, "measured": 1, "censored": 2, "absent": 0}


def test_COVERAGE_IS_ON_THE_SURFACE_ITSELF():
    """⭐ '1 of 3 measured' is the difference between a field and a field with
    holes in it, and a reader cannot infer it from the dots (III.4)."""
    f = RF.field(_payload({"revenue": 0.5, "margin": 1.0, "rate": 1.0}), rays=RAYS)
    c = f["coverage"]
    assert c["total"] == c["measured"] + c["censored"] + c["absent"]


def test_an_already_breached_ray_says_so():
    f = RF.field(_payload({"revenue": 0.0}), rays=RAYS)
    d = f["dimensions"][0]
    assert d["state"] == "breached"
    assert "already in breach" in d["absent"]


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 3 · ABSENCE DECLARES, PER PARAMETER
# ═══════════════════════════════════════════════════════════════════════════

def test_a_ray_with_no_recorded_composition_is_ABSENT_not_zero():
    """⭐⭐ A field with a silently missing dimension misstates how much room the
    company has — the expensive direction."""
    f = RF.field(_payload({"revenue": 0.5, "mystery_ray": 0.3}), rays=RAYS)
    d = next(x for x in f["dimensions"] if x["ray"] == "mystery_ray")
    assert d["state"] == "absent"
    assert d["absent"]
    assert "boundary" not in d and "at_least" not in d


def test_a_missing_SHOCK_REFERENCE_is_stated_rather_than_guessed():
    """⭐ A magnitude computed against the wrong reference is a wrong number that
    looks right."""
    p = _payload({"revenue": 0.5})
    p["shock_reference"] = {}          # the reference did not survive the freeze
    f = RF.field(p, rays=RAYS)
    d = f["dimensions"][0]
    assert d["boundary"]["revenue"].get("absent")
    assert "no shock reference" in d["boundary"]["revenue"]["absent"]


def test_NO_VIABILITY_RESULT_declares_rather_than_returning_an_empty_field():
    """⭐ An empty field reads as 'there is no room'."""
    f = RF.field(None)
    assert f["has_data"] is False
    assert "no viability result" in f["absent"]
    assert f["dimensions"] == []


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 4 · REVERSE-STRESS — measured absent, NOT built
# ═══════════════════════════════════════════════════════════════════════════

def test_REVERSE_STRESS_IS_REPORTED_ABSENT_and_not_built():
    """⭐⭐ CORE's clause names 'stress/reverse-stress'. Nothing computes it: the
    kernel bisects FORWARD to the nearest failure surface. `_prescribe` searches
    for the minimum intervention that RESTORES stability — adjacent, but it asks
    what fixes a breach, not what magnitude would cause one."""
    f = RF.field(_payload({"revenue": 0.5}), rays=RAYS)
    assert f["reverse_stress"]["present"] is False
    assert "does not solve for the shock" in f["reverse_stress"]["absent"]


def test_nothing_in_the_codebase_computes_reverse_stress():
    """⭐ Verified against the code, not inherited from the scope report."""
    import subprocess
    out = subprocess.run(
        ["grep", "-rn", "--include=*.py", "-iE", "reverse.?stress",
         os.path.join(ROOT, "services")], capture_output=True, text=True).stdout
    # ⭐ only this module's own STATEMENT that it is absent may match
    live = [ln for ln in out.splitlines()
            if "resilience_field.py" not in ln]
    assert not live, f"something computes reverse-stress after all:\n{out}"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 5 · NO NEW ENGINE, NO RECOMPUTATION
# ═══════════════════════════════════════════════════════════════════════════

def test_THE_MODULE_NEVER_RECOMPUTES():
    """⭐⭐ A surface that recomputes on read drifts from the pack that froze it —
    and the whole point of the Field is that a reader can hold it against a
    number someone else quoted."""
    tree = ast.parse(SRC)
    called = {n.func.attr for n in ast.walk(tree)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    for banned in ("run", "simulate", "compute_viability", "_nearest_t",
                   "_detect", "evaluate_trajectory"):
        assert banned not in called, f"the field recomputes via {banned}()"
    # ⭐⭐ AST, NOT SUBSTRING. My first version banned ".data" and fired on
    # `Viability.dataset_version` — §III.9, SEVENTH instance. The concern is an
    # attribute access named exactly `data`, which is how a dataset payload is
    # opened; `dataset_version` is a column name and reads nothing.
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert "data" not in attrs, "the field opens a dataset payload"
    assert "FinancialDataset" not in SRC


def test_the_pack_component_reads_FROZEN_state():
    """⭐ Constraint: renders from FrozenSource where it appears in a pack, so a
    published pack shows the field as it stood at publication."""
    pr = open(os.path.join(ROOT, "services/api/pack_render.py"),
              encoding="utf-8").read()
    fn = pr[pr.index("def c_resilience_field"):pr.index("COMPONENTS = {")]
    assert "src.klass(" in fn, "the component does not read from the Source"
    assert "SessionLocal" not in fn and "db." not in fn, \
        "the pack component reaches live state"
    assert '"resilience_field": c_resilience_field' in pr, "not registered"


def test_the_field_is_pure_over_its_input():
    """⭐ Same payload in, same field out — no clock, no db, no randomness."""
    p = _payload({"revenue": 0.5, "margin": 1.0})
    assert RF.field(p, rays=RAYS) == RF.field(p, rays=RAYS)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 6 · WIRING
# ═══════════════════════════════════════════════════════════════════════════

def test_THE_ROUTE_IS_SERVED():
    """⭐ Ten built-but-not-wired instances. A module imported but never included
    registers nothing."""
    from fastapi.testclient import TestClient

    from services.api.main import app
    with TestClient(app) as c:
        paths = c.get("/openapi.json").json()["paths"]
    assert "/companies/{company_id}/resilience-field" in paths


def test_the_route_is_a_GET_only():
    from fastapi.testclient import TestClient

    from services.api.main import app
    with TestClient(app) as c:
        paths = c.get("/openapi.json").json()["paths"]
    ms = sorted(m.upper() for m in paths["/companies/{company_id}/resilience-field"])
    assert ms == ["GET"], f"the field accepts a write: {ms}"


def test_the_FRONTEND_renders_the_field():
    """⭐⭐ THE WIRING CHAIN, EACH LINK NAMED. My first version looked for the
    fetch in the PAGE and failed — the fetch lives in the component. Asserting
    one file cannot prove a chain, and the matrix lane's defect was exactly an
    assertion that named no route at all.
    """
    page_p = os.path.join(FE, "src/routes/prescience-ai.tsx")
    comp_p = os.path.join(FE, "src/components/ResilienceField.tsx")
    if not os.path.exists(page_p) or not os.path.exists(comp_p):
        pytest.skip("frontend checkout not present")
    page = open(page_p, encoding="utf-8").read()
    comp = open(comp_p, encoding="utf-8").read()

    # link 1: the page mounts the component on the Resilience tab
    assert "ResilienceField" in page, "the page does not import the component"
    assert 'tab === "resilience"' in page, "the component is not on the Resilience tab"
    assert "<ResilienceField" in page, "the component is imported but never rendered"

    # link 2: the component calls the route the backend serves
    assert "/resilience-field" in comp, "the component does not call the route"

    # link 3: the distinctions this lane exists for survive into the render
    assert "censored" in comp, "the page does not distinguish a censored ray"
    assert "survives at least" in comp, "a censored ray is rendered as a boundary"
    assert "coverage" in comp, "coverage is not shown"
    assert "reverse_stress" in comp, "the reverse-stress absence is not stated"


def test_the_resilience_tab_is_NOT_behind_the_locked_placeholder():
    """⭐ A tab that is BUILT must not sit behind an upgrade card saying it is
    not — that is the inverse of the admissibility rule, and it is the shape
    that made four placeholders read as shipped."""
    p = os.path.join(FE, "src/routes/prescience-ai.tsx")
    if not os.path.exists(p):
        pytest.skip("frontend checkout not present")
    page = open(p, encoding="utf-8").read()
    branch = page[page.index('tab === "resilience"'):]
    lock_at = page.index("lockedBlurb[tab]")
    assert page.index('tab === "resilience"') < lock_at, \
        "the resilience branch does not precede the locked card"
    assert "ResilienceField" in branch[:400]
