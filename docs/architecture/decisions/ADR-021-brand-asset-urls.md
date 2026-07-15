# ADR-021 — Serve brand assets by URL for the frontend

Status: accepted · Phase 18.4 · Fixes the un-embeddable logo

## Problem

The AXIOM logo PNGs live at services/api/assets/ in the BACKEND repo. The
Lovable frontend (axiom-web) is a SEPARATE deploy and cannot read the
backend filesystem, so every prompt instruction to "use axiom_white.png"
pointed at a file the frontend could not access — the logo silently failed
to embed in the app and the generated PDF, repeatedly, regardless of prompt
wording.

## Decision

Serve the whitelisted brand assets as public API URLs:
  GET /assets                — index + usage guidance
  GET /assets/axiom_white.png  (white knockout, for dark backgrounds)
  GET /assets/axiom_color.png  (color, for light backgrounds)
Whitelist-only (no arbitrary file serving), long cache header, and the
existing permissive CORS lets the frontend fetch cross-origin. The Lovable
prompt now references these URLs, not filesystem paths, so the logo is
actually reachable and WILL embed. Also corrected the stale /health phase
marker (10 -> 18).

## Consequence

Battery at 234. The frontend embeds the correct logo (white on navy, color
on light) by URL, in both the app and the PDF. Assets are versioned with
the backend deploy.
