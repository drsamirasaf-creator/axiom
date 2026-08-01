"""Causal Map — the attribution half. Every edge carries its label.

⭐⭐ RULED 1 Aug (§7j.2 ruling 4): an edge is `causal-evidence` ONLY when a
declared intervention PRECEDES the movement and the linkage is EXCLUSIVE — the
attribution rule applied to time. ⭐ No difference-in-differences, no
instrumental variables, no Bayesian nets in V1.0. **Everything else is
attribution, labelled as such.**

⭐⭐ THE LABEL IS THE PRODUCT. An unlabelled edge asserts causation by omission,
which is exactly the failure the three-way vocabulary exists to prevent. CORE
names the default: ⭐ **HYPOTHESIS**. A relationship earns its way up, never
down.

⭐⭐ AND THE TRAP THE RULING NAMES EXPLICITLY: EXCLUSIVITY OF LINKAGE IS NOT
EXCLUSIVITY OF CAUSE. A line with one linked initiative and three real drivers
must NOT promote. B11 already measures that gap — it is the RESIDUAL — so
`causal-evidence` additionally requires the declared shares to leave no
unexplained remainder. ⭐ Without that condition, `SOLE` would promote every
lonely link on a line nobody else bothered to declare.

⭐ NO INFERENCE ANYWHERE. This module reads declared rows and labels them. It
never correlates, regresses, fits or infers — asserted by AST, the same guard
B10 and B12 carry.

⭐ MEASURED BEFORE BUILDING: the five link tables and B11's attribution rule all
exist. What did not exist is the EDGE VIEW over them, which is this file.
"""
from datetime import datetime

# ── the vocabulary. ⭐ Three labels, and the default is the weakest. ─────────
ATTRIBUTION = "attribution"        # a human declared this relationship
CAUSAL_EVIDENCE = "causal-evidence"  # declared + exclusive + precedes + no residual
HYPOTHESIS = "hypothesis"          # ⭐ THE DEFAULT — asserted by nobody

LABELS = (HYPOTHESIS, ATTRIBUTION, CAUSAL_EVIDENCE)

# ⭐ The five declared link tables, named. Two lanes running found work already
# present under a name nobody searched for, so the sources are enumerated here
# rather than discovered at the call site.
SOURCE_TABLES = (
    "ax_initiative_line_links",   # B10 — initiative -> statement line, weighted
    "ax_kpi_objective_links",
    "ax_kpi_initiative_links",
    "ax_goal_initiative_links",
    "ax_kr_initiative_links",
)


def _edge(src, dst, label, basis, **extra):
    """⭐ EVERY EDGE CARRIES ITS LABEL AND WHY. A label with no basis is the same
    assertion-by-omission one step later."""
    e = {"source": src, "target": dst, "label": label, "basis": basis}
    e.update(extra)
    return e


def promotes(link, *, mode, residual_amount, period_start):
    """-> (label, basis). ⭐⭐ THE THRESHOLD, IN ONE PLACE.

    `causal-evidence` requires ALL FOUR. Each failure returns `attribution` with
    the reason it did not promote — ⭐ a demotion that does not say why reads as
    an oversight.
    """
    declared_at = link.get("declared_at")
    declared_by = link.get("declared_by")

    if not declared_by:
        # ⭐ A link with no declarer is an inference wearing a declaration's
        # clothes (B10's own words). It is not even attribution.
        return HYPOTHESIS, "no declarer is recorded, so nobody asserted this"

    if mode != "sole":
        return ATTRIBUTION, (
            "the linkage is not exclusive — other initiatives declare this line, "
            "so the movement is shared")

    if declared_at is None or period_start is None:
        return ATTRIBUTION, (
            "precedence cannot be established: "
            + ("the declaration carries no date"
               if declared_at is None else
               "the movement's period start is not known"))

    if not (declared_at < period_start):
        return ATTRIBUTION, (
            "the intervention was declared on or after the movement began, so it "
            "cannot have preceded it")

    # ⭐⭐ THE CONDITION THE RULING WARNS ABOUT. Exclusive LINKAGE with an
    # unexplained remainder means other drivers moved this line — they were
    # simply never declared. Promoting here would read one declaration as the
    # whole cause.
    if residual_amount is None:
        return ATTRIBUTION, (
            "the unexplained remainder cannot be computed, so exclusivity of "
            "CAUSE cannot be established from exclusivity of LINKAGE")
    if abs(residual_amount) > 1e-9:
        return ATTRIBUTION, (
            "the declared share leaves an unexplained remainder, so other "
            "drivers moved this line even though only one is linked")

    return CAUSAL_EVIDENCE, (
        "a declared intervention preceded the movement, the linkage is "
        "exclusive, and the declared share leaves no unexplained remainder")


def build(*, line_links, other_links, attribution=None, period_start=None):
    """-> the map. Pure over its inputs; reads nothing.

    `line_links`  : [{initiative_id, statement_line, declared_by, declared_at, weight}]
    `other_links` : [{source, target, kind, declared_by, flagged_absent}]
    `attribution` : B11's `attribute()` output, for modes and residuals
    """
    att = attribution or {}
    modes, residuals = {}, {}
    for row in att.get("attributed") or []:
        modes[(row.get("initiative_id"), row.get("statement_line"))] = row.get("mode")
    for line, r in (att.get("residual") or {}).items():
        residuals[line] = (r or {}).get("amount")

    edges, nodes = [], set()

    for lk in line_links or []:
        src = f"initiative:{lk.get('initiative_id')}"
        dst = f"line:{lk.get('statement_line')}"
        nodes.add(src)
        nodes.add(dst)
        mode = modes.get((lk.get("initiative_id"), lk.get("statement_line")))
        label, basis = promotes(
            lk, mode=mode,
            # ⭐ a line with NO residual entry has no unexplained remainder;
            # a line WITH one may carry None, which means "not computable" and
            # is a different fact from zero.
            residual_amount=residuals.get(lk.get("statement_line"), 0.0),
            period_start=period_start)
        edges.append(_edge(src, dst, label, basis,
                           declared_by=lk.get("declared_by"),
                           declared_at=(lk["declared_at"].isoformat()
                                        if isinstance(lk.get("declared_at"), datetime)
                                        else lk.get("declared_at")),
                           declared_weight=lk.get("weight"),
                           mode=mode))

    for lk in other_links or []:
        src, dst = lk.get("source"), lk.get("target")
        nodes.add(src)
        nodes.add(dst)
        if lk.get("flagged_absent"):
            label, basis = HYPOTHESIS, (
                "the link references something that is not present, so the "
                "relationship is asserted but not resolvable")
        elif lk.get("declared_by"):
            # ⭐ THESE FOUR TABLES CARRY NO MOVEMENT AND NO WEIGHT, so no
            # residual exists and precedence cannot be tested against a figure.
            # They are attribution and cannot rise above it in V1.0.
            label, basis = ATTRIBUTION, (
                "a declared relationship; this link type carries no movement, "
                "so exclusivity of cause cannot be tested")
        else:
            label, basis = HYPOTHESIS, "no declarer is recorded"
        edges.append(_edge(src, dst, label, basis, kind=lk.get("kind"),
                           declared_by=lk.get("declared_by")))

    counts = {lab: sum(1 for e in edges if e["label"] == lab) for lab in LABELS}
    connected = {e["source"] for e in edges} | {e["target"] for e in edges}
    # ⭐⭐ ABSENCE DECLARES. A map that silently omits an unconnected node tells a
    # reader the company has no such driver.
    isolated = [{"node": n, "absent": "no declared relationship reaches this node"}
                for n in sorted(nodes - connected)]

    return {
        "has_data": bool(edges),
        "edges": edges,
        "nodes": sorted(nodes),
        "isolated": isolated,
        "counts": counts,
        # ⭐ COVERAGE ON THE SURFACE. "0 causal-evidence in 40 edges" and "0 in 0"
        # print the same tick and mean opposite things (III.4).
        "coverage": {"edges": len(edges), "nodes": len(nodes),
                     "isolated": len(isolated)},
        "vocabulary": {
            "default": HYPOTHESIS,
            "labels": list(LABELS),
            "threshold": ("causal-evidence requires a declared intervention that "
                          "PRECEDES the movement, EXCLUSIVE linkage, and NO "
                          "unexplained remainder"),
        },
        "methods_absent": METHODS_ABSENT,
    }


# ⭐⭐ RECORDED ON THE SURFACE, NOT ONLY IN THE LEDGER. A reader who knows what a
# causal map usually contains must be told what this one deliberately does not.
METHODS_ABSENT = {
    "present": False,
    "absent": ("difference-in-differences, instrumental variables and Bayesian "
               "networks are not used. They require a comparison group this "
               "platform does not have, and inventing one would be fabrication."),
}


def _rows(db, cid):
    """Read the five declared link tables. ⭐ Reads rows, computes nothing."""
    from .accounts import (GoalInitiativeLink, KpiInitiativeLink,
                           KpiObjectiveLink, KrInitiativeLink)
    from .initiative_lines import links_for

    line_links = [{"initiative_id": r.initiative_id,
                   "statement_line": r.statement_line,
                   "weight": r.weight,
                   "declared_by": r.declared_by_label or r.declared_by,
                   "declared_at": r.declared_at}
                  for r in links_for(db, cid)]

    other = []
    for model, kind, a, b in (
            (KpiObjectiveLink, "kpi->objective", "kpi_key", "goal_key"),
            (KpiInitiativeLink, "kpi->initiative", "kpi_key", "initiative_id"),
            (GoalInitiativeLink, "objective->initiative", "goal_key", "initiative_id"),
            (KrInitiativeLink, "key-result->initiative", "kr_key", "initiative_id")):
        for r in db.query(model).filter_by(company_id=cid).all():
            other.append({
                "source": f"{a.replace('_key','').replace('_id','')}:{getattr(r, a)}",
                "target": f"{b.replace('_key','').replace('_id','')}:{getattr(r, b)}",
                "kind": kind,
                "declared_by": getattr(r, "created_by", None),
                "flagged_absent": bool(getattr(r, "flagged_absent", False))})
    return line_links, other


def include(app, get_db, require_company_member):
    """⭐ WIRED, and the chain is asserted link by link."""
    from fastapi import APIRouter, Depends

    # ⭐⭐ PRESCIENCE-GATED (§7j.6, ruled 1 Aug). The TAB is gated; the pack's
    # inputs are not — see plans.require_prescience for why.
    from .accounts import get_current_user
    from .modules.identity.plans import require_prescience
    _tier = require_prescience(get_current_user)

    from .modules.identity.plans import showcase_tier_notice as _notice

    r = APIRouter(tags=["prescience"])

    @r.get("/companies/{company_id}/causal-map")
    def causal_map(company_id: int, db=Depends(get_db),
                   _m=Depends(require_company_member),
                   _t=Depends(_tier)):
        """⭐ The attribution half. Reads declared rows; infers nothing."""
        line_links, other = _rows(db, company_id)
        if not line_links and not other:
            # ⭐ ABSENCE DECLARES. An empty map reads as "nothing is connected",
            # which is a claim about the company rather than about the record.
            return {"has_data": False, "edges": [], "nodes": [], "isolated": [],
                    "counts": {lab: 0 for lab in LABELS},
                    "absent": ("no relationships have been declared for this "
                               "company yet"),
                    "methods_absent": METHODS_ABSENT,
                    "tier_notice": _notice(db, company_id)}
        out = build(line_links=line_links, other_links=other,
                    attribution=None, period_start=None)
        from .modules.identity.plans import showcase_tier_notice
        out["tier_notice"] = showcase_tier_notice(db, company_id)
        return out

    app.include_router(r)
