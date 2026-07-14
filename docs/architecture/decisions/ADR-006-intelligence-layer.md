# ADR-006 — The Intelligence Layer: AI gates, REO health, recommender, DRO stress

Status: accepted · Phase 7 · Companion spec: DCT-SPEC-004 (Product §5.9,
§6.15, §7.10, §8.8, §8.14; CA §3; Math §3; Vol II Ch 11)

## Governing principle

**The AI proposes; deterministic gates and certified engines dispose.**
No AI output can alter a stored dataset or enter a valuation without an
explicit, recorded user decision, and every admitted suggestion carries
machine-verified evidence.

## Decisions

### 1. AI document analysis behind three deterministic gates

`POST /intelligence/documents/{id}/analyze` sends the document text to the
Anthropic Messages API (model via `AXIOM_AI_MODEL`, default
`claude-sonnet-4-6`; single seam in `ai_client.complete`, monkeypatched in
tests). The model's proposals are then admitted only if they pass, in
order: (a) **whitelist** — the field is one of the published valuation
assumptions; (b) **bounds** — the value lies inside published numeric
bounds; (c) **explainability** — the `source_quote` appears verbatim
(whitespace-normalized) in the document. Gate (c) makes hallucination
structurally unrewarding: a quote the model invents is a rejection the
user can see, with the reason stated.

Approval (`/decisions`) records accept/reject per suggestion (§6.15);
`assemble_assumptions` folds **accepted suggestions only** into a
`/valuation/run` assumptions object. The deterministic core is untouched:
AI output becomes at most an *input the user chose*, priced by the same
certified engine as any hand-typed number.

Unconfigured key → honest 503, never a mock (SPEC-008 §4.10). v1 analyzes
text-like documents (txt/md/csv/json); PDF/DOCX extraction is roadmap.
Testing: the suite mocks `ai_client.complete` (offline, deterministic);
`scripts/ai_smoke.py` is the manual live check before deploy.

### 2. Testing posture for non-determinism

Phase 7 introduces the platform's first non-deterministic call. The
boundary is explicit: everything after `ai_client.complete` returns is
deterministic and unit-tested; the call itself is covered by the smoke
script, not the suite. CI stays green with no key and no network.

### 3. Enterprise Health Index v1 — REO distance (supersedes ADR-005 §5)

Health becomes proximity to the risk-adjusted value optimum, expressed in
value: `100 × [EV(WACC(x_cur)) / EV(WACC(x*))] × clamp(current_ratio, 0, 1)`
where `x*` minimizes the published distress-adjusted WACC curve
`kd(x) = kd_base + 0.01·max(0, x−1)²`, β relevered by Hamada from the
company's own unlevered beta (public: unlevered from the observed beta at
the current market D/E; private: the supplied industry beta). Certified:
Meridian's curve reproduces the Phase 6 WACC of 9.125% exactly at its
current structure, optimum at D/E 1.2 → 8.8326%, health 95.5.

**Compatibility:** the Phase 6 dashboard `health` block (v0 composite) is
unchanged — the deployed frontend keeps working. v1 lives at
`GET /intelligence/health/{dataset_id}`; PROMPT-09 promotes it to the
gauge with v0 as secondary.

### 4. Transformation path recommender

`GET /intelligence/recommendations/{dataset_id}` prices four candidate
moves through the certified valuation engine in trend-forecast space —
optimal capital structure (from the health curve), working-capital
release (−1pp NWC), operating margin (+50bp), growth investment (+1pp
growth funded by +0.5pp CapEx) — ranked by expected EV impact with the
exact parameter change disclosed. Datasets carrying a client pro forma are
evaluated on their historicals (the pro forma is never altered; guidance
is labeled trend-model-based). The engine is honest by construction:
growth funded below the cost of capital prices negative (Halcyon: −10.67).

### 5. DRO stress panel on valuation

`POST /valuation/stress` wraps the seeded Monte Carlo EV distribution in a
total-variation ambiguity ball (reusing the Phase 3 `_tv_worst_case`
machinery, Vol II Ch 11): the curve of worst-case mean EV over radii, plus
the **breakeven ambiguity radius** — the δ at which worst-case EV falls to
the senior-claims threshold (net debt + preferred + minority;
`threshold_override` for scenario analysis) — found by 60-step bisection.
Runs persist as `ValuationRun(mode="dro_stress")`. No schema change.

## Consequences

New module `intelligence` (ai_client, engines, router); valuation gains
`stress()` and `/stress`; glossary +14 terms; **no migration** (suggestions
live on `enterprise_documents.ai_analysis`, stress runs in
`valuation_runs`). httpx becomes a runtime dependency. Railway needs
`ANTHROPIC_API_KEY` set for live analysis. Test battery: 110.
Deferred to Phase 8: identity/auth (ADR-002) ahead of any client-facing
pilot; PDF/DOCX text extraction; MC-priced risk deltas on recommendations.
