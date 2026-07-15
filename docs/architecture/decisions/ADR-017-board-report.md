# ADR-017 — The Board Report: one endpoint, two renderings, a marketing brochure

Status: accepted · Phase 16 · Companion: SPEC-004 Product §5

## Decisions

1. **One consolidated payload.** GET /intelligence/board-report/{id}
   runs the full engine suite once (~3s) and assembles it into a
   seven-section document on the four-question spine: Executive Summary,
   Where the Company Stands, What Is Likely Next, What Should Change, The
   Best Risk-Adjusted Decision, Valuation (DCF + multiples + real
   options), and an Advanced-Analytics Appendix. Every section carries a
   title and a one-line takeaway; the engine is the single source of
   every number and sentence in the PDF, so the document can never drift
   from the product.

2. **Read-open: the showcase report is the brochure.** The endpoint is
   read-tenant, so anonymous visitors download the Meridian showcase
   report freely — maximum marketing reach. A shared report is itself a
   lead-gen channel (Regent-branded footer + Powered by AXIOM).

3. **Confidential mode.** ?confidential=true returns a variant with
   absolute currency figures redacted (grades, percentages, ratios,
   multiples, and all narrative retained) for externally shared copies —
   the brochure-vs-boardroom distinction.

4. **Rendering: Lovable HTML-to-PDF is the production path** (Prompt 21)
   for design quality; a certified server-side ReportLab baseline
   (branded, charted, 8 pages) ships as the reference artifact and a
   fallback. The split keeps the "Download Report" button instant and
   the design iterable without backend redeploys.

## Consequences

Battery at 212; two glossary entries; no migration. The report is sized
for 18-25 rendered pages; it deliberately leads with narrative and one
insight per page rather than dumping every table, per the board-document
(not data-dump) principle.
