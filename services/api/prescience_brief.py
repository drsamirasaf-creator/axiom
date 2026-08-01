"""§7j.2 ruling 6 — the Prescience Brief: the Brief's forward twin.

⭐⭐ RULED 1 Aug: *what is likely · what is at risk · what to decide* — with
**distributions rather than point estimates**, following the Brief's discipline:
**traceable-or-silent line by line**, and an absent input rendering as a **stated
absence** rather than being omitted.

⭐⭐ IT INHERITS §7s.2's MACHINERY AND DOES NOT REIMPLEMENT IT. `EM_DASH`, the
fixed line count, the deep link on every line INCLUDING absent ones, and the TWO
DISTINCT ABSENCES all come from `brief.py`. ⭐ A brief that silently loses a line
lets the reader infer completeness from length — the same fabrication by silence,
in the artefact most likely to be read alone.

⭐⭐ THE TWO ABSENCES ARE OPPOSITE MEANINGS TO A READER (§7s Stage 3):
  · **input missing** — we could not look
  · **rendered, but no single figure reduces to a one-line claim** — we looked
    and would not summarise it
Collapsing them would tell a reader "nothing here" when the truth is "too much
here to say in one line".

⭐⭐ AND THE UNCERTAINTY IS ATTRIBUTABLE. σ_RO is a declared prior at 7u-pd.2
with a stated basis, and **the basis travels to the render** — as the Multiverse
tab does. ⭐ A DISTRIBUTION WHOSE UNCERTAINTY HAS NO STATED ORIGIN IS A CAVEAT,
NOT A PRODUCT.

⭐ NO NEW COMPUTATION. Every figure is read from work already done — the
Multiverse view, the Resilience Field, the decision frontier. If a quantity is
not computed it is **absent and stated**.

⭐⭐ NOT A PACK INPUT. This adds NO input class and `pack.py` is untouched: the
Brief is a Prescience surface over Prescience surfaces, and the pack keeps its
own inputs per §7j.7.
"""
from .brief import EM_DASH

# ⭐ THREE QUESTIONS, FIXED ORDER — the forward mirror of the Brief's seven.
QUESTIONS = [
    ("likely", "What is likely"),
    ("at_risk", "What is at risk"),
    ("to_decide", "What to decide"),
]

# ⭐ Where each line may be walked back to. Traceable-or-silent means a figure
# that cannot name its surface is not published.
SOURCE_SURFACE = {
    "likely": "multiverse",
    "at_risk": "resilience-field",
    "to_decide": "multiverse",
}


def _line_likely(mv):
    """Distribution, never a point. ⭐ The spread IS the claim."""
    if not mv or not mv.get("has_data"):
        return None, "no trajectory has been evaluated, so there is no distribution"
    sp = mv.get("spread") or {}
    if sp.get("absent"):
        # ⭐ the section rendered; the figure would not reduce
        return None, sp["absent"]
    mean, tail, down = sp.get("mean"), sp.get("tail_cvar95"), sp.get("downside")
    if mean is None or tail is None:
        return None, ("the mean and the tail are needed to state a range and one "
                      "of them was not computed")
    return (f"Mean enterprise value {mean:,.0f}, tail {tail:,.0f} — "
            f"a downside of {down:,.0f} in the worst 5% of futures."), None


def _line_at_risk(rf):
    """⭐⭐ CENSORING, per the Resilience Field finding. A bound meaning 'not
    tested within range' must never render as 'this is the bound'."""
    if not rf or not rf.get("has_data"):
        return None, (rf or {}).get("absent") or "no viability result has been computed"
    pos = rf.get("position") or {}
    plain = pos.get("plain")
    if not plain:
        return None, ("the field rendered but no single boundary reduces to a "
                      "one-line claim")
    cov = rf.get("coverage") or {}
    band = rf.get("band")
    suffix = ""
    if cov.get("censored"):
        # ⭐ the censored dimensions are NAMED in the line, not silently dropped
        suffix = (f" {cov['censored']} of {cov.get('total')} dimensions did not "
                  f"break within the tested range.")
    return f"{band}. Nearest breach: {plain}.{suffix}", None


def _line_to_decide(mv):
    """The frontier's own search result — never a recommendation this module
    invents."""
    if not mv or not mv.get("has_data"):
        return None, "no decision frontier has been built, so there is nothing to rank"
    s = mv.get("search") or {}
    if s.get("absent"):
        return None, s["absent"]
    n = s.get("trajectories_evaluated")
    pct = s.get("current_strategy_percentile")
    if n is None:
        return None, ("the frontier rendered but the search statistics are not "
                      "recorded, so no claim about the ranking is traceable")
    if pct is None:
        return (f"{n:,} trajectories evaluated; the current strategy's percentile "
                f"is not recorded."), None
    return (f"{n:,} trajectories evaluated. The current strategy sits at the "
            f"{pct}th percentile."), None


LINE_FN = {"likely": _line_likely, "at_risk": _line_at_risk,
           "to_decide": _line_to_decide}


def _deep_link(company_id, surface):
    """⭐ EVERY LINE LINKS, INCLUDING AN ABSENT ONE. A reader told a figure is
    missing must still be able to go and see why."""
    if company_id is None:
        return None
    return f"/prescience-ai?tab={surface}&company={company_id}"


def build(*, multiverse=None, resilience=None, company_id=None, sigma=None):
    """-> the Prescience Brief. Pure over its inputs; reads nothing.

    ⭐ THREE LINES ALWAYS. Same rule as the Brief's seven.
    """
    lines = []
    for n, (key, question) in enumerate(QUESTIONS, start=1):
        src = multiverse if key != "at_risk" else resilience
        text, reason = LINE_FN[key](src)
        line = {
            "n": n,
            "key": key,
            "question": question,
            "text": text if text is not None else EM_DASH,
            # ⭐ traceable-or-silent, stated as a field rather than inferred
            "traceable": text is not None,
            "source_surface": SOURCE_SURFACE[key],
            "deep_link": _deep_link(company_id, SOURCE_SURFACE[key]),
        }
        if text is None:
            line["reason"] = reason
        lines.append(line)

    # ⭐⭐ THE BASIS TRAVELS. Taken from the Multiverse view where present so the
    # two surfaces cannot explain the same number differently; read from the
    # registry otherwise. Never restated here.
    basis = sigma or (multiverse or {}).get("uncertainty_basis")
    if basis is None:
        from .multiverse import sigma_basis
        basis = sigma_basis()

    return {
        "has_data": any(ln["traceable"] for ln in lines),
        "lines": lines,
        # ⭐ NAMED, so a reader can see WHICH questions went unanswered without
        # counting — and so a lost line cannot hide (III.4).
        "absent_lines": [ln["n"] for ln in lines if not ln["traceable"]],
        "line_count": len(lines),
        "expected_line_count": len(QUESTIONS),
        "uncertainty_basis": basis,
        "not_a_pack_input": NOT_A_PACK_INPUT,
    }


# ⭐⭐ RECORDED ON THE SURFACE so nobody later "completes" the pack with it.
NOT_A_PACK_INPUT = {
    "is_pack_input": False,
    "note": ("The Prescience Brief adds no pack input class. It summarises "
             "Prescience surfaces for a Prescience reader; the pack keeps its "
             "own inputs unchanged (§7j.7)."),
}


def include(app, get_db, require_company_member):
    """⭐ WIRED, and the chain is asserted link by link."""
    from fastapi import APIRouter, Depends

    from .accounts import get_current_user
    from .modules.identity.plans import require_prescience
    _tier = require_prescience(get_current_user)

    r = APIRouter(tags=["prescience"])

    @r.get("/companies/{company_id}/prescience-brief")
    def prescience_brief(company_id: int, db=Depends(get_db),
                         _m=Depends(require_company_member),
                         _t=Depends(_tier)):
        """⭐ Assembles from the two Prescience surfaces. No computation."""
        from .multiverse import build as mv_build
        from .prescience_decision import DecisionFrontier, TrajectoryCache
        from .resilience_field import from_viability_row
        from .sentinel import RAYS, Viability

        fr = (db.query(DecisionFrontier).filter_by(company_id=company_id)
                .order_by(DecisionFrontier.id.desc()).first())
        tc = (db.query(TrajectoryCache)
                .filter_by(company_id=company_id, tier="full")
                .order_by(TrajectoryCache.id.desc()).first())
        if tc is None:
            tc = (db.query(TrajectoryCache).filter_by(company_id=company_id)
                    .order_by(TrajectoryCache.id.desc()).first())
        vrow = (db.query(Viability).filter_by(company_id=company_id)
                  .order_by(Viability.dataset_version.desc()).first())

        mv = mv_build(fr, tc.metrics if tc else None) if (fr or tc) else None
        rf = from_viability_row(vrow, rays=RAYS) if vrow else None
        return build(multiverse=mv, resilience=rf, company_id=company_id)

    app.include_router(r)
