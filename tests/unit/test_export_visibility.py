"""ONE visibility rule — the export carries what the user can already see. Ruled 31 Jul.

⭐ TWO VISIBILITY RULES IS THE "TWO SURFACES, ONE CONCEPT" BUG CLASS IN ITS MOST
CONSEQUENTIAL FORM, because the second surface is the one that LEAVES THE
BUILDING. An export that can show more than the app is a second access-control
system nobody audits, and it would drift from the first silently.

⭐ THE CONSEQUENCE ASSERTED HERE: the export derives visibility from THE SAME
RESOLVER THE APP USES, never from a parallel list of what to include. A
hand-maintained inclusion list is exactly how the two rules diverge — and it is
the defect ALREADY FOUND in the export's section coverage, where `board_report`'s
section list was a literal that went stale silently. The same mistake in a
permission list would LEAK rather than omit.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest

from services.api import pack_render as R
from tests.codeonly import code_only


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ NO PARALLEL PERMISSION LIST
# ═══════════════════════════════════════════════════════════════════════════

def test_the_renderer_declares_no_permission_list_of_its_own():
    """⭐ THE GUARDIAN. A second list of who-may-see-what, anywhere in the render
    path, is the divergence this ruling forbids."""
    src = code_only(R)
    for banned in ("ALLOWED_ROLES", "VISIBLE_TO", "PERMISSION", "ROLE_WHITELIST",
                   "CAN_SEE", "EXPORT_ROLES"):
        assert banned not in src.upper(), (
            f"pack_render declares {banned} — a second visibility rule. The "
            f"export must inherit the requesting user's role visibility, never "
            f"define its own (ruled 31 Jul).")


def test_the_renderer_does_not_gate_on_a_role_at_all():
    """⭐ IT CANNOT WIDEN WHAT IT NEVER NARROWS. The components take a Source,
    not a user — so there is no place for a second rule to be written."""
    import inspect
    for fn in (R.render_export, R.render_pack):
        sig = inspect.signature(fn)
        assert list(sig.parameters) == ["src"], (
            f"{fn.__name__} takes {list(sig.parameters)} — a renderer that "
            f"receives a user can make its own visibility decision")
    src = code_only(R)
    assert "platform_role" not in src
    assert "require_company_admin" not in src


def test_the_component_registry_is_a_CONTENT_list_not_a_permission_list():
    """⭐ COMPONENTS decides WHAT SECTIONS EXIST, never WHO MAY SEE THEM. The two
    must not merge: a content list that acquires a role field becomes the
    parallel permission system by increment."""
    for name, fn in R.COMPONENTS.items():
        assert callable(fn)
        src = code_only(fn)
        assert "role" not in src.lower() or "role_label" in src.lower(), (
            f"component {name} inspects a role — visibility belongs to the "
            f"caller's resolver, not to a section")


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE FLOOR IS THE PROTECTION, AND IT ACTS AT SOURCE
# ═══════════════════════════════════════════════════════════════════════════

def test_the_k_floor_suppresses_before_any_surface_sees_the_data():
    """⭐ K-ANONYMITY PROTECTS RESPONDENTS FROM THE COMPANY, NOT THE COMPANY FROM
    ITSELF. The floor acts at SOURCE — so an export inheriting full user
    visibility still cannot reach a suppressed slice, because it was never in the
    payload to begin with.

    This is what makes "one visibility rule" safe: the thing that must not leak
    is removed upstream of every surface, rather than by each surface remembering.
    """
    import inspect

    from services.api import assessment_engine as AE
    src = inspect.getsource(AE.apply_kfloor)
    assert src, "apply_kfloor must exist"
    # it is applied at SERIALIZATION, not per-surface
    core = inspect.getsource(AE.compute_cei)
    assert "suppression is applied at" in core or "apply_kfloor" not in core, (
        "compute_cei applies the floor itself — the raw/suppressed split is what "
        "keeps one rule at one place")


def test_a_below_floor_slice_is_absent_from_the_payload_not_merely_hidden():
    """⭐ SUPPRESSED MEANS THE VALUE IS GONE, not styled away. A surface that
    inherited full visibility would otherwise still receive it.

    ⭐ ON THE REAL SEEDED DATA THE RULING CITES (`e67262b`), not a synthetic
    aggregate. The first version hand-built a three-department dict and
    `apply_kfloor` returned an empty map — the fixture lacked the structure the
    real path produces, so it proved nothing about the real path.
    """
    from fastapi.testclient import TestClient

    from services.api.assessment_engine import KFLOOR, apply_kfloor
    from services.api.core import seed_meridian as SM
    from services.api.core.db import SessionLocal
    from services.api.main import app
    from services.api.modules.enterprise_state.models import Enterprise

    with TestClient(app):
        db = SessionLocal()
        ent = Enterprise(tenant="t-exp-vis", name="Export visibility",
                         sector="industrials", reporting_currency="USD",
                         statement_units="thousands", ownership="private")
        db.add(ent); db.commit(); db.refresh(ent)
        SM.reseed(db, ent.id)
        asmt = SM.seed_assessment(db, ent.id)
        db.commit()
        out = apply_kfloor(SM.cei_for_cycle(db, ent.id, asmt["cycles"][1]))

    depts = out["departments"]
    hidden = {d: v for d, v in depts.items() if v.get("suppressed")}
    assert hidden, "the floor suppressed nothing on data built to trip it"
    for d, v in hidden.items():
        assert v.get("cei") is None or "cei" not in v, (
            f"{d} is suppressed but still carries its value — an export "
            f"inheriting the user's visibility would then carry it too")
        assert v.get("n") is not None, "the count is published; the VALUE is not"
    # ⭐ the complement guard leaves at least two unknowns
    assert len(hidden) >= 2, "one hidden slice is derivable by subtraction"
    assert any(v.get("n", 0) < KFLOOR for v in hidden.values())


def test_the_ruling_does_not_claim_to_stop_a_CEO_forwarding_an_export():
    """⭐ RECORDED SO IT IS NOT MISTAKEN FOR SOLVED. A CEO who can see a slice
    in-app can export it and send it anywhere. That is deliberate — the
    alternative is an export that LIES TO ITS OWN USER about what the product
    told them.

    Asserted as an absence: nothing in the render path attempts recipient-side
    restriction, because that would be the second rule wearing a different name.
    """
    src = code_only(R)
    for pretence in ("watermark", "redact_for_recipient", "forward_protection",
                     "drm", "expire_on_forward"):
        assert pretence not in src.lower(), (
            f"the renderer implements {pretence} — a control the ruling "
            f"explicitly does not claim")


# ═══════════════════════════════════════════════════════════════════════════
# the section-coverage precedent this ruling cites
# ═══════════════════════════════════════════════════════════════════════════

def test_the_section_coverage_guard_still_derives_both_sides():
    """⭐ THE PRECEDENT. The export's SECTION list was a hand-maintained literal
    that went stale silently; the guard now derives both sides from code. A
    permission list would fail the same way and leak rather than omit."""
    src = open("scripts/check-export-coverage.py", encoding="utf-8").read()
    assert "app_surfaces" in src and "export_carries" in src
    assert "_component_names" in src, \
        "the carried set is no longer derived from the component registry"
