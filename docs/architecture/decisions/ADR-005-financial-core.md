# ADR-005 — The Financial Core: templates, FCFE, documents, RAEV, Health Index

Status: accepted · Phase 6 · Companion spec: DCT-SPEC-004 (Product §5/§6/§7/§8, Math §3, Data §5/§6)

## Context

Phase 6 delivers the client-facing financial workflow: Data Input,
Valuation, and the Executive Dashboard. The SPEC-004 consistency audit
(2026-07) found the feature set consistent with the spec, with four points
requiring an explicit engineering decision. This ADR records them.

## Decisions

### 1. Identity remains deferred (ADR-002 reaffirmed, one more phase)

Phase 6 ships single-tenant behind the `X-Axiom-Tenant` header, with the
frontend displaying a persistent notice: **demonstration environment — do
not upload confidential client data**. Authentication, per-user isolation,
and encrypted document storage are a prerequisite for any client-facing
advisory use and are committed ahead of that milestone (Product §2, §4).
Rationale: identity done properly is its own phase; bolting it onto the
Financial Core mid-build risks both.

### 2. Locked templates are the deterministic v0 of Intelligent Financial Mapping

Product §7.9/§7.10 prescribe free-form import with AI account mapping.
Phase 6 instead ships two protected input templates (US GAAP, IFRS) with a
fixed canonical line-item schema. This is a deliberate narrowing: a
deterministic, checkpoint-certifiable v0 of the same import requirement.
The xlsx workbook lock is **advisory only** (spreadsheet protection is
trivially removable); the integrity guarantee is the server-side parser,
which re-validates the template signature, every label, and every cell,
returning cell-level errors (Product §7.14). Free-form import with AI
mapping is the roadmap successor, not a replacement.

### 3. FCFE is a logged extension to the spec

SPEC-004 defines only firm-level free cash flow (Math §3.9). Phase 6 adds
FCFE = FCFF − interest·(1−T) + net borrowing, identity-checked against
NI + D&A − CapEx − ΔNWC + net borrowing on every derivation. Recommend a
one-paragraph amendment to Math §3.9 in the spec's next revision.

### 4. Risk-Adjusted Enterprise Value (RAEV), defined

Product §8.14/Math §3.14 require a Monte Carlo valuation distribution but
leave the headline risk-adjusted scalar open. Phase 6 defines
**RAEV = (1−λ)·mean + λ·CVaR₉₅**, λ ∈ [0,1] (default 0.5), over the seeded
EV distribution (seed 26060, 2 000 paths default). λ=0 is risk-neutral,
λ=1 is CVaR-only; the dial is a client-visible assumption, never hidden.

### 5. Enterprise Health Index v0 is a published composite

Product §5.6 lists the Health Index without a formula. v0 is the
deterministic composite documented in `financials/engines.health_index`
(value-creation spread, liquidity, leverage, growth; weights
0.35/0.25/0.20/0.20), reproducible by hand. The REO-distance formulation —
health as proximity of the current state to the risk-adjusted optimum —
replaces it in Phase 7.

### 6. Document upload is plumbing only in Phase 6

Storage/retrieval endpoints ship now (CA §3.4 data-fusion posture);
`ai_analysis` is honestly `null` until Phase 7 (SPEC-008 §4.10 — no
fabricated availability). Phase 7's analysis runs behind the §6.15/§8.8
gates: every AI-inferred assumption is explainable and requires user
approval before it can touch a valuation.

## Consequences

Three new tables (`financial_datasets`, `valuation_runs`,
`enterprise_documents`, migration 0005). Two new modules (`financials`,
`valuation`) with 25 new tests; the platform battery stands at 88.
Dependencies added: openpyxl, python-multipart.
