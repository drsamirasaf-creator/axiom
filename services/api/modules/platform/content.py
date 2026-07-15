"""Platform messaging — backend-owned copy (Phase 10, ADR-009).

The words users read about AXIOM ship with the platform itself, exactly
like the glossary: one source of truth, versioned with the code, so the
frontend can never drift from what the product actually does.
"""
import os

ABOUT = {
    "product": "AXIOM",
    "tagline": "The enterprise, as a living mathematical model.",
    # -------- audience 1: organizations -----------------------------------
    "for_organizations": {
        "title": "AXIOM for Organizations",
        "definition": (
            "AXIOM builds a living digital twin of your company — your "
            "financial statements, your plan, your risks — and applies "
            "advanced mathematical optimization and AI to the questions "
            "boards actually ask: What is the business worth, as a "
            "distribution rather than a single number? How far is it from "
            "its value-maximizing configuration? Which moves create the "
            "most value? And when reality deviates from plan — by how "
            "much, and what should change?"),
        "benefits": [
            {"title": "Valuation you can defend",
             "text": "Deterministic DCF plus a seeded Monte Carlo layer: "
                     "enterprise value with confidence intervals, VaR, and "
                     "a risk-adjusted headline — every figure reproducible "
                     "and self-certifying."},
            {"title": "Know where you stand",
             "text": "Apples-to-apples benchmarking against sector "
                     "averages or your own named peers, translated onto "
                     "your books: what a sector-typical performer would "
                     "earn on your revenue, beside what you actually earn."},
            {"title": "A recommendation engine with mathematics behind it",
             "text": "Risk-adjusted enterprise optimization ranks the "
                     "moves — capital structure, working capital, margin "
                     "programs — by expected value impact, and prices the "
                     "health of the firm as distance from its optimum."},
            {"title": "A twin that stays honest",
             "text": "When a period closes, actuals sync against the "
                     "committed plan: forecast accuracy is scored, model "
                     "drivers are re-estimated, and valuation drift is "
                     "measured — with the original plan preserved as the "
                     "audit trail."},
            {"title": "AI that proposes, never decides",
             "text": "Upload a strategy memo and AXIOM's AI extracts "
                     "suggested assumptions — each with a verbatim source "
                     "quote, checked against published bounds, and applied "
                     "only after your explicit approval."},
        ],
        "uniqueness": (
            "What makes AXIOM different is the marriage of three things "
            "that rarely coexist: a true digital twin of the organization, "
            "rigorous stochastic optimization and valuation mathematics, "
            "and gated AI. The AI proposes; deterministic, certified "
            "engines dispose. Every number on every screen can be "
            "reproduced by hand from published formulas."),
    },
    # -------- audience 2: DCT readers, students, instructors ---------------
    "for_dct": {
        "title": "AXIOM as the Computational Laboratory of DCT",
        "definition": (
            "AXIOM is the executable companion to Dynamic Corporate "
            "Transformation (Springer, Volumes I–II). Every major "
            "construct in the books — the enterprise state, risk-adjusted "
            "enterprise optimization, stochastic valuation, "
            "distributionally robust decisions, learning dynamics — runs "
            "here as a live engine, keyed to the course website's "
            "laboratories and seeds, so theory can be executed, not just "
            "read."),
        "benefits": [
            {"title": "Certified against the labs",
             "text": "Engines carry the same seeds and checkpoint values "
                     "as the course laboratories; a green badge on screen "
                     "means the mathematics reproduced the book."},
            {"title": "From chapter to console",
             "text": "The course workspace deep-links each module to its "
                     "live experience: run the chapter's model, vary its "
                     "parameters, watch the results update instantly."},
            {"title": "Research-grade transparency",
             "text": "No black boxes: formulas, thresholds, weights, and "
                     "seeds are published in the interface, and every "
                     "stochastic result is replayable."},
        ],
    },
    "contact": {
        "heading": "Bring AXIOM to your organization",
        "text": ("If your firm would like to use AXIOM for valuation, "
                 "benchmarking, or enterprise transformation work, contact "
                 "Regent Financial."),
        "firm": "Regent Financial",
        "email": "samir@theregentfinancial.com",
    },
}

PAGES = {
    "dashboard": {
        "title": "Executive Dashboard",
        "what": "A single view of enterprise health: the KPI strip, the Health Index, and trend charts for your selected company.",
        "benefit": "Understand the state of the business in thirty seconds — and whether it is creating or eroding value (ROIC vs WACC).",
        "start": "Pick a dataset; if you have none yet, create one on Data Input."},
    "data_input": {
        "title": "Data Input",
        "what": "Where company financials enter AXIOM: download a GAAP/IFRS template, upload it, or type statements directly. Supporting documents (strategy memos, board papers) attach here too.",
        "benefit": "Ten minutes of input unlocks everything else — valuation, benchmarking, recommendations, and monitoring all run from this data.",
        "start": "Download a template, fill the highlighted cells, and upload — AXIOM validates every cell and tells you exactly what to fix."},
    "valuation": {
        "title": "Valuation",
        "what": "Discounted cash flow on your pro forma or on AXIOM's trend forecast, plus a Monte Carlo layer that treats value as a distribution — with sensitivity grids, the EV bridge, and stress testing under distributional ambiguity.",
        "benefit": "A defensible answer to 'what is it worth' — including how confident you should be, and how wrong your assumptions can be before the answer flips.",
        "start": "Select a dataset and a mode; results recompute instantly as you move assumptions."},
    "risk_analysis": {
        "title": "Risk Analysis",
        "what": "Robust decision tools from the DCT program: chance-constrained sizing, distributionally robust choice, and data-driven robustness radii.",
        "benefit": "Make decisions that survive being wrong about the probabilities — and know exactly how much evidence licenses the bolder choice.",
        "start": "Pick an analysis, adjust its parameters, and read the certificates that prove the answer."},
    "benchmarking": {
        "title": "Benchmarking",
        "what": "Your KPIs against sector averages or a peer set you name, translated onto your own books: what a sector-typical performer would earn on your revenue, beside your actuals, with traffic lights and one performance index.",
        "benefit": "Know if you are over- or under-performing peers — in plain currency terms and in words, not just ratios.",
        "start": "Choose a sector (or enter 2+ peers) and run the comparison."},
    "twin_monitoring": {
        "title": "Twin Monitoring",
        "what": "The living-model loop: when a period closes, enter actuals; AXIOM scores forecast accuracy, re-estimates the model's drivers, measures valuation drift against plan, and can propose a re-forecast.",
        "benefit": "Your valuation stops being a point-in-time document and becomes a model that learns — with the original plan preserved as the audit trail.",
        "start": "Select a dataset with a committed forecast and enter actuals for the next plan year."},
    "optimization": {
        "title": "Enterprise Optimization (REO)",
        "what": "The risk-adjusted enterprise optimization engine: certified problems from the DCT volumes, solved live with optimality certificates.",
        "benefit": "See the book's central machinery — value maximization under risk and constraints — run on real parameters.",
        "start": "Choose a problem, vary its inputs, and inspect the certificates."},
    "simulation": {
        "title": "Dynamics & Simulation",
        "what": "Enterprise dynamics scenarios: state evolution, shocks, and trajectories from the DCT dynamics engine.",
        "benefit": "Intuition for how enterprises move through time under uncertainty — the book's dynamics, executable.",
        "start": "Pick a scenario and run it."},
    "learning_lab": {
        "title": "Learning Lab",
        "what": "Adaptive learning experiments from the DCT program — estimation, generalization, and feedback dynamics.",
        "benefit": "Hands-on grounding for the learning mathematics used across the platform.",
        "start": "Choose an experiment and run it with its default (certified) parameters first."},
    "course_workspace": {
        "title": "Course Workspace",
        "what": "The bridge to the DCT course website: each course module deep-links to its live AXIOM experience.",
        "benefit": "Move from a chapter to a running model in one click.",
        "start": "Follow a module link from the course site, or browse the module list here."},
}


def intro_video_url() -> str | None:
    """Set AXIOM_INTRO_VIDEO_URL on Railway when the video is published —
    the landing page picks it up without a deploy; until then the frontend
    hides the player (never a broken embed)."""
    return os.environ.get("AXIOM_INTRO_VIDEO_URL") or None


# ---- The board report brand block (Phase 16, ADR-017) -----------------------
REPORT_BRAND = {
    "product": "AXIOM",
    "tagline": "The enterprise, as a living mathematical model.",
    "prepared_by": "Regent Financial",
    "contact_email": "samir@theregentfinancial.com",
    "powered_by": "Powered by AXIOM — axiomdynamics.app",
    "confidentiality_line": ("This report was generated by AXIOM from the "
                             "figures on file. It is intended for the board "
                             "and executive team of the subject company."),
    "methodology_note": ("Every figure in this report is reproducible from "
                         "published formulas and seeds. Valuations combine "
                         "deterministic DCF with seeded Monte Carlo; risk, "
                         "optimization, and real-options results follow the "
                         "Dynamic Corporate Transformation methodology."),
}


# ---- Safe harbor + EULA (Phase 16.2) ----------------------------------------
SAFE_HARBOR = (
    "IMPORTANT — PLEASE READ. This report is generated automatically by the "
    "AXIOM platform from figures supplied by or on behalf of the subject "
    "company. It is provided for informational and illustrative purposes "
    "only and does NOT constitute strategic, operational, financial, "
    "investment, accounting, tax, or legal advice from Regent Financial or "
    "any of its members, partners, employees, officers, or shareholders, and "
    "no advisory, fiduciary, or professional relationship is created by its "
    "delivery or use. The figures herein are the outputs of mathematical "
    "models applied to client-supplied data; Regent Financial does not audit, "
    "verify, warrant, or confirm the accuracy, completeness, or suitability "
    "of any input or result. No person should rely on this report for any "
    "decision. All valuations, forecasts, probabilities, and recommendations "
    "are inherently uncertain and may differ materially from actual outcomes. "
    "To the maximum extent permitted by law, Regent Financial and its "
    "affiliates disclaim all warranties and shall have no liability for any "
    "loss or damage arising from use of or reliance on this report. Use of "
    "AXIOM is governed by the End User License Agreement accepted at "
    "registration.")

EULA_SUMMARY = (
    "By subscribing to AXIOM you agree to the End User License Agreement: the "
    "software and its outputs are provided 'as is' without warranty; they are "
    "informational only and not professional advice; you are responsible for "
    "the data you input and for your own decisions; Regent Financial's "
    "liability is limited to the maximum extent permitted by law; and you may "
    "not resell, reverse-engineer, or misrepresent the platform. Full terms "
    "are presented for acceptance at sign-up.")


# ---- Financial-statement disclaimer (Phase 18.2) ----------------------------
# Rides on every pro-forma / comprehensive-income statement. Makes explicit
# that these are unaudited model estimates, not certified financials.
STATEMENTS_DISCLAIMER = (
    "UNAUDITED ESTIMATES. These pro forma financial statements are "
    "forward-looking projections generated by mathematical models from "
    "client-supplied figures. They are NOT audited, reviewed, or compiled by "
    "an independent accountant, and are NOT certified as compliant with US "
    "GAAP, IFRS, or any other accounting framework. The accounting-framework "
    "label indicates the basis of presentation only, not certification. All "
    "figures are estimates subject to modeling assumptions, data limitations, "
    "and error, and may differ materially from actual reported results. They "
    "must not be relied upon for financial reporting, tax, audit, lending, or "
    "investment purposes.")
