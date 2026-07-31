"""B10/B11 — the declared initiative → statement-line link and the attribution rule.

⭐ THREE RECORDED GAPS TRACE TO ONE MEASURED FACT. This closes the mechanism for
all three; whether the brochure claim is restored is a separate ruling and this
lane does not touch it.

⭐⭐ THE LOAD-BEARING TEST IS `test_a_sole_link_does_not_take_the_whole_movement`.
Exclusivity of linkage is not exclusivity of cause, and a partially-linked model
over-credits whichever initiative was wired up first — invisibly, because it
cannot see the drivers nobody declared.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest
from fastapi.testclient import TestClient

from services.api import initiative_lines as IL
from services.api.main import app
from tests.codeonly import code_only
from tests.fixtures.refcases import meridian


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _db():
    from services.api.core.db import SessionLocal
    return SessionLocal()


@pytest.fixture
def company(client):
    from services.api.accounts import Initiative, apply_upload
    from services.api.modules.enterprise_state.models import Enterprise
    with _db() as db:
        n = db.query(Enterprise).count()
        ent = Enterprise(tenant=f"t-il{n}", name=f"IL {n}", sector="industrials",
                         reporting_currency="USD", statement_units="thousands",
                         ownership="private")
        db.add(ent); db.commit(); db.refresh(ent)
        apply_upload(db, ent.id, ent=ent, data=meridian(), objectives=[],
                     key_results=[], kpis=[], departments=[], warnings=[],
                     frequency="annual", meta={}, okr_flags={}, user=None)
        inits = []
        for i in range(4):
            row = Initiative(company_id=ent.id, ref_code=f"INI-{n}-{i}",
                             title=f"Initiative {i}", importance=3, urgency=3,
                             current_priority=3, created_by=1, status="on_track")
            db.add(row); db.flush()
            inits.append(row.id)
        db.commit()
        return ent.id, inits


# ═══════════════════════════════════════════════════════════════════════════
# 2 · DECLARED, NEVER INFERRED
# ═══════════════════════════════════════════════════════════════════════════

def test_the_link_is_declared_and_carries_its_declarer(company):
    cid, inits = company
    with _db() as db:
        r = IL.declare(db, cid, inits[0], "revenue", weight=0.4,
                       user=type("U", (), {"id": 7, "name": "A Person"})(),
                       note="board-approved plan")
        db.commit()
        assert r.declared_by == 7
        assert r.declared_by_label == "A Person"
        assert r.declared_at is not None
        assert r.note == "board-approved plan"


def test_nothing_infers_a_link(company):
    """⭐ Inferring it from a correlation would fabricate exactly the number the
    brochure proof point was withdrawn for asserting."""
    src = code_only(IL)
    for banned in ("corr", "regress", "fit(", "estimate_link", "infer"):
        assert banned not in src.lower(), f"the module {banned}s a link"


def test_a_line_that_does_not_exist_is_refused(company):
    """⭐ A link naming a non-existent line would contribute nothing while
    looking declared."""
    from fastapi import HTTPException
    cid, inits = company
    with _db() as db:
        with pytest.raises(HTTPException) as ei:
            IL.declare(db, cid, inits[0], "not_a_real_line", weight=0.5)
    assert ei.value.status_code == 422


def test_the_line_set_is_DERIVED_from_the_engines_keys():
    src = code_only(IL.statement_lines)
    assert "IS_KEYS" in src and "BS_KEYS" in src and "CF_KEYS" in src
    lines = IL.statement_lines()
    assert "revenue" in lines and "ebitda" in lines and "net_debt" in lines


def test_a_weight_outside_zero_to_one_is_refused(company):
    from fastapi import HTTPException
    cid, inits = company
    with _db() as db:
        for bad in (0.0, -0.1, 1.5):
            with pytest.raises(HTTPException):
                IL.declare(db, cid, inits[0], "revenue", weight=bad)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 3 · THE ATTRIBUTION RULE — AND THE OVER-CREDITING TRAP
# ═══════════════════════════════════════════════════════════════════════════

def test_a_sole_link_does_not_take_the_whole_movement(company):
    """⭐⭐ THE LOAD-BEARING ASSERTION. A line with ONE linked initiative and
    THREE real drivers must not attribute its whole movement to the one link.

    The declarer said this initiative accounts for 30% of revenue. Revenue moved
    1000. It gets 300 — NOT 1000 — and the remaining 700 is residual, because the
    model cannot see the drivers nobody declared.
    """
    cid, inits = company
    with _db() as db:
        IL.declare(db, cid, inits[0], "revenue", weight=0.3)
        db.commit()
        out = IL.attribute(db, cid, {"revenue": 1000.0})

    assert len(out["attributed"]) == 1
    a = out["attributed"][0]
    assert a["mode"] == IL.SOLE
    assert a["amount"] == pytest.approx(300.0), \
        "a sole link took more than its declared share — this is the " \
        "over-crediting the rule exists to prevent"
    assert out["residual"]["revenue"]["amount"] == pytest.approx(700.0)
    assert "not covered by a declared share" in out["residual"]["revenue"]["reason"]


def test_several_initiatives_split_by_declared_weight(company):
    cid, inits = company
    with _db() as db:
        IL.declare(db, cid, inits[0], "ebitda", weight=0.5)
        IL.declare(db, cid, inits[1], "ebitda", weight=0.2)
        db.commit()
        out = IL.attribute(db, cid, {"ebitda": 200.0})
    amounts = {a["initiative_id"]: a["amount"] for a in out["attributed"]}
    assert amounts[inits[0]] == pytest.approx(100.0)
    assert amounts[inits[1]] == pytest.approx(40.0)
    assert all(a["mode"] == IL.PROPORTIONAL for a in out["attributed"])
    assert out["residual"]["ebitda"]["amount"] == pytest.approx(60.0)


def test_an_unstated_share_attributes_NOTHING(company):
    """⭐ NULL weight means the share is UNKNOWN — not 1.0, not 0. Treating an
    unstated share as full ownership is the fabrication this prevents."""
    cid, inits = company
    with _db() as db:
        IL.declare(db, cid, inits[0], "revenue")          # no weight
        db.commit()
        out = IL.attribute(db, cid, {"revenue": 500.0})
    a = out["attributed"][0]
    assert a["amount"] is None
    assert a["declared_weight"] is None
    assert "not full ownership" in a["absent"]
    assert out["residual"]["revenue"]["amount"] == pytest.approx(500.0)


def test_weights_summing_above_one_attribute_NOTHING(company):
    """⭐ A DECLARATION ERROR IS NOT NORMALISED. Rescaling would silently invent a
    split nobody stated."""
    cid, inits = company
    with _db() as db:
        IL.declare(db, cid, inits[0], "cogs", weight=0.7)
        IL.declare(db, cid, inits[1], "cogs", weight=0.6)
        db.commit()
        out = IL.attribute(db, cid, {"cogs": 100.0})
    assert out["attributed"] == []
    assert "inconsistent" in out["residual"]["cogs"]["reason"]
    assert out["residual"]["cogs"]["amount"] == pytest.approx(100.0)


def test_a_full_declared_share_leaves_no_residual_ONLY_because_it_was_declared(company):
    cid, inits = company
    with _db() as db:
        IL.declare(db, cid, inits[0], "opex", weight=1.0)
        db.commit()
        out = IL.attribute(db, cid, {"opex": 80.0})
    assert out["attributed"][0]["amount"] == pytest.approx(80.0)
    assert "opex" not in out["residual"] or \
        out["residual"]["opex"]["amount"] == pytest.approx(0.0)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 4 · ABSENCE STAYS ABSENT
# ═══════════════════════════════════════════════════════════════════════════

def test_a_line_no_initiative_declares_is_residual_not_attributed(company):
    cid, inits = company
    with _db() as db:
        IL.declare(db, cid, inits[0], "revenue", weight=0.5)
        db.commit()
        out = IL.attribute(db, cid, {"revenue": 100.0, "cogs": 50.0})
    assert out["residual"]["cogs"]["reason"] == "no initiative declares this line"
    assert out["residual"]["cogs"]["amount"] == pytest.approx(50.0)
    assert not any(a["statement_line"] == "cogs" for a in out["attributed"])


def test_unlinked_initiatives_are_NAMED_not_silently_omitted(company):
    """⭐ Saying so is what stops a reader assuming the linked ones are all of
    them."""
    cid, inits = company
    with _db() as db:
        IL.declare(db, cid, inits[0], "revenue", weight=0.5)
        db.commit()
        out = IL.attribute(db, cid, {"revenue": 100.0})
    un = {u["initiative_id"] for u in out["unlinked_initiatives"]}
    assert un == set(inits[1:]), "unlinked initiatives were not reported"
    for u in out["unlinked_initiatives"]:
        assert u["reason"] and u["ref_code"]


def test_an_incomputable_movement_is_absent_not_zero(company):
    cid, inits = company
    with _db() as db:
        IL.declare(db, cid, inits[0], "revenue", weight=0.5)
        db.commit()
        out = IL.attribute(db, cid, {"revenue": None})
    assert out["residual"]["revenue"]["amount"] is None
    assert "not computable" in out["residual"]["revenue"]["reason"]
    assert out["attributed"] == []


# ═══════════════════════════════════════════════════════════════════════════
# THE BRIDGE
# ═══════════════════════════════════════════════════════════════════════════

def _publish_two(cid, tweak):
    from services.api import pack as P
    from services.api.accounts import apply_upload
    from services.api.modules.enterprise_state.models import Enterprise
    with _db() as db:
        first = P.publish(db, cid, "monthly", "2026-05-31"); db.commit()
        ent = db.get(Enterprise, cid)
        d = meridian()
        ys = str(max(d["periods"]["historical"]))
        d["income_statement"]["revenue"][ys] += tweak
        apply_upload(db, ent.id, ent=ent, data=d, objectives=[], key_results=[],
                     kpis=[], departments=[], warnings=[], frequency="annual",
                     meta={}, okr_flags={}, user=None)
        db.commit()
        second = P.publish(db, cid, "monthly", "2026-06-30"); db.commit()
        return first.id, second.id


def test_the_bridge_driver_is_ABSENT_with_no_declared_link(company):
    """⭐ Before B10 it was absent for everyone. It stays absent for anyone who
    has declared nothing."""
    from services.api import pack as P
    cid, inits = company
    a, b = _publish_two(cid, 100.0)
    with _db() as db:
        br = P.frozen_inputs(db, db.get(P.Pack, b))["classes"]["value_bridge"]["bridge"]
    d = [x for x in br["drivers"] if x["key"] == "initiatives"][0]
    assert d["amount"] is None
    assert "no initiative declares a statement line" in d["absent"]


def test_the_bridge_driver_ATTRIBUTES_when_a_link_is_declared(company):
    """⭐⭐ THE GAP CLOSING. The initiatives driver produces a number for the
    first time — at the declared share, and no more."""
    from services.api import pack as P
    cid, inits = company
    with _db() as db:
        IL.declare(db, cid, inits[0], "revenue", weight=0.25)
        db.commit()
    a, b = _publish_two(cid, 400.0)
    with _db() as db:
        br = P.frozen_inputs(db, db.get(P.Pack, b))["classes"]["value_bridge"]["bridge"]
    d = [x for x in br["drivers"] if x["key"] == "initiatives"][0]
    assert d["amount"] is not None, "the initiatives driver is still absent"
    assert d["traceable"] is True
    assert d["amount"] == pytest.approx(100.0), \
        "revenue moved 400 and the declared share is 25% — 100, not 400"
    assert d["detail"]["attribution"]["residual"]["revenue"]["amount"] \
        == pytest.approx(300.0)
    assert d["detail"]["unlinked"], "the unlinked initiatives are not carried"


def test_the_frozen_links_do_not_move_after_publication(company):
    """⭐ A link declared AFTER publication must not retro-attribute a movement
    in a pack already issued."""
    from services.api import pack as P
    from services.api import pack_render as R
    cid, inits = company
    with _db() as db:
        IL.declare(db, cid, inits[0], "revenue", weight=0.25); db.commit()
    a, b = _publish_two(cid, 400.0)

    def _render():
        with _db() as db:
            return R.render_hash(R.render_pack(R.FrozenSource(
                P.frozen_inputs(db, db.get(P.Pack, b)))))

    before = _render()
    with _db() as db:
        IL.declare(db, cid, inits[1], "revenue", weight=0.5); db.commit()
        live = R.render_hash(R.render_pack(R.LiveSource(db, cid)))
    assert _render() == before, "a later declaration moved a published pack"


def test_the_attribution_reader_takes_no_session():
    """⭐ A bridge that re-read the live links would retro-attribute."""
    import inspect

    from services.api import value_bridge as VB
    sig = inspect.signature(VB._attribute_frozen)
    assert "db" not in sig.parameters
    src = code_only(VB._attribute_frozen)
    assert "db.query" not in src and "links_for" not in src


# ═══════════════════════════════════════════════════════════════════════════
# constraints
# ═══════════════════════════════════════════════════════════════════════════

def test_nothing_is_backfilled():
    """⭐ Every existing initiative starts unlinked. Inferring links for rows
    already present would fabricate the withdrawn claim."""
    import ast
    src = open("migrations/versions/0023_initiative_line_links.py",
               encoding="utf-8").read()
    up = next(n for n in ast.parse(src).body
              if isinstance(n, ast.FunctionDef) and n.name == "upgrade")
    calls = {n.func.attr for n in ast.walk(up)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "execute" not in calls and "bulk_insert" not in calls


def test_the_brochure_claim_is_untouched():
    """⭐ This lane builds the MECHANISM. Whether the claim is restored is a
    separate ruling, and the ledger must still say withdrawn."""
    core = open("docs/ledger/AXIOM_LEDGER_CORE.md", encoding="utf-8").read()
    assert "THE PROOF POINT — WITHDRAWN AS WRITTEN AND REPLACED" in core
