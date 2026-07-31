"""§7s.1 Stage 2 — the shared component library, the spine, and the export.

⭐ SHARED COMPONENT LIBRARY, NOT A SHARED SPINE. Each section renders once, as a
component. **The Pack composes seven into an argument; the export enumerates all
of them.** Forcing the export through the spine would make it a worse export:
the Pack is SELECTIVE and fails by being noisy; the export is EXHAUSTIVE and
fails by being incomplete. A section gaining a field is picked up by both.

⭐ SAME COMPONENTS, DIFFERENT DATA SOURCE. The Pack renders from its FROZEN
SNAPSHOT; the on-demand export renders from LIVE state. That is the only
difference, and it is expressed as a `Source` rather than as two renderers —
a second renderer is how the two drift.

⭐ ABSENCE DECLARES. A section whose input is missing APPEARS, stating what is
missing and as of when. A section that silently does not render lets the reader
infer it had nothing to report, and in a dense document that leaves the building
that is fabrication by silence.
"""
from datetime import datetime, timezone

# ═══════════════════════════════════════════════════════════════════════════
# SOURCES — the only thing that differs between the two documents
# ═══════════════════════════════════════════════════════════════════════════


class Source:
    """What a component may read. Both documents implement this."""

    kind = "abstract"

    def dataset(self):
        """{payload, version, sha} or None."""
        raise NotImplementedError

    def klass(self, name):
        """A frozen/live input-class block in Stage 1's three-state shape."""
        raise NotImplementedError

    def versions(self):
        raise NotImplementedError


class FrozenSource(Source):
    """⭐ READS THE SNAPSHOT, NEVER LIVE STATE. This is what makes a published
    pack immutable: every input moving underneath it changes nothing here."""

    kind = "frozen"

    def __init__(self, frozen):
        self._f = frozen or {}

    def klass(self, name):
        return (self._f.get("classes") or {}).get(name) or {
            "present": False, "reason": f"'{name}' is not in this frozen set"}

    def dataset(self):
        b = self.klass("active_financial_dataset")
        return b if b.get("present") else None

    def versions(self):
        return self._f.get("versions") or {}

    def captured_at(self):
        return self._f.get("captured_at")


class LiveSource(Source):
    """⭐ READS LIVE, AND REUSES STAGE 1'S CAPTURES rather than re-deriving them.
    Two derivations of "the company's current inputs" would drift, and the
    export would slowly stop matching the pack for reasons no one could name."""

    kind = "live"

    def __init__(self, db, cid):
        from . import pack as P
        self._db, self._cid, self._P = db, cid, P
        self._cache = {}

    def klass(self, name):
        if name not in self._cache:
            fn = self._P.INPUT_CLASSES.get(name)
            if fn is None:
                self._cache[name] = {"present": False,
                                     "reason": f"no capture registered for '{name}'"}
            else:
                try:
                    self._cache[name] = self._P._jsonable(fn(self._db, self._cid))
                except Exception as exc:
                    self._cache[name] = {"present": False,
                                         "reason": f"capture failed: {exc}"}
        return self._cache[name]

    def dataset(self):
        b = self.klass("active_financial_dataset")
        return b if b.get("present") else None

    def versions(self):
        return self._P.pinned_versions(self._db, self._cid)

    def captured_at(self):
        return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════════════
# the section contract
# ═══════════════════════════════════════════════════════════════════════════

def _section(cid_, title, *, present, body=None, missing=None, gap=None):
    """⭐ EVERY SECTION RENDERS. `present: False` carries `missing`; it is never
    an omission. `gap` states a KNOWN structural gap — a section whose computation
    does not exist yet — which is a different claim from "this company has no
    data" and must not read as one."""
    out = {"id": cid_, "title": title, "present": bool(present)}
    if present:
        out["body"] = body or {}
    else:
        out["missing"] = missing or "input not available"
    if gap:
        out["gap"] = gap
    return out


def _payload(src):
    ds = src.dataset()
    return (ds or {}).get("payload")


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ PROVENANCE TRAVELS — §4x, and export is one of the two surfaces most
# likely to drop attribution
# ═══════════════════════════════════════════════════════════════════════════

def adjusted_figures(src):
    """Every overridden figure, as value AND attribution in one object.

    ⭐ AN OVERRIDDEN NUMBER REACHING ANY EXPORT BARE IS A FAIL. This returns the
    computed value, the adjusted value, the author, the reason and the date
    together — there is no shape here that yields an adjusted figure stripped of
    its authorship, which is the property the override feature exists to hold.

    ⭐ IT READS THE SOURCE, NOT THE DATABASE. A pack resolving overrides live
    would show today's adjustments against a frozen figure — the pack would
    change after publication, which is the whole thing Stage 1 prevents.
    """
    from .overrides import REASON_LABEL
    block = src.klass("cfo_overrides")
    if not block.get("present"):
        return []
    out = []
    for o in block.get("overrides") or []:
        out.append({
            "metric_ref": o.get("metric_ref"),
            "metric_label": o.get("metric_label"),
            "computed": o.get("computed_value_at_override"),
            "adjusted": o.get("override_value"),
            "adjusted_by": o.get("author_label"),
            "reason_category": o.get("reason_category"),
            "reason_label": REASON_LABEL.get(o.get("reason_category"),
                                             o.get("reason_category")),
            "reason_note": o.get("reason_note"),
            "adjusted_at": o.get("created_at"),
            # the rendered sentence, so no surface has to compose it and none
            # can compose it differently
            "attribution": _attribution_line(o, REASON_LABEL),
        })
    return out


def _attribution_line(o, REASON_LABEL):
    who = o.get("author_label") or "an authorised approver"
    why = REASON_LABEL.get(o.get("reason_category"), o.get("reason_category"))
    when = (o.get("created_at") or "")[:10]
    note = o.get("reason_note")
    line = (f"computed {o.get('computed_value_at_override')}, "
            f"adjusted to {o.get('override_value')} by {who}, {why}")
    if note:
        line += f" — {note}"
    if when:
        line += f", {when}"
    return line


# ═══════════════════════════════════════════════════════════════════════════
# THE COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════

def c_what_changed(src):
    """1 · What changed — long-run variance, plan against method."""
    from .modules.financials.router import compute_plan_vs_methods
    data = _payload(src)
    if not data:
        return _section("what_changed", "What changed", present=False,
                        missing=src.klass("active_financial_dataset").get("reason"))
    try:
        pv = compute_plan_vs_methods(data)
    except Exception as exc:
        return _section("what_changed", "What changed", present=False,
                        missing=f"variance could not be computed: {exc}")
    return _section("what_changed", "What changed", present=True, body=pv)


def c_why_ratios(src):
    """2 · Why — the ratio library.

    ⭐ A DECLARED STRUCTURAL GAP. Stage 1's enumeration found §7r's ratio LIBRARY
    is not built: `axiom_ratio_registry.yaml` is loaded only by
    `scripts/check-ratio-shapes.py`, never by production code. Per the dispatch
    this renders from what EXISTS — the dashboard's computed ratios — and DECLARES
    the gap rather than omitting the section. Omitting it would let the reader
    infer the company has no ratios to report.
    """
    from .modules.financials import engines as fin
    gap = ("the §7r ratio library is not built; these are the dashboard's "
           "computed ratios, not a registry-versioned ratio set")
    data = _payload(src)
    if not data:
        return _section("why_ratios", "Why", present=False, gap=gap,
                        missing=src.klass("active_financial_dataset").get("reason"))
    try:
        dm = fin.dashboard_metrics(data)
    except Exception as exc:
        return _section("why_ratios", "Why", present=False, gap=gap,
                        missing=f"ratios could not be computed: {exc}")
    return _section("why_ratios", "Why", present=True, gap=gap,
                    body={"metrics": dm,
                          "ratio_registry": src.versions().get("ratio_registry")})


def c_what_is_likely(src):
    """3 · What is likely — the forecast."""
    block = src.klass("forecast_sets")
    data = _payload(src)
    body = {"forecast_sets": block}
    if data:
        from .modules.financials import engines as fin
        try:
            body["auto_forecast"] = fin.auto_forecast(data, {})
        except Exception as exc:
            body["auto_forecast_missing"] = str(exc)
    if not data and not block.get("present"):
        return _section("what_is_likely", "What is likely", present=False,
                        missing=block.get("reason"))
    return _section("what_is_likely", "What is likely", present=True, body=body)


def c_what_is_at_risk(src):
    """4 · What is at risk — the viability kernel, Sentinel, and the Watch."""
    caches = src.klass("computed_caches")
    sentinel = src.klass("sentinel_state")
    watch = src.klass("watch_events")
    if not any(b.get("present") for b in (caches, sentinel, watch)):
        return _section("what_is_at_risk", "What is at risk", present=False,
                        missing=caches.get("reason"))
    return _section("what_is_at_risk", "What is at risk", present=True,
                    body={"viability": (caches.get("viability")
                                        if caches.get("present") else None),
                          "frontier": (caches.get("frontier")
                                       if caches.get("present") else None),
                          # ⭐ THE WATCH APPEARS HERE AS A PACK SECTION, per §7s —
                          # what fired during the period, what was decided in
                          # response, and what it turned out to be worth.
                          # Delivery stays event-timed; this is the record.
                          "watch": src.klass("watch_events"),
                          "sentinel_raw": sentinel,
                          "dispositions": src.klass("dispositions")})


def c_initiatives(src):
    """5 · Which initiatives are underperforming."""
    block = src.klass("initiatives")
    if not block.get("present"):
        return _section("initiatives", "Which initiatives are underperforming",
                        present=False, missing=block.get("reason"))
    rows = block.get("initiatives") or []
    at_risk = [r for r in rows
               if (r.get("status") in ("at_risk", "off_track", "blocked")
                   or r.get("rag") in ("red", "amber"))]
    return _section("initiatives", "Which initiatives are underperforming",
                    present=True,
                    body={"total": len(rows), "underperforming": at_risk,
                          "milestones": block.get("milestones"),
                          "blockers": block.get("blockers")})


def c_what_to_do_next(src):
    """6 · What to do next — enterprise optimisation."""
    from .modules.intelligence.engines import optimize_analytics
    data = _payload(src)
    if not data:
        return _section("what_to_do_next", "What to do next", present=False,
                        missing=src.klass("active_financial_dataset").get("reason"))
    try:
        body = optimize_analytics(data)
    except Exception as exc:
        return _section("what_to_do_next", "What to do next", present=False,
                        missing=f"optimisation could not be computed: {exc}")
    return _section("what_to_do_next", "What to do next", present=True,
                    body={"optimisation": body,
                          "moves": src.klass("strategic_move_library")})


def c_value_bridge(src):
    """7 · How those actions affect cash flow and equity value.

    ⭐ THE VALUE BRIDGE CLOSES THE DOCUMENT, and §7s.5 IS NOT BUILT. Every other
    section exists in some form elsewhere in the product; a bridge stating that a
    named initiative slipped and that this is a specific quantity of equity value
    does not. The section renders the equity-value endpoints it CAN — so the
    reader sees the value, not a blank — and declares that the driver
    decomposition and residual are not yet built.
    """
    gap = ("§7s.5 is not built: the driver decomposition and its residual are "
           "not computed, so this section states equity value without "
           "attributing its movement to drivers")
    data = _payload(src)
    if not data:
        return _section("value_bridge", "How this affects cash flow and equity "
                        "value", present=False, gap=gap,
                        missing=src.klass("active_financial_dataset").get("reason"))
    from .modules.valuation import engines as val
    mode = "proforma" if (data.get("periods") or {}).get("forecast") else "auto_forecast"
    try:
        run = val.run(data, mode)
    except Exception as exc:
        return _section("value_bridge", "How this affects cash flow and equity "
                        "value", present=False, gap=gap,
                        missing=f"valuation could not be computed: {exc}")
    return _section("value_bridge", "How this affects cash flow and equity value",
                    present=True, gap=gap,
                    body={"mode": mode, "valuation": run,
                          "runs": src.klass("valuation_runs")})


# ── export-only components: exhaustive, not selective ───────────────────────

def c_proforma(src):
    from .modules.financials import engines as fin
    data = _payload(src)
    if not data:
        return _section("proforma", "Pro forma financial statements",
                        present=False,
                        missing=src.klass("active_financial_dataset").get("reason"))
    try:
        return _section("proforma", "Pro forma financial statements", present=True,
                        body=fin.build_statements(data)
                        if hasattr(fin, "build_statements") else {"payload": data})
    except Exception as exc:
        return _section("proforma", "Pro forma financial statements",
                        present=False, missing=str(exc))


def c_assessment(src):
    block = src.klass("assessment_cycle")
    if not block.get("present"):
        return _section("assessment", "Organisational assessment", present=False,
                        missing=block.get("reason"))
    return _section("assessment", "Organisational assessment", present=True,
                    body=block)


def c_okr(src):
    block = src.klass("okr_rows")
    if not block.get("present"):
        return _section("okr", "Objectives, key results and KPIs", present=False,
                        missing=block.get("reason"))
    return _section("okr", "Objectives, key results and KPIs", present=True,
                    body=block)


def c_documents(src):
    block = src.klass("documents")
    if not block.get("present"):
        return _section("documents", "Documents and memoranda", present=False,
                        missing=block.get("reason"))
    return _section("documents", "Documents and memoranda", present=True,
                    body=block)


def c_adjustments(src):
    """⭐ THE DISCLOSURE SECTION. Every CXO adjustment in force, with its full
    attribution. It renders even when empty — "no adjustments were made" is a
    statement a board needs, and an omitted section does not make it."""
    adj = adjusted_figures(src)
    return _section("adjustments", "Executive adjustments and their attribution",
                    present=True,
                    body={"count": len(adj), "adjustments": adj,
                          "note": ("No figures were adjusted in this period."
                                   if not adj else
                                   "Every adjusted figure below shows its "
                                   "computed value, its author and its reason.")})


def c_provenance(src):
    """The pinned versions and the frozen input inventory."""
    return _section("provenance", "Provenance — what produced these figures",
                    present=True,
                    body={"versions": src.versions(),
                          "captured_at": src.captured_at(),
                          "source_kind": src.kind})


# ⭐ THE COMPONENT LIBRARY. One entry per section; both documents draw from here.
COMPONENTS = {
    "what_changed": c_what_changed,
    "why_ratios": c_why_ratios,
    "what_is_likely": c_what_is_likely,
    "what_is_at_risk": c_what_is_at_risk,
    "initiatives": c_initiatives,
    "what_to_do_next": c_what_to_do_next,
    "value_bridge": c_value_bridge,
    "proforma": c_proforma,
    "assessment": c_assessment,
    "okr": c_okr,
    "documents": c_documents,
    "adjustments": c_adjustments,
    "provenance": c_provenance,
}

# ⭐ THE PACK'S CANONICAL ORDER (§7s). Seven questions, and the Value Bridge
# closes the document — the last thing the reader sees is the only claim
# unavailable anywhere else.
SPINE = ["what_changed", "why_ratios", "what_is_likely", "what_is_at_risk",
         "initiatives", "what_to_do_next", "value_bridge"]

# ⭐ THE PACK ALWAYS CARRIES ITS DISCLOSURE AND PROVENANCE, outside the spine.
# They are not one of the seven questions; they are what makes the seven
# answerable. §4x: an overridden number reaching any export bare is a fail.
PACK_ALWAYS = ["adjustments", "provenance"]


def render_pack(src):
    """The Pack — SELECTIVE. Seven sections in canonical order, plus disclosure."""
    sections = [COMPONENTS[k](src) for k in SPINE]
    sections += [COMPONENTS[k](src) for k in PACK_ALWAYS]
    return {"document": "pack", "spine": list(SPINE),
            "source_kind": src.kind, "sections": sections,
            "declared_absences": [s["id"] for s in sections if not s["present"]],
            "declared_gaps": [s["id"] for s in sections if s.get("gap")]}


def render_export(src):
    """The export — EXHAUSTIVE. Every component, in registry order.

    ⭐ NOT ON THE SPINE, DELIBERATELY. The export's purpose is that a reader
    without app access sees what a user sees; it fails by being incomplete.
    Forcing it through a selective seven-section argument would make it a worse
    export, and the ruling that it must not is recorded in §7s.
    """
    sections = [COMPONENTS[k](src) for k in COMPONENTS]
    return {"document": "export", "source_kind": src.kind, "sections": sections,
            "declared_absences": [s["id"] for s in sections if not s["present"]],
            "declared_gaps": [s["id"] for s in sections if s.get("gap")]}


def render_hash(doc):
    import hashlib
    import json
    return hashlib.sha256(json.dumps(doc, sort_keys=True, separators=(",", ":"),
                                     default=str).encode("utf-8")).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# ⭐ EXPORT-ONLY: the advanced-analytics surfaces
# ─────────────────────────────────────────────────────────────────────────────
# The export is EXHAUSTIVE — "a reader without app access sees what a user sees".
# The coverage guard found 17 surfaces the app rendered and the export did not.
# These components carry the ones that are genuinely SECTIONS; the remainder are
# exempted in the guard with a stated reason each, never as a blanket skip.
#
# ⭐ NONE OF THESE IS ON THE SPINE. The Pack is selective and fails by being
# noisy; adding these to it would make it a worse Pack for the same reason
# forcing the export onto the spine would make a worse export.

def _try(thunk):
    """Run a surface behind an error boundary.

    ⭐ IT TAKES A THUNK, NOT (fn, *args). The first version was
    `_try(scenario, data, "baseline")`, which passes `scenario` as an ARGUMENT —
    no call node exists, so no static reader can see that this component renders
    that surface, and the export coverage guard correctly reported all ten as
    uncarried. Same lesson as the aliased import in Stage 1: make the code plain
    rather than teach the guard to chase indirection. `lambda: scenario(...)`
    keeps the error boundary and leaves a real call for anything reading the AST.
    """
    try:
        return {"ok": True, "value": thunk()}
    except Exception as exc:
        # ⭐ NAMED, NOT SWALLOWED. A surface that could not compute is reported
        # as such; dropping it would recreate the silent staleness this whole
        # guard exists to end.
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def c_scenarios(src):
    """Scenario, scenario-pro and what-if — the app's scenario surfaces."""
    from .modules.intelligence.engines import scenario, scenario_pro, what_if
    data = _payload(src)
    if not data:
        return _section("scenarios", "Scenarios and what-if", present=False,
                        missing=src.klass("active_financial_dataset").get("reason"))
    return _section("scenarios", "Scenarios and what-if", present=True,
                    body={"scenario": _try(lambda: scenario(data, "baseline")),
                          "scenario_pro": _try(lambda: scenario_pro(data, "baseline")),
                          "what_if": _try(lambda: what_if(data, {}))})


def c_readiness(src):
    """ANFIS readiness and the target state."""
    from .modules.intelligence.engines import anfis_readiness, target_state
    data = _payload(src)
    if not data:
        return _section("readiness", "Readiness and target state", present=False,
                        missing=src.klass("active_financial_dataset").get("reason"))
    return _section("readiness", "Readiness and target state", present=True,
                    body={"readiness": _try(lambda: anfis_readiness(data)),
                          "target_state": _try(lambda: target_state(data))})


def c_levers(src):
    """Optimal levers and the unified optimisation."""
    from .modules.intelligence.engines import optimal_levers, unified_optimization
    data = _payload(src)
    if not data:
        return _section("levers", "Levers and unified optimisation",
                        present=False,
                        missing=src.klass("active_financial_dataset").get("reason"))
    return _section("levers", "Levers and unified optimisation", present=True,
                    body={"optimal_levers": _try(lambda: optimal_levers(data)),
                          "unified": _try(lambda: unified_optimization(data))})


def c_real_options(src):
    from .modules.valuation.engines import real_option
    data = _payload(src)
    if not data:
        return _section("real_options", "Real options", present=False,
                        missing=src.klass("active_financial_dataset").get("reason"))
    return _section("real_options", "Real options", present=True,
                    body={"real_option": _try(lambda: real_option(data, "expand"))})


def c_coverage(src):
    """Data coverage — what the company has supplied and what it has not.

    ⭐ THIS IS THE ABSENCE SECTION THE EXPORT NEVER HAD. It states what is
    missing as a first-class figure rather than leaving the reader to notice
    which tables are short."""
    from .modules.financials.engines import data_coverage
    data = _payload(src)
    if not data:
        return _section("coverage", "Data coverage", present=False,
                        missing=src.klass("active_financial_dataset").get("reason"))
    return _section("coverage", "Data coverage", present=True,
                    body={"coverage": _try(lambda: data_coverage(data))})


def c_reforecast(src):
    from .modules.twin.engines import reforecast_proposal
    data = _payload(src)
    if not data:
        return _section("reforecast", "Reforecast proposal", present=False,
                        missing=src.klass("active_financial_dataset").get("reason"))
    return _section("reforecast", "Reforecast proposal", present=True,
                    body={"proposal": _try(lambda: reforecast_proposal(data))})


COMPONENTS.update({
    "scenarios": c_scenarios,
    "readiness": c_readiness,
    "levers": c_levers,
    "real_options": c_real_options,
    "coverage": c_coverage,
    "reforecast": c_reforecast,
})
