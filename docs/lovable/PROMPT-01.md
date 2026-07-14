# Lovable Prompt 01 — AXIOM Shell + Enterprise + Optimization workspaces
(paste into Lovable after the Railway API URL exists; replace YOUR_RAILWAY_URL)

Build AXIOM, the enterprise optimization platform of the Dynamic Corporate
Transformation ecosystem. React + Tailwind, professional and calm.

DESIGN SYSTEM
Palette: deep pine #0B3D2E (primary surfaces, nav), brass #C8A24B (accents,
active states, primary buttons), soft brass #D9BE7A, ivory #F7F4EC (page
background), ink #17231F (text), moss #1B6B52 (success), gray #8A8F8B (muted).
Georgia or a serif for headings, a clean sans for body. Generous whitespace,
subtle rounded cards, no gradients, no stock imagery.

CRITICAL RULES
1. ALL data comes from the live API at: YOUR_RAILWAY_URL
   Store this as API_BASE in one config file. NEVER invent, mock, or hardcode
   data. If a request fails, show the error state — do not fabricate results.
2. Send header "X-AXIOM-Tenant: demo" on every request.
3. This frontend contains ZERO calculation logic. It renders what the API returns.

LAYOUT
Left sidebar navigation (pine background, ivory text, brass active indicator):
Home, Enterprise, Optimization, and disabled "coming soon" items: Simulation &
Twin, Risk & Valuation, Learning Lab, Course. Top bar with "AXIOM" wordmark
and phase badge "Phase 0 · Educational Edition".

PAGE 1 — HOME
Hero: "AXIOM — Enterprise Optimization, Certified." Sub-line: "Every result
ships with its certificates and checkpoints." Three stat cards fetched live:
enterprise count (GET /api/v1/enterprises → length), optimization runs (GET
/api/v1/reo/runs → length), available problems (GET /api/v1/reo/problems →
length). A health chip in the corner calling GET /health.

PAGE 2 — ENTERPRISE
Left: list of enterprises (GET /api/v1/enterprises) with name, sector, created
date; a "New enterprise" form (name, sector) posting to POST /api/v1/enterprises
(JSON {"name","sector"}). Clicking an enterprise loads GET /api/v1/enterprises/{id}
into a right panel: its details plus state snapshots (payload JSON, note,
timestamp, newest first). A "Record state" form with a JSON textarea (validate
it parses) and a note field, posting to POST /api/v1/enterprises/{id}/state as
{"payload": <parsed JSON>, "note": "..."}.

PAGE 3 — OPTIMIZATION (the flagship)
Top: problem picker populated from GET /api/v1/reo/problems — render each as a
selectable card showing title, course_ref, description. When selected, render
a params form pre-filled from default_params (numbers as number inputs; the
2x2 matrix H and vector c as small grids; unknown shapes as a JSON textarea).
Optional dropdown to attach an enterprise_id from GET /api/v1/enterprises.
"Solve" posts to POST /api/v1/reo/solve as {"problem", "params", "enterprise_id"}.
Render the response's result object in three blocks:
  - SOLUTION: key/value grid of result.solution plus result.value prominently.
  - CERTIFICATES: table of result.certificates rows {name, value, expected,
    pass} — pass true renders a moss check, false a red cross.
  - CHECKPOINTS: same table for result.checkpoints, with a banner "All
    checkpoints pass — certified against the DCT course laboratories" when
    result.all_checkpoints_pass is true; hide the block when checkpoints is empty.
Below: "Run history" table from GET /api/v1/reo/runs (problem, value from
result.value, all_checkpoints_pass badge, timestamp), newest first,
refreshing after each solve.

STATES: every fetch needs a loading skeleton and a readable error card with
the failing URL. Empty states get one-line invitations, not blank space.
