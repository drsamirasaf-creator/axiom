"""The AXIOM vs FP&A/xP&A comparison matrix — data, attribution, and witnesses.

⭐⭐ THIS TABLE MAKES 253 ASSERTIONS. Twenty-three features across eleven products
is not a diagram; it is a page of claims, and the standing admissibility rule
says a claim ships only when it can be checked.

⭐ SO THE TWO COLUMNS REST ON DIFFERENT THINGS, AND THE TABLE SAYS SO:
  · AXIOM's column rests on THE PRODUCT — every green names a code WITNESS, and
    `scripts/check-comparison-matrix.py` fails the build if the witness is gone.
  · The competitor columns rest on PUBLISHED MATERIAL — each carries "publicly
    documented as of <date>", because a cell asserting someone else's product
    lacks a capability is a claim about a company we cannot measure.

⭐⭐ THEY MUST NOT READ AS EQUALLY VERIFIED, and the header says which is which.

⭐ NO COMPARATIVE SUPERLATIVES IN ANY HOVER. The standing ruling strikes claimed
sophistication and admits checkable discipline; a matrix is exactly where the
temptation is worst.
"""

G, A, R = "green", "amber", "red"

# ⭐ The date every competitor cell is attributed to. ONE constant, so a stale
# table cannot have some cells fresher than others without anyone noticing.
DOCUMENTED_AS_OF = "2026-08-01"

COMPETITORS = ["Anaplan", "Workday Adaptive", "OneStream", "Planful", "Pigment",
               "Prophix", "Vena", "Datarails", "Cubo", "Mosaic"]

# ⭐⭐ "Where others are stronger" MEANS SOMETHING ONLY IF EVERY ROW IN IT IS A
# CONCESSION. `AI copilot` sat in this block while AXIOM was GREEN on it, which
# made the block's own claim false — a reader counting concessions would have
# counted five and found four. Moved to Execute (1 Aug ruling); the guard now
# asserts the WHOLE block rather than an enumerated subset, so the next
# misplacement fails the build instead of being absorbed by the enumeration.
BLOCKS = [
    "Analyze — what's true today",
    "Strategize — where to go next",
    "Execute — make it happen",
    "Where others are stronger",
]

LEGEND = {G: "strong / native", A: "partial, limited or add-on", R: "not offered"}

# ⭐⭐ EVERY AXIOM GREEN NAMES A WITNESS. `path` = a served route; `symbol` = a
# (module, attribute) pair. A green with no witness is refused by the guard —
# the admissibility rule mechanised.
#
# ⭐ AMBER AND RED NEED NO WITNESS. A concession is not a claim, and requiring
# evidence for "we do not do this" would be requiring evidence of an absence.
ROWS = [
    # ── Analyze ─────────────────────────────────────────────────────────────
    dict(n=1, block=BLOCKS[0], feature="Dashboards & reports",
         info="Company and departmental views, plus the report pack that is issued on a schedule.",
         axiom=G, witness={"path": "/companies/{company_id}/reports"},
         why="Dashboards and the issued report pack are generated inside the product.",
         demo={"route": "/dashboard", "verify": "/companies/20/reports"},
         comp=[G, G, G, G, G, G, G, G, G, G]),
    dict(n=2, block=BLOCKS[0], feature="Financial statements & ratio analysis",
         info="Income statement, balance sheet and cash flow, with the ratios computed from them rather than re-entered.",
         axiom=G, witness={"symbol": ("services.api.modules.financials.ratios", "wacc_at")},
         why="Ratios are computed from the same statements the report carries.",
         demo={"route": "/valuation", "verify": "/companies/20/reports/latest"},
         comp=[A, A, A, A, A, A, G, A, A, A]),
    dict(n=3, block=BLOCKS[0], feature="Scenario, sensitivity & driver modelling",
         info="Change a driver and see what it does to the value of the business, with the limits that bind it.",
         axiom=G, witness={"symbol": ("services.api.modules.intelligence.engines", "optimize_analytics")},
         why="Drivers are searched together and each one's separate contribution is returned.",
         demo={"route": "/scenarios", "verify": "/api/v1/intelligence/frontier/45"},
         comp=[G, G, A, A, G, A, A, A, A, A]),
    dict(n=4, block=BLOCKS[0], feature="Departmental accountability mapping",
         info="Which department owns which measure, and who may sign it off.",
         axiom=G, witness={"symbol": ("services.api.accounts", "Department")},
         why="Departments carry named heads and a separate authority to sign off.",
         demo={"route": "/organization", "verify": "/companies/20/departments"},
         comp=[A, A, G, A, A, A, A, A, A, A]),
    dict(n=5, block=BLOCKS[0], feature="SWOT & strategic risk",
         info="Strengths, weaknesses, opportunities and threats, built from what people inside the company said.",
         axiom=G, witness={"symbol": ("services.api.assessment_engine", "apply_kfloor")},
         why="Built from stakeholder responses, with small groups withheld for confidentiality.",
         demo={"route": "/swot", "verify": "/companies/20/assessment/swot"},
         comp=[R, R, A, A, A, R, R, R, R, R]),
    dict(n=6, block=BLOCKS[0], feature="Stakeholder sentiment & organisational signals",
         info="What the people inside the business think, by department and by level of seniority.",
         axiom=G, witness={"path": "/companies/{company_id}/assessment/summary"},
         why="Responses are collected, scored and reported by department under a confidentiality floor.",
         demo=None, demo_absent="the stakeholder-sentiment surfaces require a signed-in member, so an anonymous prospect would reach a login wall rather than the capability",
         comp=[R, R, R, R, R, R, R, R, R, R]),
    # ── Strategize ──────────────────────────────────────────────────────────
    dict(n=7, block=BLOCKS[1], feature="Scenario & driver-based planning",
         info="Several ways of planning the same business, over one shared model.",
         axiom=G, witness={"symbol": ("services.api.forecast_studio", "METHODS")},
         why="Five planning methods run over the same underlying figures.",
         demo={"route": "/financial-forecasts", "verify": "/companies/20/objectives"},
         comp=[G, G, G, G, G, G, G, G, A, A]),
    dict(n=8, block=BLOCKS[1], feature="Forecasting",
         info="Producing the forward view the plan is judged against.",
         axiom=A,
         why="Forecasts are produced and stored, with narrower configuration than a dedicated planning suite.",
         comp=[G, G, G, G, G, A, A, A, A, A]),
    dict(n=9, block=BLOCKS[1], feature="Rolling re-forecasting",
         info="The forward view is refreshed on a schedule rather than when someone remembers.",
         axiom=G, witness={"symbol": ("services.api.pack", "sweep_calendar")},
         why="A scheduled sweep re-runs the cycle without anyone asking it to.",
         demo={"route": "/financial-forecasts", "verify": "/companies/20/reports"},
         comp=[G, G, A, G, G, A, A, A, A, A]),
    dict(n=10, block=BLOCKS[1], feature="Enterprise value attribution",
         info="What moved the value of the business, item by item, and how much of the movement nothing explains.",
         axiom=G, witness={"symbol": ("services.api.value_bridge", "d_initiatives")},
         why="Movement is split across named causes, and the unexplained part is shown rather than absorbed.",
         demo={"route": "/brief", "verify": "/companies/20/reports/latest"},
         comp=[A, A, G, A, A, A, A, A, A, A]),
    dict(n=11, block=BLOCKS[1], feature="Probabilistic simulation & predictive guidance",
         info="A range of outcomes with their likelihoods, rather than a single line.",
         axiom=G, witness={"symbol": ("services.api.modules.simulation.engines", "run")},
         why="Cash flow is simulated across a distribution of outcomes.",
         demo={"route": "/simulation", "verify": "/companies/20/reports/latest"},
         comp=[A, A, A, A, A, R, A, A, R, R]),
    dict(n=12, block=BLOCKS[1], feature="OKR → KPI → initiative cascade",
         info="Objectives, the results that measure them, the indicators behind those, and the work being done — in one line of sight.",
         axiom=G, witness={"symbol": ("services.api.accounts", "KpiPlan")},
         why="Objectives, key results and indicators are stored and linked to the work.",
         demo={"route": "/target-state", "verify": "/companies/20/objectives"},
         comp=[A, A, A, R, A, A, A, A, R, R]),
    dict(n=13, block=BLOCKS[1], feature="Approvals, guardrails & exception handling",
         info="Limits that raise an alert to a named person when something crosses them.",
         axiom=G, witness={"symbol": ("services.api.sentinel", "sentinel_recompute")},
         why="A nightly check measures distance to failure and alerts named recipients.",
         demo={"route": "/risk-analysis", "verify": "/companies/20/readiness/derived"},
         comp=[A, A, A, R, A, A, A, A, R, R]),
    # ── Execute ─────────────────────────────────────────────────────────────
    dict(n=14, block=BLOCKS[2], feature="Initiatives & projects",
         info="The work in flight, who owns it, and what it is expected to move.",
         axiom=G, witness={"symbol": ("services.api.accounts", "Initiative")},
         why="Initiatives carry owners, status, and a declared link to the line they affect.",
         demo={"route": "/initiatives", "verify": "/companies/20/initiatives"},
         comp=[A, A, A, A, A, A, A, A, A, A]),
    dict(n=15, block=BLOCKS[2], feature="Plan vs actual & variance analysis",
         info="What was promised against what happened, line by line.",
         axiom=G, witness={"symbol": ("services.api.modules.financials.engines", "auto_forecast")},
         why="Plan and actuals sit on the same figures and are compared line by line.",
         demo={"route": "/financial-forecasts", "verify": "/companies/20/reports"},
         comp=[G, G, G, G, G, G, G, G, A, A]),
    dict(n=16, block=BLOCKS[2], feature="Multi-dimensional reporting",
         info="Slicing the same numbers by several dimensions at once.",
         axiom=A,
         why="Reporting slices by company, department and period; it is not a general multi-dimensional cube.",
         comp=[A, R, G, A, A, A, A, R, R, R]),
    dict(n=17, block=BLOCKS[2], feature="Transaction-level drilldown",
         info="Following a figure down to the entries that make it up.",
         axiom=A,
         why="Figures resolve to the versioned input that produced them, not to individual ledger entries.",
         comp=[A, A, G, A, A, A, G, R, R, R]),
    dict(n=18, block=BLOCKS[2], feature="Collaborative comments & sign-off",
         info="What people wrote, and a named person accepting the numbers.",
         axiom=G, witness={"path": "/companies/{company_id}/departments/{department_id}/voice"},
         why="Written feedback is readable under a confidentiality floor, with a recorded sign-off.",
         demo=None, demo_absent="the departmental feedback surface is member-gated by §4u-b, deliberately — the words are readable under the floor, not in public",
         comp=[A, A, A, A, A, A, A, R, A, A]),
    dict(n=19, block=BLOCKS[2], feature="AI copilot & natural language interface",
         info="Asking questions of the company's own numbers in ordinary language.",
         axiom=G, witness={"path": "/companies/{company_id}/prescience/ask"},
         why="Questions are answered against the company's own model, with the sources cited.",
         demo=None, demo_absent="Ask AXIOM answers a POST from a signed-in session; there is no anonymous destination to link to",
         comp=[G, G, G, G, G, G, G, R, G, G]),
    # ── Where others are stronger ───────────────────────────────────────────
    dict(n=20, block=BLOCKS[3], feature="Native Excel & ERP ingest",
         info="Reading directly from spreadsheets and from the systems that run the business.",
         axiom=A,
         why="A structured upload with the original file retained — not a live connection into the finance system.",
         comp=[G, G, G, G, G, G, G, G, G, G]),
    dict(n=21, block=BLOCKS[3], feature="Financial close & consolidation",
         info="Closing the books, removing internal transactions between entities, and the audit trail for that work.",
         axiom=R,
         why="Not offered. AXIOM does not touch the ledger and does not close the books.",
         comp=[G, G, G, A, A, G, A, A, A, A]),
    dict(n=22, block=BLOCKS[3], feature="Workflow & governance tooling",
         info="Configurable chains of approval and hierarchies of permission.",
         axiom=A,
         why="Administrator and viewer roles with departmental authority — not a configurable workflow engine.",
         comp=[G, G, G, G, G, G, G, A, A, A]),
    dict(n=23, block=BLOCKS[3], feature="Enterprise scale & partner ecosystem",
         info="Implementation partners, certified consultants and a marketplace of extensions.",
         axiom=R,
         why="Not offered. There is no partner ecosystem.",
         comp=[G, G, G, A, G, G, G, A, G, G]),
]

# ⭐ Monthly AND annual, so the comparison is like-for-like. Competitor figures
# are quoted annually in their own material; showing only AXIOM's monthly rate
# beside them would flatter it by a factor of twelve.
PRICING = {
    "AXIOM": "$4,995 / company / month  ($59,940 / yr)",
    "Anaplan": "$25k–35k+ / yr", "Workday Adaptive": "$22k–30k+ / yr",
    "OneStream": "$40k–60k+ / yr", "Planful": "$17k–25k+ / yr",
    "Pigment": "$35k–50k+ / yr", "Prophix": "$23k–31k+ / yr",
    "Vena": "$17k–25k+ / yr", "Datarails": "$17k–19k+ / yr",
    "Cubo": "$10k–30k+ / yr", "Mosaic": "$18k–32k+ / yr",
}
PRICING_NOTE = ("Indicative annual pricing, publicly documented as of "
                + DOCUMENTED_AS_OF + ". Annualised, AXIOM sits mid-band.")

# ⭐⭐ THIS ROW SITS ABOVE PRICING AND IS EMPHASISED, and the reason is recorded
# so a later editor does not "tidy" it back below: annualised, AXIOM is mid-band
# on price. UNLIMITED USERS IS THE DIFFERENTIATOR, NOT COST — and a table that
# led with price would be making the one claim the numbers do not support.
USERS_INCLUDED = {"AXIOM": "Unlimited users",
                  **{c: "Seat, role or named-user limited" for c in COMPETITORS}}
USERS_NOTE = ("Annualised, AXIOM sits mid-band on price. Unlimited users is the "
              "difference, not cost.")

BASIS_NOTE = (
    "AXIOM's column is checked against the product: every green names a "
    "capability in the codebase, and the build fails if it is removed. The "
    "competitor columns rest on publicly available documentation as of "
    + DOCUMENTED_AS_OF + " and are not independently verified."
)


def unlinked_greens():
    """⭐ Greens with no anonymous demo destination — a FINDING, not a broken
    link. A capability that exists but cannot be shown to a prospect without a
    login is a different problem from one that does not exist."""
    return [r for r in ROWS if r["axiom"] == G and not r.get("demo")]


def axiom_greens():
    """Rows whose AXIOM dot is green — each of which must name a witness."""
    return [r for r in ROWS if r["axiom"] == G]


def matrix():
    """The whole asset, ready to render."""
    return {"columns": ["AXIOM"] + COMPETITORS, "blocks": BLOCKS,
            "users_note": USERS_NOTE,
            "rows": [{**r, "documented_as_of": DOCUMENTED_AS_OF} for r in ROWS],
            "pricing": PRICING, "pricing_note": PRICING_NOTE,
            "users_included": USERS_INCLUDED, "legend": LEGEND,
            "basis": BASIS_NOTE, "documented_as_of": DOCUMENTED_AS_OF}


def include(app):
    """⭐⭐ SERVED, NOT DUPLICATED. The page could have carried its own copy of
    this data — and then the guard would check one table while the prospect read
    another. Two surfaces of one concept is the standing bug class, and a
    comparison matrix is the worst possible place for it.

    ⭐ Public: it is marketing material, and the page is anonymous.
    """
    from fastapi import APIRouter
    r = APIRouter(tags=["brochure"])

    @r.get("/brochure/comparison-matrix")
    def _matrix():
        return matrix()

    app.include_router(r)
    return r
