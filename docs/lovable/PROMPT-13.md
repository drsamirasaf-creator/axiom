# Lovable Prompt 13 — Phase 10: landing, explainers, frontier, re-forecast, contact

Paste everything below the line into Lovable against the `axiom-web` project.

---

The backend has shipped the v1.0 completion. Four changes. Standing rules
hold (bearer auth on protected pages, no math or invented copy in the
frontend, tooltips, honest empty states). ALL text in this prompt's
features comes from two new public endpoints — fetch once and cache:
`GET /api/v1/platform/about` and `GET /api/v1/platform/pages`. Do not
paraphrase or rewrite the copy; render it verbatim.

## 1. Landing page (make `/` a proper front door)

- Hero: the product name and `tagline` from /about, one primary CTA
  ("Explore the platform" → Dashboard) and one secondary ("For
  organizations" → opens modal 1).
- **Two feature modals** ("fancy pop-ups": full-screen-dimmed dialogs
  with a card design matching the app's navy/teal, smooth open/close,
  ESC/outside-click to dismiss, accessible focus trap):
  - **Modal 1 — For Organizations**: from `for_organizations`: the
    `definition` as lead paragraph, the five `benefits` as icon cards
    (title + text), and the `uniqueness` paragraph as a highlighted
    closing block. Trigger: a prominent "What is AXIOM?" button in the
    hero AND a persistent ⓘ next to the AXIOM wordmark in the app header.
  - **Modal 2 — For Students & Readers of DCT**: from `for_dct`, same
    structure (definition + three benefit cards). Trigger: a "The DCT
    Companion" link in the hero and in the Course Workspace page header.
- **Intro video**: if `intro_video_url` is non-null, render a responsive
  YouTube embed between the hero and the modals' trigger sections, titled
  "AXIOM in 90 seconds". If null, render nothing (no placeholder box).
- **Contact section** (also see §4): the `contact` block as a distinct
  card near the footer.

## 2. "About this page" — on every workspace

From /pages (keys: dashboard, data_input, valuation, risk_analysis,
benchmarking, twin_monitoring, optimization, simulation, learning_lab,
course_workspace): at the top of each corresponding page, render a slim
dismissible info bar: the page `title` in bold, the `what` sentence, and
an expand chevron revealing `benefit` and `start` ("How to start: …").
Remember dismissal per page in localStorage, and add a small ⓘ button in
each page header that reopens it. This is the answer for a user who lands
on any page cold: one glance says what it is and why it matters.

## 3. Two new analytical panels

- **Valuation page — "Value-Risk Frontier" section**:
  `GET /api/v1/intelligence/frontier/{dataset_id}?risk_aversion=λ`
  (λ slider 0–1, default 0.5, debounced refetch). Scatter/line chart:
  x = `safety_tail_margin`, y = `value_mean_ev`, one point per `points`
  entry labeled by `de`; Pareto-efficient points solid, dominated points
  faded; the `recommended` point highlighted with a ring. Below: the
  `narrative` verbatim and the checkpoint badge. Tooltips: "Value-Risk
  Frontier", "Tail Solvency Margin", "Pareto Efficient" (glossary).
- **Twin Monitoring page — "Re-Forecast" panel**: on any dataset version
  with `syncs_completed >= 1` and remaining forecast years, a "Propose
  re-forecast" button → `POST /api/v1/twin/reforecast` `{dataset_id}`
  (persist false). Show the `drivers`, and the `comparison` as a
  committed-vs-proposed table (revenue and FCFF per year). An "Apply
  re-forecast" button re-POSTs with `persist: true`, then refreshes the
  lineage strip (the new plan appears as a child) and toasts the new
  dataset id. Tooltip: "Re-Forecast Proposal".

## 4. Contact Regent Financial

From the `contact` block of /about: render (a) the landing-page card and
(b) a compact footer line on EVERY page: "`heading` — `firm`,
`email`" with the email as a mailto link (samir@theregentfinancial.com).
On the Financial Core pages, the unauthenticated sign-in prompt should
also include one line: "Firms: contact `firm` at `email` to bring AXIOM
to your organization."
