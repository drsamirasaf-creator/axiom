# ADR-009 — v1.0 completion: messaging, frontier, re-forecast, contact

Status: accepted · Phase 10 · Companion: Vol II Ch 12; SPEC-004 Product §1

## Decisions

### 1. The words ship with the platform

All product messaging — the two-audience definitions (organizations vs
DCT readers), per-page explainers (what / benefit / how to start), and
the Regent Financial contact block — is served by the API
(`/api/v1/platform/about`, `/api/v1/platform/pages`), exactly like the
glossary: one versioned source of truth, so the frontend can never
describe features the backend does not have. The intro video URL is an
environment variable (`AXIOM_INTRO_VIDEO_URL`), honestly null until the
video exists — set it on Railway when published, no deploy.

### 2. The value-risk frontier is over a real trade-off

Varying only WACC makes value and tail metrics co-move (one dominating
point, no frontier). The safety objective is therefore the TAIL SOLVENCY
MARGIN — CVaR95(EV) minus the D/E-implied recapitalized debt — which
leverage genuinely erodes while it raises expected value. Certified on
Meridian: six Pareto-efficient structures from D/E 0 to 1.25; everything
beyond dominated by the distress penalty; the lambda dial spans the set
exactly (0 -> 1.25, 1 -> 0).

### 3. Re-forecast closes the twin loop deterministically

After a sync, the proposal refits trend drivers on the post-sync evidence
and shows committed-vs-proposed side by side; persisting creates a new
lineage node (plan -> actuals -> re-plan) — the ADR-006 approval posture
achieved without AI. An AI-enriched rationale can layer on later behind
the usual gates.

## v1.0 scope statement

With Phase 10, AXIOM v1.0 is feature-complete against the original
program: intake -> derivation -> valuation -> intelligence -> benchmarking
-> monitoring -> re-planning, under identity, at 151 certified tests.
Named electives (deliberately out of v1.0): organizations, quarterly-
granularity syncs, real benchmark vintages (curated table swap-in),
password reset by email, AI re-forecast rationales, encrypted document
storage beyond Railway defaults.
