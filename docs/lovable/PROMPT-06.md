# Lovable Prompt 06 — Course Workspace + deep links (the ecosystem closes)
(paste into the existing AXIOM Lovable project as a follow-up message)

Add the Course workspace and app-wide deep linking. Enable the "Course"
sidebar item (the last coming-soon item disappears). Keep every existing
rule: all data from API_BASE, header "X-AXIOM-Tenant: demo", zero calculation
logic, no mock data.

DEEP LINKS (app-wide, do this first)
1. On app load, if the URL has ?module=axiom-NN (any NN), navigate to the
   Course workspace with that module opened. The DCT course site sends
   students here with exactly these links.
2. Give each engine workspace a select param: /optimization?select=dp_switch,
   /simulation?select=twin_sync, /risk?select=dro_flip,
   /learning?select=q_learning — when present, pre-select that card and
   pre-fill its default params, scrolled into view, ready to run.

PAGE — COURSE
Header: "The DCT Course, instrumented." with stat chips from
GET /api/v1/education/summary: modules_total, modules_live,
experiences_total, and a link-out button "Open the course site" to the
summary's course_site URL.

Module grid: GET /api/v1/education/modules returns 32 records (two volumes x
16). Group by number into 16 cards labeled AXIOM-01..AXIOM-16; each card
shows both volume titles stacked (Vol I title in gray, Vol II title in ink),
the seeds, and a status chip per volume (live in moss, planned in gray
outline). Clicking a card opens the module detail.

Module detail (also the ?module= landing target): fetch
GET /api/v1/education/modules/{slug}. Two volume panels side by side (Vol I |
Vol II), each showing title, seed, status chip, and its EXPERIENCES as
prominent buttons: label text from experience.label, small workspace tag
from experience.workspace. Clicking an experience navigates to its workspace
using the kind->route map {reo: /optimization, simulation: /simulation,
risk: /risk, learning: /learning} with ?select={key}. Below the panels: two
external link buttons per volume from course_links: "Chapter page" and
"Labs & downloads" (open in new tab). Planned volumes show "Instrumentation
arrives in a later phase" in gray italic instead of buttons.

HOME PAGE FINALE
1. The phase badge must read from GET /health ("Phase {phase} · Educational
   Edition") if it does not already.
2. Add a closing section under the stat cards: "Part of the Dynamic Corporate
   Transformation ecosystem" with two link buttons: "Course site" (from the
   education summary's course_site) and "Course workspace" (internal, to
   /course).
