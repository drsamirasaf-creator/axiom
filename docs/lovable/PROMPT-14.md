# Lovable Prompt 14 (v2) — Phase 11: the zero-friction sandbox, the Education/Business split, and AXIOM Business payments

Paste everything below the line into Lovable against the `axiom-web` project.

---

The backend has shipped sandbox mode: anonymous visitors can READ
everything (a fully populated showcase company is served automatically),
and only WRITE actions require an account. Restructure the app
accordingly. Standing rules hold (no math or invented copy in the
frontend, tooltips, honest empty states).

## 1. Split the left navigation into two labeled sections

Restructure the sidebar into two clearly separated groups, each with a
section header and an ⓘ tooltip:

- **AXIOM Education** (tooltip from glossary key "Course Workspace" plus
  this line: "The computational laboratory of the Dynamic Corporate
  Transformation program — open to everyone, no account needed."):
  Enterprise Optimization (REO), Dynamics & Simulation, Risk Analysis,
  Learning Lab, Course Workspace. Move the "Valuation Analyses" section
  that currently hosts the GBM Valuation Fan (the
  `category === "valuation"` analyses from `/api/v1/risk/analyses`) into
  a subsection here — it is course content.
- **AXIOM Business** (tooltip: first sentence of the glossary "Sandbox"
  term): Dashboard, Data Input, Valuation, Benchmarking, Twin Monitoring.

Visual distinction between the sections (subtle divider + section
labels; Business may carry a small "PRO" badge). Everything in AXIOM
Education remains fully open — no account, no payment, ever. Everyone
(including students) can freely browse the AXIOM Business sandbox per
§2–4 below.

## 2. Remove the sign-in gates from the Business pages

Dashboard, Data Input, Valuation, Benchmarking, and Twin Monitoring must
render fully for anonymous visitors — remove the "sign in to view"
screens. Make all GET/compute calls WITHOUT an Authorization header when
no token is stored; the API returns showcase data automatically (the
seeded companies "Meridian Industries (showcase)" — including its 2026
actuals and re-forecast lineage — and "Halcyon Components (showcase)").
Do NOT send the X-Axiom-Tenant header anymore, signed in or not.

## 3. The sandbox banner

When unauthenticated (or authenticated without an active AXIOM Business
plan), show a slim persistent banner on the Business pages: the glossary
"Sandbox" text shortened to its first sentence, with an ⓘ for the full
text and a "Get AXIOM Business" button (opens the paywall flow of §6).
Signed-in subscribers see the "Private workspace — <email>" chip instead.

## 4. Write actions become the conversion moment (two-stage)

Every data-changing control on the Business pages — Create dataset,
Upload template, Upload document, Analyze with AI, Accept/Reject
suggestions, Submit actuals, Apply re-forecast, persist a forecast —
when clicked:

- **No session** → open the register/sign-in modal: "You're exploring
  the AXIOM sandbox. To work with your own company or client data,
  create an account and choose an AXIOM Business plan — everything you
  enter stays private to your account."
- **Signed in but no active plan** → open the subscription/paywall modal
  (§6).
- **Signed in with an active plan** → fire the request normally.
- Also treat the API's own 401-with-invitation (the `detail` mentions
  "sandbox") as the no-session case. After successful registration AND
  checkout, retry the user's original action.

Keep fully interactive for ALL visitors (no gate): valuation runs and
all assumption sliders, sensitivity, Monte Carlo, stress, the frontier,
benchmark comparisons (sector and custom peers), and "Propose
re-forecast" (preview only — "Apply" is gated). Anonymous
valuation/stress responses include `transient: true` — show a subtle
"not saved — sandbox" tag on the run instead of adding it to history.

## 5. Landing page and flow updates

- Primary hero CTA becomes "Explore the live sandbox" → Dashboard
  (instant, pre-populated).
- On first anonymous visit to the Dashboard, preselect the "Meridian
  Industries (showcase)" dataset so charts appear with zero clicks.
- After a user subscribes, their workspace starts empty BY DESIGN: a
  purposeful empty state on each Business page — "This is your private
  workspace. Start on Data Input →" — with a secondary link "revisit the
  sandbox example" that views the showcase read-only (drop the auth
  header for those reads, clearly labeled "Sandbox view").
- The "For Organizations" modal (Prompt 13) gains a closing CTA row:
  "Get AXIOM Business" and "Contact Regent Financial" (mailto from the
  /about contact block).

## 6. AXIOM Business subscriptions via Lovable's payment gateway

Implement subscription payments using Lovable's built-in payment/Stripe
integration for the **AXIOM Business** plan (the plan name, price, and
billing interval will be configured by the owner in the payment
settings — scaffold a single subscription product named "AXIOM Business"
as a placeholder the owner will replace):

- A **/pricing** page and a **paywall modal** (same content): what AXIOM
  Business includes (private workspace, your own companies and
  documents, saved valuations, twin monitoring, AI document analysis)
  versus the free tier (the full live sandbox + all of AXIOM Education).
  Pull benefit wording from the /about `for_organizations.benefits` — do
  not write new marketing copy.
- Checkout via the payment gateway; on success, record the subscription
  status in the app's session/user state and unlock the Business write
  actions per §4.
- A "Manage subscription" item in the signed-in user menu (billing
  portal if the gateway provides one).
- Graceful degradation: if payment is not yet activated by the owner,
  the paywall modal shows the plan description with a "Coming soon —
  contact Regent Financial at samir@theregentfinancial.com" line instead
  of a checkout button, and Business writes remain gated. Never fake a
  successful payment.
- IMPORTANT: subscription state currently gates the UI only; the backend
  will add server-side entitlement checks in a subsequent phase.
  Structure the code so the "has active plan" check is a single reusable
  function.
