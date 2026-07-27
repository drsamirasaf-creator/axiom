# AXIOM MASTER LEDGER — CORE

**Last updated: 27 Jul 2026.**

## CANONICALITY RULE (read first)

This ledger is now TWO files. The split is by open/closed, not by topic:

- **LEDGER-CORE (this file) is canonical for anything OPEN** — every live
  decision, locked-but-unbuilt design, active incident, queue item, standing
  rule, and open question. **Upload this file into every new conversation.**
- **LEDGER-ARCHIVE is canonical for anything CLOSED** — shipped-and-verified
  history, the closed seam-bug incident log, and the Department Dashboard build
  log. **Upload only when a specific question needs it.**

Nothing was rewritten, paraphrased, or summarised in this split. Both files carry
the original text verbatim. If a decision appears to be missing from CORE, it is
in ARCHIVE — check there before re-deciding it.

**Reason for the split (27 Jul):** the single ledger reached 135,000 characters
and was being uploaded whole into every window, costing roughly 3x on response
speed and producing failed sends. Section sizing at the time of the split:
§4q build log 30%, §4b–4o 22%, §4r–4v 21%, §1 shipped 9% — those four were 82%
of the file, and two of them were closed history.

**Standing rule, amended:** "nothing is parked in the advisor's memory — every
decision is written into the ledger" is UNCHANGED. What changed is only which
file it goes into. Open → CORE. Closed → ARCHIVE, moved there only once it is
genuinely shipped and verified.

---

## IMMEDIATE STATE

**CXO Override & Sign-off (#3) — Stage 1 BUILT (638bd3a model+read path, 5932c41
proof) and REVIEWED 27 Jul (PASS ON INTENT, NOT CERTIFIED). ⭐ STAGE 1b ITEMS 1–5
COMPLETE (7969f48 items 1/2/3/5 · 5708729 item 4 + rulings · c40269e production
constraint sweep). 455 passed, exit 0.**

**⭐ ITEM 6 — COMPLETE 27 Jul. STAGE 1b IS CLOSED (items 1-6).** Production
surface proof run against company 38, authorized as a named write lane. All five
surfaces carried value + attribution live; removal restored the resting state
exactly including the flipped variance verdict; crawler diff showed no new
failure; zero residue. **⭐ THE FinancialDataset-on-core.db.Base FIXTURE CAVEAT
IS CLOSED** — dataset 50 was created by the real upload endpoint on
core.db.Base and every read crossed the bind with no stub, so the proof
exercised the seam that produced the last eight bugs instead of standing beside
it. The release gate recorded at e1549b5 is SATISFIED; Stage 2 has no remaining
Stage 1b blocker. Report:
docs/reports/2026-07-27-item-6-production-surface-proof.md

**Historical note (superseded):** item 6 was previously DEFERRED and RE-GATED —
the production surface proof was outstanding and blocked on an admin token, and
it gated Stage 2 SHIPPING TO A CUSTOMER rather than Stage 2 being BUILT. The
distinction is deliberate: the schema is now certified behaviourally against
production (c40269e), which is what made building safe; what remains unproven is
the RENDERED behaviour of an override across live surfaces, which is what makes
*shipping* safe.

**⚠ WHAT THE DEFERRAL LEAVES OPEN — recorded so it is not lost with the item.**

1. **The `FinancialDataset`-on-`core.db.Base` fixture caveat is UNCLOSED.**
   Closing it was item 6's *other* purpose, separate from the surface proof. The
   Stage 1 travel proof stubs `_active_company_dataset` because
   `FinancialDataset` sits on a different engine bind and cannot be created
   through the accounts session. That accounts-world/legacy-identity seam
   produced the last eight bugs; a stub across it is exactly where a ninth would
   live. **No amount of unit testing closes this** — only a run against a real
   dataset row does.
2. **No production surface proof.** Proven so far: value+provenance as ONE
   OBJECT on the department card/drill-down, and a disclosure block reaching
   exports — both against a local database. NOT proven: that a rendered number
   on a live PDF or a live Ask AXIOM answer carries its marker.
3. **No before/after crawler diff.** Silent-empty is the primary failure mode and
   the sidebar-presence assertions are what catch it. The operator crawl ABORTED
   this session on its own sanity gate (expired `OPERATOR_TOKEN`) — the gate
   working correctly, refusing to report a silently-anonymous run as
   authenticated, but leaving no operator baseline.

**CONSEQUENCE: Stage 2 may be built. Stage 2 must not reach a customer until
item 6 completes.** Anyone picking this up must treat item 6 as a release gate,
not a backlog item.

**⭐ SIGN-OFF INVALIDATION LOCKED 27 Jul — see §4x §8 below. DESIGN ONLY, NOT
BUILT.** Trigger is DISPLAYED VALUES ONLY (too broad and executives click without
reviewing, which destroys the feature more quietly than a bug; too narrow and a
signed number changes silently). The dependency set is COMPUTED from the
resolver, never hand-maintained — a hand-kept list goes stale silently, the same
defect class as a declared-but-unbound constraint. The re-sign-off prompt SHOWS
THE DIFF, and is where the override retirement prompt fires. **No magnitude
threshold** — a threshold selects which silent changes are permitted, and it
selects the small ones.

**⭐ STAGE 2 GRANT MODEL LOCKED 27 Jul — see §4x §7 below. DESIGN ONLY, NOT
BUILT.** Admin grants and may never exercise; grants are rows with `revoked_at`
timestamps, never a role field; one person may hold multiple departments;
**revocation never touches history** (test-pinned: revoke, then assert prior
sign-offs and overrides are byte-identical); department change moves the grant
and the display renders the role AS IT WAS ("then CHRO"); and **no admin
sign-off ever** — vacancy resolves by interim grant to a real CXO, or by an
explicit vacancy state that renders differently from "unsigned".

**Stage 1b outcomes:** (1) partial unique index — defect confirmed empirically
first, fix verified by re-running the failing test. (2) index key now carries
`target_scope`+`department_id`, and `metric_ref` is whitelisted to
resolver-covered metrics at BOTH schema and write path. (3) **`enterprise` scope
REMOVED** — traced to a single resolver call site (`_serialize_kpis`); no
enterprise surface resolves, so the scope was representable-but-unresolved.
(4) **`private CXO information` REMOVED** — see §5(B). (5) route assertion now
runs against the app's real route table, with a companion test proving the
detector fires.

**⭐⭐ STANDING PRINCIPLE — ASSERT BEHAVIOUR AGAINST THE LIVE SYSTEM, NEVER
DECLARATION. (Generalised 27 Jul; this is the THIRD instance of one principle,
not a third unrelated lesson.)**

A test that checks a constraint is *declared* certifies the **model file**. Only
a test that attempts the forbidden operation and watches it **fail** certifies
the **database**. The gap between those two is where every defect in this session
lived: the constraint was declared, the test passed, and nothing was enforced.

The three instances are the same principle wearing different clothes:

| Instance | Declaration (insufficient) | Behaviour (sufficient) |
|---|---|---|
| Verification | hand-clicking a route | `scripts/auth-regression.py`, 92 routes, sidebar-presence asserted |
| Deploy truth | a pushed commit hash | the **served bundle hash** |
| Schema truth | a constraint declared on the model | an INSERT attempted and **refused by the database** |

Applies beyond schemas: wherever a guard is claimed, the test must attempt the
thing the guard forbids. `test_the_route_assertion_would_actually_catch_one`
exists for the same reason — a negative assertion that can never fail is not a
test.

**VERIFICATION SWEEP RUN 27 Jul, against PRODUCTION, behaviourally.** Every
NOT NULL on `ax_metric_overrides` was tested by attempting a direct INSERT that
omits it; every session-added guard was tested by attempting the operation it
forbids. All inside transactions, all rolled back, residue confirmed 0 rows.

- `override_value`, `computed_value_at_override`, `reason_category`,
  `author_user_id`, `author_label`, `created_at` — **all six genuinely bound**,
  none declaration-only. The Stage 1 report's claim survives scrutiny.
- A **control insert of a complete row was ACCEPTED**, which is what makes the
  six refusals evidence: they are the omission failing, not the probe being
  malformed. A sweep without a positive control proves nothing.
- `private_info` · `enterprise` scope · NULL `department_id` · pipe-less
  `metric_ref` · a second ACTIVE row on one `metric_ref` — **all refused**.
- Supersession still releases the slot (one superseded + one active accepted) —
  the index is correct, not merely strict.

**VERDICT: ALL GUARDS BIND IN PRODUCTION.** Nothing needed fixing before item 6.

**⭐ MEMBERSHIP-BLIND GATE CLASS — FIFTH OCCURRENCE (27 Jul). The ledger
declares this class "KILLED (4th and final occurrence)". It is not dead, and the
reason is that it was never properly characterised.**

**What the first four had in common:** a gate derived the user's rights from a
`memberships[]` row, so a platform super/staff account — which HAS no membership
row — was locked out of Proposals, Team, Data Input writes and CEI cycle
controls. The kill centralised admin escalation at both hook seams
(`useCompanyAccess`, `useAccessMode`) and eliminated local derivations. That fix
was correct **for the failure as characterised: rights derived from membership.**

**What makes the FIFTH different, and why the kill did not cover it.** This one
derives nothing from membership and touches no role at all. `CompanySelector`
asked `isDemo` — a predicate about **the content being viewed** — to answer
**"which companies may this user switch to"**. Those are different questions, and
because the active company was the showcase, the answer collapsed to
showcase-only and the session could never leave. **The gate was not
membership-blind; it was QUESTION-BLIND.** No role check was wrong; the wrong
question was asked.

**THE CORRECTED CHARACTERISATION, so a sixth is recognisable:** the class is not
"gates that read memberships". It is **"a gate answering a question its predicate
was not built for"** — membership-as-rights was one instance,
content-mode-as-selectability is another. The recognisable shape is a boolean
whose NAME describes one axis (is this demo CONTENT?) being used to decide a
different axis (what may this user REACH?).

**The test that finds the sixth:** for every gating boolean, ask what question
its name answers, then ask what question the call site is actually asking. If
they differ, it is this class — regardless of whether membership appears
anywhere. A gate that is correct for its own question can still be wrong at a
call site that needed a different one.

**Fix applied (B lane):** `isDemo` is UNCHANGED — it remains the right predicate
for content and every content gate behaves identically. `CompanySelector` now
gates its FETCH on `isAnonymous` (the demo-safety line: anonymous fires zero
authenticated calls, unchanged) and builds its LIST from the user's own
companies plus showcase entries they do not already own. Separating the two
questions is the fix; changing the predicate would have been the wrong repair,
because `isDemo` was never wrong about what it describes.

**⭐ COMPANY 38 IS THE STANDING VERIFICATION TENANT (authorized 27 Jul).** Not a
throwaway. `AXIOM Test Fixture Co`, id 38, carries persistent departments and KPI
data so the crawler can exercise owner-gated, department-scoped content rather
than only its gate.

**LICENCE GATE RESOLVED CLEAN — NOTHING WAS ACTIVATED, BECAUSE NOTHING NEEDED TO
BE.** Company 38 was ALREADY in `ax_company_access` for account 20. No seat was
consumed, no licence state mutated, and the account carrying Milliner was never
written to. (Had activation been required it would have been REFUSED anyway: the
seat gate is `used >= company_slots`, and the account stands at 2 activated
against 0 purchased — so forcing it would have meant either raising
`company_slots` or bypassing the gate with a direct INSERT, both of which touch
billing state on an account carrying a real customer. The stop-and-report gate
would have fired.)

**ISOLATION PROPERTIES — ASSERTED EVERY RUN, NEVER ASSUMED:** not Meridian · not
showcase-gated · unreachable anonymously (401) · no real respondent data · never
a customer. `VERIFY_COMPANY_ID = 38` is a fail-closed PIN: the authed crawl
ABORTS if the app resolves anything else. `DENY_COMPANY_IDS = {25}` is separate
and absolute — **the operator ALSO owns Milliner, a real customer**, and no
resolver change may ever redirect an automated crawl into customer data.
Activation is NOT standing write permission; Stage 2 write exercises remain a
named, user-authorized lane per the mint fence. Teardown is by exact id (the app
ARCHIVES rather than deletes).

**⭐ OWNERSHIP CORRECTION, AND A PATTERN WORTH MORE THAN THE CORRECTION.** The
operator DOES own Milliner (25) — and company 38. The earlier "owns no
companies" was a **probe-level operator-precedence bug** in my own parsing
expression, not an empty list. A later read then printed a **truncated** slice of
the same list and was again read as complete.

**FOUR MEASUREMENT ERRORS THIS SESSION, ALL IN THE VERIFICATION TOOLING
REPORTING ON ITSELF:** (1) the crawler's identity check matching `/me` as a
substring of `/api/v1/metrics/glossary` and passing a rejected credential;
(2) `enterprises` queried where accounts-world ids apply, concluding a company
did not exist; (3) an operator-precedence bug reporting zero owned companies;
(4) a truncated list read as exhaustive. Zero were product defects. **All four
were the instrument mis-measuring, and each was found only by testing the
instrument the way we test the product.**

**THE RULE THIS SETTLES: the instrument gets the same behavioural standard as
the thing it measures.** A guard is only proven by attempting what it forbids
and watching it refuse; a list is only complete if the read is proven
untruncated; an id only means something once its world is established. The
standing principle already says assert behaviour, never declaration — this
extends it explicitly to the tooling, which had been exempt in practice.

**⭐ NINTH OCCURRENCE — THE ACCOUNTS-WORLD / LEGACY-IDENTITY SEAM NOW CATCHES
DIAGNOSIS, NOT ONLY CODE (27 Jul).** The eight seam incidents are closed and in
ARCHIVE. **The seam is not.** It persists as a CLASS, and its ninth occurrence
was not a defect in the product — it was a defect in my *diagnosis of* the
product.

Investigating the drifting `/companies/48/logo` 404, I queried `enterprises` for
id 48, found nothing, and concluded the company did not exist. **`enterprises` is
the LEGACY-IDENTITY table; `/companies/{id}/*` takes ACCOUNTS-WORLD ids.**
Company 48 exists perfectly well — `/companies/48/departments` and
`/companies/48/reports/latest` both return 200. The 404 was only ever the
documented "this company has no logo" signal (`company-logo.ts`: *"Returns null
if none"*).

The standing rule — *"no code may join accounts-world ids against
legacy-identity ids; email is the only cross-world key"* — was written for code.
**It applies to investigation with equal force**, and a wrong diagnosis is more
dangerous than a wrong line of code because it gets written into a report and
believed. Extend the rule: **before concluding anything from an id lookup,
establish WHICH WORLD the id belongs to.**

**⭐ THE §8.2 DECAY PATH, OBSERVED INSIDE THE VERIFICATION TOOL (27 Jul).** §8.2
argues that a hand-maintained list of "things that invalidate" goes stale
silently — correct the day it is written, wrong after the next change, and
failing in a way nothing reports. That is not a hypothetical: **it had already
happened, in the crawler.**

The `/cei` alias asserted the needle `"Collaborative Assessment"` — a heading the
app has never rendered. The nav restructure folded Collaborative Assessment into
Stakeholder Engagement, **and the crawler's own `EXPECTED_SIDEBAR_LINKS` comment
documents that restructure**. So one hand-maintained list in the file recorded
the change that invalidated another hand-maintained list in the same file, and
the stale one failed on every run for weeks without anyone treating it as a
defect — it had become background noise, which is precisely the state in which a
real regression goes unnoticed.

Two things follow. First, §8.2's "derive it, never restate it" is confirmed by
observation rather than argument, and applies to verification assertions as much
as to invalidation sets. Second, **a permanently-failing assertion is itself a
defect**, because it trains readers to discount the tool.

**⭐ A SECOND INSTANCE OF THE SAME CLASS, found during 1b and worth recording.**
`ensure_override_schema` initially checked only for the partial index. When the
reason-category CheckConstraint landed one commit later the index was already
present, the rebuild was skipped, and the new constraint never reached the
database — declared in the model, enforcing nothing. Caught only because a test
inserted the forbidden value and watched it commit. **The migration guard now
names EVERY required index and check constraint and rebuilds if any is missing.**
Generalised rule: a schema-drift guard that checks for one artifact certifies
one artifact, not the schema.

**RULINGS CLOSED 27 Jul:** §4x recomputed-RAG-badge provenance (LOCKED, Stage 2
build condition, recorded not built) · §4x `private CXO information` (LOCKED,
removed entirely, built) · §4y CXO Dataroom READ access (LOCKED, granted,
departmentally scoped; write stays Admin-only; §4y scope, not buildable now).

**ONE OPEN ITEM REMAINS, non-blocking:** Dataroom naming (§4y).

**STANDING RULE: build reports arrive as FILE UPLOADS, never pastes**; a dropped
clause in a verification report is a verification failure, not a formatting
annoyance (one dropped clause inverted the meaning of report flag 4 and produced
a wrong reading on first pass). Reports now live in `docs/reports/`.

**⭐ STAGE 1b ITEM 1 — EMPIRICALLY CONFIRMED 27 Jul, not merely suspected.** The
review's reading was tested rather than accepted. Two consecutive INSERTs of
ACTIVE overrides (`superseded_at IS NULL`) on the same `metric_ref` both
committed; the resulting count of active rows on one metric was **2**. The
constraint `UniqueConstraint(company_id, metric_ref, superseded_at)` therefore
does NOT bind active rows, exactly as the review stated. Consequence is
load-bearing, not cosmetic: the resolver's `.first()` would pick arbitrarily
between two contradictory live assertions about the same board figure, and the
Stage 1 report's "exactly one active assertion" claim was **false as written**.

**SHARED DEFECT CLASS — the same mistake, one table later.** This is the
identical SQL-NULLs-are-distinct trap that `_kpi_scope_key` already documents and
defends against: that function uses a literal `0` sentinel for a null
`department_id` *precisely because* NULLs do not compare equal, so a NULL-bearing
key cannot enforce uniqueness. The rule was known, written down in this codebase,
and reintroduced in `ax_metric_overrides` anyway. Recording it as a class rather
than an incident: any future uniqueness constraint whose key includes a nullable
column is wrong by default and needs a partial index or `NULLS NOT DISTINCT`.

**DATAROOM (§4y) written into the ledger 27 Jul** — designed and agreed in an
earlier session, never written down, and consequently missed on review. The
ledger rule caught the gap; the writing-down step had failed.

**~~FOUR OPEN ITEMS AWAITING USER RULING~~ — THREE CLOSED 27 Jul, ONE REMAINS.**
(1) CXO read access on the Dataroom — **LOCKED: granted, departmentally scoped,
read-only.** (2) Dataroom naming vs the existing document repository — **STILL
OPEN**, non-blocking. (3) recomputed RAG badge inherits the provenance marker —
**LOCKED: yes**, Stage 2 build condition. (4) the `private CXO information`
reason category — **LOCKED: removed entirely** (the stronger of the two options,
not the advisor's conditional-NOT-NULL recommendation).

---

## MOVED TO LEDGER-ARCHIVE

- **§1. SHIPPED & VERIFIED (do not rebuild)** — full shipped inventory.
- **§4q item 1 — Department Dashboard (DONE + LIVE)** — the full build log,
  including the alias fix, the k-anonymity partition defect and its fix, the
  seeding/unseed narrative, and per-trajectory verification results.
- **§5. INCIDENT LOG (the seam-bug era — CLOSED 21 Jul)**.

The forward build order (§4q items 2–5) stayed in CORE, below.

---

**2. CORRECTIONS TO OLD HANDOFF (facts, not opinions)**

**✅ KPI VARIANCE DIRECTION --- FIXED AND SHIPPED (e496444, 27 Jul). The
durable fix specified here was built exactly as specified: a `direction`
column on KpiPlan, captured in the UPLOAD TEMPLATE (column I, template
7M-v7.5) so the KPI's owner STATES direction rather than the system
guessing it, and `_kpi_variance` honours it. The name-keyword heuristic
survives only as a labelled fallback for rows predating the column, and
prints `(inferred)` where it is used. FULL RECORD MOVED TO ARCHIVE ---
see ARCHIVE §2-FIXED. Retained here as a one-line pointer only because
the defect was product-wide and its absence from CORE should not read as
the item having been forgotten.**

-   **No dp_switch / value_iteration exists in repo** --- beam search
    built in 7c-2 instead. dp_optimize is welded to growth/leverage
    (used only for its policy-surface pattern).

-   **DRO is Total-Variation, not Wasserstein** (valuation.stress /
    \_tv_worst_case, certified). Wasserstein exists only as
    twin-divergence. All copy says \"distributionally robust\"
    generically. **/free-pilot copy edit queued**: replace
    \"Wasserstein-robust stress testing\" with \"worst-case stress
    testing across an ambiguity radius\".

-   **Known model limitation**: kernel does not link capex→growth, so
    capex/cost/WC atoms are accretive-by-construction at defaults
    (magnitudes bounded). Trajectory Room + Prescience Brief must NOT
    narrate capex cuts as free money --- carry caveat into 7j grounding.
    Kernel coupling = possible later phase.

-   CID semantics: handoff says company-level; user described it as
    per-report. **OPEN QUESTION to Claude Code: what does CID actually
    identify?** Resolve before Entity Model phase.

**3. FREE PILOT ARC (locked design)**

-   Sales motion: super admin creates pilot company (no slot burn) →
    uploads client data → invites exec participants → reports ready →
    invites CFO as read-only viewer → Zoom walkthrough → CFO registers +
    pays via Stripe → transfer consumes his slot → seller drops off
    completely (no viewer access).

-   Buyer sees the shared showcase sample (Meridian) --- removable via
    existing hide/restore (SampleCompanySection). No per-account seeding
    needed (recon-confirmed no-op).

-   Super-admin UI: \"Pilot Companies\" tab; lifecycle Created → Data
    Loaded → Assessment Live → Reports Ready → CFO Invited → Transferred
    \| Archived, date-stamped list. (Lovable script DRAFTED, in queue.)

-   Public page: /free-pilot --- six high-level tabs (Try Before You Buy
    / The Process / Key Benefits / Under the Hood \[4 sub-tabs:
    Analytical Core, Organizational Lens, AXIOM Prescience, Board-Grade
    Output\] / Why It\'s Safe to Try / Start Now), persistent CTA bar on
    every tab, 7-step brass stepper animating on tab activation, minimal
    vertical scrolling, hidden placeholder slots for customer quotes +
    Capterra + awards (content later), Calendly:
    <https://calendly.com/regent-intro/axiom-live-demo>. Feature list
    includes ALL Prescience features (building now, will land).

**4. ENTITY MODEL (locked concept, phase queued)**

Two-tier customer model: **EID = buying entity** (three segments: (1)
single corporate --- one EID, one CID; (2) HoldCo --- one EID, N OpCo
CIDs; (3) consulting firm --- one EID, up to \~50 client CIDs). **CID =
each company AXIOM is applied to.** Leave-and-rejoin ⇒ new CID. Phase
contents: (a) EID as first-class customer-facing identifier (format like
AX-E-0147) + display; (b) multi-seat checkout + volume pricing
(**PENDING USER DECISION: price points for segments 2/3**); (c)
generalized CID-between-EID transfer built on FP-1 machinery (pilot
transfer = special case); (d) consultant-mode polish. Backend already
account→slots→companies shaped; this formalizes it. Near-term: pricing
page gets a \"running multiple companies? talk to us\" line (one-liner
in a future Lovable script).

**4b. DCT ADVISORY (LOCKED)**

-   **Naming locked: DCT = Dynamic Corporate Transformation** (matches
    existing logo tagline; umbrella brand). Service = **\"DCT
    Advisory\"**. Story: software = engine, advisory = human interface,
    book = doctrine.

-   **SKU locked (revised): single offer --- 5-hour block \$8,500**
    (effective \$1,700/hr, founder-direct). Quarterly retainer DROPPED
    (calendar commitment unacceptable); quarterly rhythm emerges via
    block-per-cycle purchasing instead. Page copy drafted +
    user-revised; awaiting final user sign-off on remaining copy
    (name/photo/bio question open).

-   **Free Activation Session (90 min) bundled with every
    purchase/transfer** --- onboarding + advisory sampler + retainer
    conversion moment.

-   Hours tracking: offline log with client sign-off for v1; in-app
    hours ledger = Entity Model rider later.

-   Website: pilot flow UNCHANGED except one sentence added to Step 7
    tooltip (\"...every purchase includes a complimentary Activation
    Session with AXIOM\'s founder\"). Dedicated DCT Advisory page (main
    nav + pricing link, NOT from /free-pilot): benefits list, two SKUs,
    quarterly loop diagram (diagnose→decide→execute→measure, brass loop
    visual). Book gets hidden placeholder slot until published. (Lovable
    script to be drafted.)

-   Stripe: two simple SKUs --- no Entity Model dependency.

-   Counsel item: advisory engagement terms +
    strategic-vs-investment-advice disclaimer (same counsel visit as
    EULA).

-   **Ledger-recorded caveat: advisory revenue is deliberately
    non-scaling** (\~2,000 sellable hrs/yr ⇒ ceiling \~20--30 clients).
    Escape hatches: certified partners; productizing interpretation into
    Prescience Brief.

**4c. AXIOM PARTNER PROGRAM (LOCKED --- all four terms approved)**

**Tier 1 Referral Partner** --- \$500 joining fee, unique Stripe promo
code (customer gets 10% off, partner earns 10% of first-12-months
revenue per referred customer incl. referrals into founder-delivered
advisory; recurring attribution needs customer↔partner mapping stored at
first purchase = Entity Model rider). Ship at launch as store product.
**Tier 2 Certified Implementation Partner** --- \$4,500 certification
(book = curriculum), may deliver implementation + DCT Advisory; AXIOM
collects **25% license royalty** on partner-delivered advisory. DO NOT
build until: book exists + real customers + advisory demand exceeds
founder capacity. Website now: Tier 1 purchasable at launch; Tier 2
\"Certification --- opening 2027, waitlist\". Principle: partners extend
software reach immediately, touch advisory only post-certification; risk
is brand dilution, not cannibalization (founder ceiling \~30 clients).

**4d. PRICING TIERS & SEAT LIMITS (LOCKED)**

**Tiers (monthly subscription, both):** **AXIOM Business \$4,995/mo** ·
**AXIOM Prescience \$14,995/mo** · **Prescience Upgrade \$10,000/mo**
(Business + Upgrade = Prescience exactly --- no arbitrage). Three Stripe
products. **Gating:** Business includes ALL core product + **Ask AXIOM
only** from the Prescience layer (cheap taster, existing 200/day cap;
its cited answers upsell the gated engines). Prescience-only:
Multiverse, Resilience Field, Causal Map, Radar/Sentinel, Prescience
Brief. **Positioning rule:** price on value, never on compute cost in
customer-facing copy (true compute \~11s/company/night). /free-pilot
keeps \"nothing watered down\" --- pilot tastes the full engine; tier
choice happens at purchase (Zoom walkthrough = upsell moment). **Seat
limits (per company):** Business --- 10 full members / 50 assessment
participants PER CYCLE / 5 viewers. Prescience --- 25 / 150 per cycle /
15. Participants cap is per-cycle (resets), killing the 300k-invite
scenario; CEI is a leadership instrument by design. **Overage
(locked):** +full member \$100/mo · +viewer \$50/mo · +50 participants
\$495/cycle; beyond \~2x base caps -\> \"talk to us\" (HoldCo/consulting
conversation). **Model:** monthly subscription both tiers (locked ---
ongoing engines justify recurring; lapse -\> tier-flag revocation). OPEN
MECHANICAL Q for Entity Model phase: is current Stripe checkout
one-time? (determines migration). **Implementation home:** Entity Model
phase (now the Commercial Architecture phase: EID + multi-seat +
transfers + tiers + limits + subscriptions + partner attribution).
Nothing here blocks 7i/Wizard.

**4g. LATE-SESSION FEATURE LOCKS (designs locked; LAUNCH-LINE RULING
PENDING)**

**(1) 7L expanded -\> \"Business Planning & Forecasting\" tab.** Full
standard statements in template (IS/BS/CF/SCI, real line items) ---
RECON GATE: every new line needs a kernel-mapping decision (feeds-model
vs carried-for-reporting). Actual-vs-forecast gap + variance analysis
for all statement lines + KPIs --- BUILD ON THE TWIN: store each
generated forecast as a versioned snapshot; variance layer
(abs/%/favorable-unfavorable) over twin deltas. Standard KPI set
(profitability, liquidity, solvency, working capital, CCC) +
**self-defined KPIs = the long-pending structured KPI ingestion item,
now with its product surface**. Forecast Studio methods 4/5 surface MC
fan charts w/ confidence bands (P10/P50/P90) --- the anti-vanilla
differentiator; say so in copy.

**(2) Macro & Industry layer.** Template macro-outlook section
(GDP/inflation/rates) -\> forecast drivers + 7i shock machinery consumes
directly. Industry KPIs via the self-defined KPI system + industry
template library. **DATA TRUTH (locked): v1 industry benchmarks are
USER-ENTERED** (structured for licensed-feed drop-in later; cross-client
aggregate = long-term moat). Never promise data we don\'t hold.

**(3) Evidence-based SWOT.** SWOT = three cited strands: assessment
(shipped) + documents (7k) + **financial signals** (computed entries w/
metric+trend+threshold tags, RED worsening = weakness, GREEN improving =
strength; traceable-or-silent applied to numbers). Trend-based entries
ship with 7k/7L (no external data needed); industry-relative entries
GATED on (2) benchmarks --- honest \"no benchmark provided\" otherwise.

**(4) CXO Priorities Registry (sleeper hit; cheap --- reuses
participants/magic-links/RAG/initiatives patterns).** STANDING registry
(not cycle-bound): each CXO (CEO/CFO/CMO/CIO/CHRO/CSO\...) holds a
ranked top-5 w/ RAG + text status, scoped link writes ONLY their own
list, updatable anytime; cycles snapshot the registry for trend.
Aggregation = full organizational-priorities view (Key Initiatives
enhancement). **Alignment analytics (Prescience-tier magic): priorities
vs frontier/viability --- coverage gaps (\"nobody\'s top-5 touches the
nearest-breach\"), conflicts, priority-vs-initiative orphans --- a Brief
section.**

**LAUNCH-LINE RULING (RESOLVED): no line. Founder\'s standing decision
--- launch timing is satisfaction-driven, not market-driven;
self-funded, delay at will.** All 4g features are in scope; ship when
the founder deems it ready. Sequencing remains DEPENDENCY-driven only
(contamination -\> 7k -\> 7L -\> macro/industry & SWOT strands &
priorities registry -\> 7j finale); quality gates (recon,
traceable-or-silent, crawler-per-build, interaction regression
pre-launch) are the guarantee that \'ready\' is true whenever declared.
Advisor drops urgency framing permanently.

**4e. ACTIVE INCIDENT --- CROSS-COMPANY CONTAMINATION (OPEN, diagnosis
script FIRED to Claude Code)**

**DIAGNOSED --- BACKEND EXONERATED, FRONTEND CULPRIT (fix fired to
Lovable).** Stored Milliner PDF/PPTX are 100% Milliner (26x/46x name
hits, 0 Meridian bytes); initiatives API returns \[\]; report builder
has NO fallback (409s on missing data); 3.5MB size match was a red
herring (all board PDFs \~3.5MB --- chart weight). The Meridian content
was injected CLIENT-SIDE: initiatives page demo-fallback on empty +
report view serving showcase/cached PDF. Lovable fix (in flight): delete
initiatives fallback -\> honest empty; report surface company-scoped
endpoints only, per-company cache; audit all legacy /api/v1
member-surface calls (bearer + own dataset id; only sample-workspace
currentTenant() may send showcase); CLASS-KILL grep of every showcase
fallback in member mode, enumerate + delete. Backend fail-closed (item
4) DECLINED --- anon showcase default is demo-load-bearing; revisit on
recurrence. Stale-report note (Milliner reports from data v1, active v3)
-\> future regenerate-on-upload rider. ASIDE for user: clean Milliner
PDF shows \$30.59B equity vs 17,500 revenue --- probable UNITS MISMATCH
in wizard entry (thousands vs Actual); user to sanity-check.

**4f. ROADMAP RE-SEQUENCE + NEW PHASES (LOCKED this session)**

**Locked sequence:** (1) contamination fix -\> (2) **7k Document
Intelligence** -\> (3) **7L Flexible Horizon + Forecast Studio** -\> (4)
**7j Rooms + Brief (moved LAST deliberately** --- finale stands on
docs + forecasts + clean pipeline; Brief gains doc grounding). Lovable
parallel: wizard friction fixes -\> 7k/7L surfaces -\> rooms; commercial
script on bio+photo.

**7k --- DOCUMENT INTELLIGENCE (locked design).** The differentiator:
financials + documents + assessment -\> one strategic picture. Three
layers in order: (a) **Extraction** --- PDF/DOCX -\> clean text,
stored/chunked/tagged per document (the prerequisite 7h flagged); (b)
**Prescience injection** --- doc text enters Ask AXIOM grounding on the
**existing delimited-untrusted seam** (SECURITY: uploaded docs are
prompt-injection vectors; doc text = data, never instructions),
citations like \[doc.name.pN\]; (c) **Synthesis** --- AI pass (Sonnet,
cite-or-decline persona) proposes SWOT entries + recommended initiatives
from docs, each source-tagged, entering the EXISTING disposition
machinery (proposed, not auto-accepted; accepted -\> Initiatives as
today). SWOT populated from docs + assessment classifications;
recommendations from financial analysis + doc text + assessment.
**Standing rule: TRACEABLE OR SILENT --- every synthesized claim cites
doc+page; thin evidence -\> honest gaps, never filler.** Wizard step-4
copy updated to be TRUE when 7k ships (currently oversells: docs are
metadata-only --- 7h known limitation; interim copy softening = user
ruling pending, lean (a) soften now).

**7L --- FLEXIBLE HORIZON + FORECAST STUDIO (locked design).** Template:
5 historical + up to 10 forecast years (kernel horizon already
parametric; work = template regen + parser flex + audit for hardcoded
5s). Forecast Studio: after upload, if no forecast data (or even with
it), ask \"want AXIOM forecasts?\" -\> multi-select of 5 methods in
ascending sophistication: (1) Trend extrapolation (CAGR/drift), (2)
Driver-based (current auto_forecast), (3) Statistical time-series (exp
smoothing/Holt-Winters), (4) Stochastic simulation (existing MC as
forecast band), (5) AXIOM Ensemble (weighted blend, divergence flagged
--- disagreement is insight). Chart: one line per selected method +
client\'s own forecast line. **PRIMARY-FORECAST RULE (locked): user
marks ONE selection primary (default: own forecast if provided, else
Ensemble); valuation/viability/frontier run ONLY on primary; others =
comparison lines with one-click make-primary-\>regenerate.** Then Save
-\> Generate Report (PDF+PPT+live webapp). Assessment feedback -\>
radar/CEI populate -\> recommendations -\> accepted -\> Initiatives.

**FINAL-PASS UPGRADE (locked):** end-stage regression expands from
nav-level to **100% interaction-level**: every button, form, and action
SEQUENCE (wizard e2e, pilot lifecycle, transfer claim, report
gen/download/share, invites) scripted in Playwright as crawler
extension, all three modes, before launch. Rationale: crawler proves
routes render; wizard run proved rendering != working.

**Wizard friction --- ITEMIZED (fix script drafted, queued behind
contamination verification):** (1) logo upload not retained/displayed;
(2) resume restarts at step 1 despite saved profile (firstIncompleteStep
signal bug); (3) assessment invite landed recipient on dashboard instead
of assessment feedback page; (4) **INVITE DESIGN LOCKED: wizard step 5 =
two labeled kinds --- ASSESSORS (magic-link -\> assessment feedback
page, no full-report access, continuous re-access to update feedback as
items evolve, optional register-as-viewer) and VIEW-ONLY (scoped link
-\> dashboard)**; (4b) financials render \$B where \$M expected ---
units-mismatch investigation (display formatter vs statement_units vs
entry units; USER TO CONFIRM what units were typed; PATCH endpoint can
relabel); (5b) ABCD Company removal --- Archive exists via pilot status
override (point user there); hard-delete = declined-by-default
(over-broad-cleanup class), user may override. **MOBILE APP (roadmap,
post-arc):** native/PWA for assessors + viewers --- feedback anywhere,
any language; sequences after web mobile-responsive pass; assessor = the
mobile persona.

**4i. SURVEY DESIGNER + INITIATIVE EXECUTION SUITE (DESIGNS LOCKED)**

**Survey Designer (framework panel extension):** progressive disclosure
(13 categories -\> subcategories -\> items, not a wall); admin adds
CUSTOM categories/items with title+subtitle+definition; custom items
join the company\'s framework revision, flow into cycles like taxonomy
items; editable anytime (edits = new revision, closed cycles preserved).
Backend: custom-item CRUD on existing revision model. Slot: with
assessment/seeding work.

**7m --- INITIATIVE EXECUTION SUITE (new phase, after 7j, before
content-packing; pairs w/ CXO Priorities Registry):** each initiative =
a PROJECT. RACI: one ACCOUNTABLE (Initiative Leader --- name+email,
magic-link invite; builds on 7e\'s existing leader/lead machinery) +
multiple RESPONSIBLE team members (scoped update access). Leader creates
ACTION ITEMS (owner, due date, RAG) + milestones/timeline w/ KPR/KPA;
**GANTT auto-renders** from dates+milestones (frontend viz, no new
backend concept). **PROJECT MONITORING COCKPIT**: portfolio view ---
every initiative as project card (leader, team, RAG, %-complete, next
milestone, value impact), drillable, VIEWER-VISIBLE (the board view).
New Initiative card fixes: explain Target Date; Expected Impact =
monetary value impact (label must say so, currency justified); owner
email via the RACI assign flow.

**Open bugs from this run:** weights vanish on Save (evidence needed:
does PUT fire/succeed?); create-initiative failure (symptom needed: dead
button vs error).

**4j. CUSTOMER CHANGE REQUESTS (DESIGN LOCKED --- 26 Jul)**

Customer-facing change-request / feature-request system, trouble-ticket
shape, full lifecycle. ANY user (member/CXO/viewer) can submit; lands in
super-admin area for careful evaluation.

-   **Submission (rich detail required):** each request captures ---
    title; **why** (the motivation/goal); **what problem/issue**
    they\'re trying to solve or experiencing; **how they\'d like it
    developed** (their proposed solution, optional); category/area;
    priority-to-them; attachments optional. Adequate-detail requirement
    enforced (not a one-line box). On submit, the requester is
    **thanked** (acknowledgement message + confirmation the request was
    received).

-   **Unique ID:** every request gets a unique human-readable ID (e.g.
    CR-0001) for reference/tracking.

-   **Super-admin evaluation area:** all requests land in the
    super-admin console --- queue with filters (status, company,
    category, date). Super admin (founder) evaluates carefully.

-   **Disposition:** super admin sets status --- **Accepted / Deferred /
    Declined** --- with **reasons** (declines and defers must carry a
    reason; the requester sees it).

-   **Lifecycle statuses (trouble-ticket model):** Submitted → Under
    Review → Accepted (with possible timeline) \| Deferred (with reason)
    \| Declined (with reason) → (if accepted) In Development → Testing →
    Deployed → Closed. Each transition timestamped; full history
    retained.

-   **Requester notifications (best-practice):** requester is notified
    on --- receipt (thank-you), disposition
    (accepted/deferred/declined + reasons), status changes on accepted
    requests (incl. possible implementation timeline), and on
    **Deployed** (\"the feature you requested is now live\").
    Notifications in-app and/or email.

-   **Best practices:** unique IDs, audit trail of all transitions,
    reason-required on defer/decline, requester visibility into their
    own requests\' status, no silent drops (every request reaches a
    disposition), super-admin-only evaluation (customers can\'t see
    others\' requests or the internal queue). Optional later:
    upvoting/duplicate-linking, public roadmap of accepted items.

-   **Reuse:** disposition/status-transition machinery parallels the
    recommendation-disposition pattern; notifications reuse the
    invite/email infra; unique-ID + audit-trail parallels changeset
    provenance.

-   **Distinct from CXO Sign-off reason-routing:** that routes
    disagreements about *displayed numbers*
    (calc-error/data-error/definition) to their fix; this is a *general
    product change-request channel* (feature asks, improvements, issues)
    landing in the super-admin queue. They are complementary, not the
    same system.

-   **Build slot:** commercial/support phase (near Support Chatbot §4k).
    Backend: ax_change_requests (+ status history),
    submit/list/disposition endpoints, super-admin surface, notification
    hooks.

**4k. SUPPORT CHATBOT + TIER 2 HUMAN ESCALATION (DESIGN LOCKED --- 26
Jul)**

In-app support/help chatbot, DISTINCT from Ask AXIOM. Ask AXIOM answers
about the *company\'s own data* (grounded, cited); this answers **\"how
do I use AXIOM\"** --- product help, how-tos, troubleshooting --- and
escalates to a human when it can\'t resolve.

-   **AI-first, human-escalation:** the chatbot handles common
    support/how-to questions (grounded in AXIOM product
    documentation/help content, NOT customer financial data). When it
    can\'t resolve --- or the user asks for a human --- it **escalates
    to Tier 2 human support** (the Customer Success Manager, per §4b\'s
    premium-support hire).

-   **Escalation → creates a support ticket** routed to the human queue;
    user notified of escalation + expected response; conversation
    context handed to the human so the user doesn\'t repeat themselves.

-   **Scope boundary (important):** the support bot is grounded in
    *product/help* content only --- it must NOT answer about a
    company\'s financial data (that\'s Ask AXIOM\'s job) and must NOT
    fabricate. Cite-or-decline discipline applies: if it doesn\'t know,
    it escalates rather than guessing. Same prompt-injection posture as
    Ask AXIOM (help content = data, not instructions).

-   **Tier differentiation (ties to §4d):** priority support for
    Prescience tier (per §4b Customer Success coverage --- faster human
    escalation); Business tier standard.

-   **Best practices:** honest \"I\'ll get a human\" rather than
    looping; ticket has unique ID + status (parallels §4j
    change-requests); user sees their open support tickets; no
    dead-ends.

-   **Reuse:** ticket/status machinery shared with §4j change-requests;
    escalation notifications reuse email infra; the chatbot grounding
    pattern reuses Ask AXIOM\'s cite-or-decline architecture (different
    corpus --- help docs vs. company data).

-   **Build slot:** commercial/support phase, alongside §4j. Depends on:
    help/documentation content existing to ground the bot; the Customer
    Success Manager hire (§4b) for the human tier.

**4l. ADVANCED ANALYTICS + CXO TRUST ARC (DESIGNS LOCKED --- 26 Jul;
full-vision, honesty-gated)**

Three major design specs drafted this session, governed by the
**HONEST-ANALYTICS PRINCIPLE**: every advanced analytic clears four
gates or DECLINES --- (1) data-sufficiency (\"AXIOM cannot compute this
reliably given data insufficiency\" is CORRECT and allowed), (2)
uncertainty disclosure (never a bare point estimate), (3) method
transparency, (4) causal honesty (attribution vs. causal-evidence vs.
hypothesis; default hypothesis). \"Trustworthy-or-silent.\" The heavy
lifting is the honesty-engineering, not the math. Each technique
verified against real INSUFFICIENT data + a decline-correctly test.
Decision (user): build the FULL vision, ALL techniques --- advanced
analytics no other software offers, a PhD quant will be impressed ---
BUT every number honesty-gated.

-   **Performance Monitoring (full-vision spec):** the Corporate Control
    Tower / digital nervous system. Module identity: Dashboard=SEE,
    Business Planning=ANTICIPATE, Performance Monitoring=CONTROL. Leads
    with \"what requires your attention?\" not KPI cards. All techniques
    across 7 rigor-stages: Management Attention Score (context-weighted
    ranking --- the defining new engine), signal detection
    (CUSUM/EWMA/Bayesian change-point/SPC), causal engine (SCM/Bayesian
    nets/DiD/IV/causal-forests/Shapley), DEA/SFA performance frontier,
    NLP assessor intelligence + human-data divergence (LATENT RISK
    detection), value-realization (activity-completion vs.
    economic-value), intervention memory, risk-propagation map, the
    Performance Intelligence Map capstone. Reuses 7L variance / 7i
    viability / assessor data / OKR / valuation engines. Spec file:
    AXIOM_Performance_Monitoring_Full_Vision_Spec.md. Source: 1,128-para
    enhancement spec.

-   **Prescience AI (full-vision spec):** the \$14,995-tier forward
    engine, 5 tabs. Ask AXIOM (taster, SHIPPED backend --- see §1) ·
    Multiverse (Monte Carlo/scenario across thousands of futures) ·
    Resilience (stress/reverse-stress, builds on 7i) · Causal Map (the
    honesty crucible --- causal graphs/Bayesian nets/DiD/IV, EVERY edge
    labeled attribution/causal-evidence/hypothesis, default hypothesis)
    · Prescience Brief (synthesis). Uncertainty is the product, not a
    caveat --- forward outputs are distributions/probabilities, never
    bare points. \"Prescience declines more than any surface, and that
    is its integrity.\" Locked tabs show honest arriving/upgrade state,
    never blank. Spec file: AXIOM_Prescience_AI_Build_Spec.md.

-   **CXO Dashboard Control & Sign-off (spec):** makes numbers OWNED and
    defensible at the board table. Part A --- explainability drawer
    (how/from-what/as-of/confidence; blanks explain themselves, never
    bare \"---\"). Part B --- full immediate self-service CXO control
    (show/hide/add KPIs, adjust values, set RAG, sign off --- never
    hostage to an absent admin; display-fix seconds vs. data-fix days on
    decoupled clocks). **Immutable-computed-truth (non-negotiable):**
    computed value NEVER destroyed; override is an attributed layer
    shown beside it; visible \"adjusted by \[CXO\]\" authorship marker
    (tracked-changes model) so the CEO/board can tell computed from
    adjusted --- trust-building, not number-laundering. Reason-routing:
    calc-error→flag/fix-engine, definition→config change,
    wrong-data→Data Update Wizard/gate, private-info→genuine display
    override, other→flag (reason never mandatory). Re-sign-off on new
    data. Reuses approval-gate/disposition/Wizard machinery. Spec file:
    AXIOM_CXO_Signoff_Build_Spec.md.

**4m. DEPARTMENT NAVIGATION & DEPARTMENT PAGES (design locked --- 26
Jul; audited)**

Two requests, both audited against docs/department-scope-audit.md
(295-line canonical inventory, verified vs. code 26 Jul). Reality
differs from \"just add the dropdown / expand the page\" --- most
remaining gaps need BACKEND work.

**(1) \"By Department\" dropdown coverage.** 6 endpoints already accept
?department= (objectives, kpi-variance, initiatives, assessment
summary/sentiment/swot); 17 frontend pages carry scope config. Pure-UI
gap is nearly zero. Remaining gaps need BACKEND plumbing first:
Initiatives→Cockpit (/initiatives/cockpit takes no department),
Transformation Readiness (department=None hardcoded accounts.py:7935),
CEI Trend/ΔCEI/Slopegraph/Heat-Matrix (trend exposes only snapshot cei,
not sliced), Benchmarking (imports PageHeader line 22, never renders it
--- no scope zone at all; peer-comparison so department may not apply).

**(2) Department PAGE --- currently a DRAWER, not a page.** Clicking a
department card opens DepartmentMap (org-structure.tsx:625) --- a
drawer: no route, no URL, not deep-linkable/shareable, lost on reload,
renders a breadcrumb implying a page hierarchy that doesn\'t exist.
Shows \~1/3 of the target: header (name/head/participation/RAG/one-line
sentiment) + Objectives&KRs + KPIs + Initiatives. Backend returns only
{department, objectives, kpis, initiatives}. MISSING: Stakeholder roster
(only a participation COUNT, no who), full Stakeholder Sentiment (only a
one-number gloss --- the per-department CEI slice \[13-axis radar, L1
subscores, dispersion, abstention\] IS already computed + k-floored,
just not surfaced here), SWOT slice (endpoint supports ?department=),
KPI variance (endpoint supports it), seniority-gap, readiness.

**LOCKED PLAN:**

-   **Lane A (main): convert drawer → real routable Department Page**
    (URL, deep-linkable, breadcrumb becomes true), and ASSEMBLE the full
    view: OKRs/KRs/KPIs + Initiatives (exist) + Stakeholder roster (data
    exists, surface it) + full Stakeholder Sentiment (per-department CEI
    radar/subscores/dispersion --- already computed + k-floored) + SWOT
    slice + KPI variance (endpoints exist). Mostly FRONTEND ASSEMBLY of
    already-computed, already-k-floored data. Honest states for the 2
    genuinely-blocked items (per-department CEI trend, readiness) until
    their backend lands.

-   **Lane B: dropdown backend gaps + trap fix** --- add department
    filtering to Cockpit + CEI-trend surfaces (backend), fix
    Benchmarking missing-header, and FIX/FIREWALL the department_slice
    trap (below).

-   Feeds the Performance Monitoring \"whose attention?\" dimension
    (§4l).

**⚠ TRAP (recorded --- silent-wrong-data hazard):**
assessment/summary?department= does NOT filter --- it returns
department_filter/department_slice as EXTRA fields while top-level
cei/radar/l1_subscores/trend stay ENTERPRISE-WIDE. /cei was wired to
read department_slice so it\'s correct, BUT any NEW consumer passing
?department= and reading top-level fields silently gets ENTERPRISE
numbers labeled as department. Fix or firewall before adding consumers.

**4n. MULTI-LANGUAGE / i18n (decision --- 26 Jul: DEFER past V1.0)**

**Finding (audited, NOT a regression):** i18next+react-i18next is wired
but only 3 files subscribe (AppLayout, LanguageSelector, FxDisclaimer)
--- 49 t() calls, 44 keys, 4 namespaces (nav/header/fx/common). **The
app was NEVER translated site-wide** --- every page body is a hardcoded
English literal. History confirms en.json grew 40→44 keys, same
namespaces, last touched 19 Jul (before the 9-commit queue); the top-nav
change d88a2d8 was cleared (added 5 lines, no provider/nesting change).
So \"language switch stopped working\" = it never worked beyond
nav/header; likely felt broken because language choice ALSO doesn\'t
persist (no localStorage write, detector plugin never .use()\'d → every
reload resets to English).

**DECISION (user, 26 Jul):** DEFER full site-wide translation past V1.0,
and **REMOVE the language dropdown** until multi-language is fully
incorporated (a dropdown that appears to do nothing reads as broken ---
hiding the incomplete feature is more polished than exposing it). Keep
the i18n INFRASTRUCTURE intact (i18next, init, en/es/fr/de/zh resources,
existing t() calls) --- hide the switcher only. App defaults to English.

**Rationale for deferral:** full translation = extracting hundreds of
hardcoded strings across \~50 route files into keys + translating each
language + a PERMANENT tax (every new feature\'s strings need
translating into all languages). C-suite/board buyers largely operate in
English for financial matters; financial terminology
(equity/leverage/provision/DLOM/WACC) translates BADLY --- doing it
cheaply (machine translation) risks credibility on exactly the terms
that matter; doing it well is expensive. Better fewer-languages-well
than many-badly.

**When revisited:** (a) the genuine multi-language case is the
ASSESSOR/PARTICIPANT SURVEY FLOW (rank-and-file employees, global, may
not operate in English --- ledger already notes assessor mobile =
\"feedback anywhere, any language\"); scope THAT translation
separately + well, not the whole CXO app. (b) Also fix language-choice
PERSISTENCE (localStorage + detector plugin) when the switcher returns.

**4o. UNSTRUCTURED DATA INGESTION WIZARD (CAPTURED --- not yet specced,
26 Jul)**

**On the list, NOT yet designed** (recorded so it doesn\'t fall through;
needs a scoping conversation before it\'s locked). User flagged wanting
a \"Data Wizard for unstructured data ingestion.\" DISTINCT from what
exists: the Data Update Wizard (25d348f) reviews STRUCTURED template
uploads; 7k Document Intelligence extracts/cites/synthesizes from
documents. The gap this would fill: **ingest data the customer has
HOWEVER they have it (messy non-template spreadsheets, narrative docs
containing numbers) and have AXIOM MAP it into the template schema, user
confirms** --- removing the \"fill out the Excel template\" friction (a
known adoption barrier for CFOs). Ambitious: unstructured→structured
mapping = real AI-extraction-with-validation; MUST carry
traceable-or-silent discipline (every extracted number cited to its
source page/cell, user confirms, never fabricated --- same posture as
7k). OPEN: exact scope --- (a) guided wizard over existing 7k
extraction, vs (b) full unstructured→structured schema mapping. Needs a
design pass before build. Pairs naturally with §4l CXO override (both =
meet the customer where they are).

**4n-note. CXO OVERRIDE --- already captured at §4l (CXO Dashboard
Control & Sign-off, spec file AXIOM_CXO_Signoff_Build_Spec.md). On the
list, designed, ready to build.**


**4q. BUILD SEQUENCE (locked order --- 26 Jul)**

User-set sequential build order for the next arc (do these in order):


2.  **Advanced Analytics = Prescience engines** (§4l) --- Multiverse,
    Resilience, Causal Map, Prescience Brief (forward-looking;
    honesty-gated). ← NEXT.

3.  **CXO Override** (§4l --- CXO Dashboard Control & Sign-off).

4.  **Performance Monitoring** (§4l --- the Control Tower,
    present-tense; full-vision honesty-gated).

5.  **DEI** then **VOC** (§4r / §4s --- NEW items, definitions pending
    from user before spec).

Note: \"Advanced Analytics\" in the user\'s phrasing = the Prescience
forward engines specifically (distinct from Performance Monitoring,
which is the present-tense Control Tower). Both live under the §4l
honesty-gated umbrella.

**4r. DEI (NEW --- named 26 Jul, DEFINITION PENDING)**

User added to the build sequence (after Performance Monitoring). NOT yet
defined --- likely a Diversity/Equity/Inclusion assessment dimension or
metrics module fitting the assessment/CEI machinery (a DEI survey
dimension and/or DEI KPIs), but UNCONFIRMED. Get a one-line definition
from user before speccing. Recorded so it doesn\'t fall through.

**4s. VOC --- VOICE OF CUSTOMER (NEW --- named 26 Jul, DEFINITION
PENDING)**

User added to the build sequence (after DEI). NOT yet defined --- likely
external-customer feedback capture (fitting the external-stakeholder
assessment machinery; overlaps the §4p Innovation Hub external-input
side), but UNCONFIRMED. Get a one-line definition from user before
speccing. Recorded so it doesn\'t fall through.

**4t. POSITIONING SHIFT --- LEAD WITH STRATEGY EXECUTION, NOT MATH
(decision --- 26 Jul)**

**Decision:** retire \"see your organization as a living mathematical
object\" as the PRIMARY marketing punchline. It described what AXIOM
does for the BUILDER/quant, not what the BUYER wants --- and CEOs (the
economic buyer) are often not math-savvy and shy from a math-led
product. Since
surveys/OKR/org-structure/departments/engagement/innovation were added,
the real value is the MANAGEMENT challenges (strategy execution,
alignment, prioritization, engagement, innovation), with the
mathematical techniques now the ENGINE, not the headline.

**New structure --- DEMOTE, don\'t DELETE the math:**

-   **LEAD (the promise, CEO\'s own language):** strategy execution /
    alignment / prioritization / engagement / innovation --- the
    outcomes a CEO already wants. Verb-first, outcome-first.

-   **SUPPORT (the differentiator + reason-to-believe):** advanced
    analytics / data-science rigor --- demoted from HEADLINE to PROOF
    POINT. This is what makes the strategy-execution claim BELIEVABLE
    and different from crowded OKR/BI/consultancy competitors (which all
    claim strategy execution). Framing sharper than generic \"data
    science\" --- e.g. \"brings decision-grade rigor to the decisions
    leaders usually make on instinct.\"

-   **Net:** \"strategy execution you can actually trust because it\'s
    rigorous underneath\" --- outcome first, math second.

**Rationale:** math-lead (a) repels the non-quant CEO at the headline
(the check-signer), (b) undersells the management-platform breadth as a
mere analytics tool, (c) leads with the hardest-to-trust element
(invites \"is your math right / black box?\" skepticism) vs. strategy
execution which leads with a problem the CEO already knows they have.
Don\'t OVER-correct into pure soft-management-speak --- that loses the
differentiator and sounds like every other strategy tool. The rigor IS
the moat; it just moves from front door to engine room.

**Book vs. product (deliberate audience split):** DCT-the-BOOK stays
math-forward/rigorous = the DOCTRINE (for the reader who wants the
theory). AXIOM-the-PRODUCT leads with the OUTCOME (for the CEO who wants
the result), math as invisible engine. Same substance, different front
door per audience --- intentional segmentation, not inconsistency.

**PENDING:** exact new punchline wording (user to finalize --- capture
direction now, finalize words after sitting with options; this copy
deserves a beat). Directions floated: \"Turn strategy into execution\" ·
\"See whether your strategy is actually happening\" · \"Align your
organization. Execute your strategy. Know what matters.\" When finalized
→ propagate across landing/pricing/free-pilot/deck/About (a copy pass,
Lovable + artifacts).

**Concept:** a place where NEW IDEAS for projects/initiatives from ALL
internal AND external stakeholders come in, are viewed + acted upon by
top management, and accepted ideas can REWARD the (non-anonymous)
submitter. Turns the assessment machinery from diagnostic (\"what\'s
wrong\") into generative (\"what could we do\").

**Reuses existing pieces:** stakeholder collection
(assessment/magic-link participants), the Initiatives/Projects spine
(§7m), and the disposition→initiative pattern (same flow as 7k
document-synthesis proposals --- accepted proposal becomes an
Initiative; here the source is a human stakeholder instead of the AI).

### ⭐ SUBMISSION CATCHMENT — EXPLICIT ENUMERATION (user confirmation, 27 Jul). DESIGN ONLY, NOT BUILT.

The concept above says ideas come from "ALL internal AND external
stakeholders". That intent is now **enumerated so it cannot be narrowed at build
time**:

**EVERY USER OF THE APP MAY SUBMIT AN IDEA** — CEO, CXOs, admins, assessors, and
**view-only users** — plus external stakeholders per the existing concept
(customers/partners, subject to the light-moderation open question below).

**⭐ SUBMISSION IS NOT GATED ON ASSESSMENT PARTICIPATION.** This is the specific
risk being closed, and it is a build-time risk rather than a design
disagreement. §4p as written puts the submission side in Stakeholder Engagement,
which **is the assessment path** — so a reasonable builder could implement
"assessment participants can submit" and silently exclude a view-only board
member, an admin, or a CEO who never takes the survey. **Those are precisely the
people whose ideas matter most.**

**The questionnaire is ONE submission door, not the only one.** Idea submission
must also be reachable **from the app itself**, independent of any assessment
cycle, and **open when no cycle is running**.

**Rationale, recorded because the narrowing would be invisible:** the feature's
value is **catchment breadth**. A hub that only catches survey-takers is a
survey feature, not an innovation hub. And nothing would fail — no error, no
empty state, no one reporting a fault; the hub would simply receive fewer ideas
than it should, from a narrower set of people, forever. **Same shape as the
declared-but-unbound class recorded earlier today: the intent is stated, the
enforcement is absent.** The enumeration above is the enforcement.

### CARRY TO THE SHARED SPINE (§4j ↔ §4p)

The standing instruction — §4j and §4p overlap and must **share one
ticket/disposition/notification spine** rather than two parallel systems — means
**this role enumeration belongs to the spine, not to §4p alone**, and it must
match §4j's already-stated catchment (**any user — member / CXO / viewer**).

**Both entry points feed ONE spine with different content types and
destinations**, and **NEITHER MAY GATE SUBMISSION ON A ROLE THE OTHER ADMITS.**
Two submission surfaces with two different eligibility rules is the same
"two surfaces, one concept" bug class already flagged for Department Dashboard
and Dataroom naming — and here it would be worse, because the divergence is in
*who is allowed to speak* rather than in what a thing is called.

**UNCHANGED — the anonymity rule stands exactly as recorded below:** assessment
is anonymous with a k-floor; ideas are **attributed by default** because reward
needs to know who; anonymous submission is **permitted but cannot be rewarded**;
and the separation must be **explicit and clearly marked** wherever both appear
on one surface. The catchment enumeration widens WHO may submit; it does not
touch HOW submissions are attributed.

**Design shape (locked concept):**

-   **Two-sided:** SUBMISSION side lives in Stakeholder Engagement (+
    optionally a questionnaire section --- see anonymity rule) **AND, per the
    catchment ruling above, in an app-native entry point that does not depend on
    an assessment cycle**;
    REVIEW/ACT side is a management queue near Initiatives (view /
    accept→convert-to-Initiative attributed / defer /
    decline-with-reason / recognize-reward). Whether 1 tab or 2 surfaces
    = UX call.

-   **⚠ ANONYMITY RULE (critical):** assessment/CEI is ANONYMOUS
    (k-floor, load-bearing for honest feedback); Innovation Hub ideas
    are ATTRIBUTED (reward needs to know who). These are OPPOSITE
    requirements in the same questionnaire. So idea-submission MUST be
    explicitly separated + clearly marked: \"assessment is anonymous,
    but submit an idea you can be credited for here (optional).\"
    Attributed-by-default; anonymous submission allowed BUT can\'t be
    rewarded.

-   **Reward (keep light v1):** attribution + a \"recognized/rewarded\"
    status flag management sets; actual reward handled OFFLINE. Do NOT
    build a rewards-payment system in v1.

-   **Lifecycle (best-practice, parallels §4j):** submit → thank-you →
    management review/disposition → submitter notified on accept/reward;
    accepted → becomes an Initiative crediting the submitter.

**OPEN QUESTIONS before spec:** (1) do external submitters
(customers/partners) get the same reward path + need light moderation?
(2) one tab or two surfaces? (3) shared machinery with §4j Change
Requests? --- **NOTE: §4j (Customer Change Requests) and §4p (Innovation
Hub) OVERLAP significantly** --- both are
submit→management-queue→disposition→notify→accepted-becomes-work.
Difference = what\'s submitted (product change-request vs.
project/initiative idea) + the reward angle. Likely SHARE the
ticket/disposition/notification spine with different content types +
destinations. Do NOT build two parallel systems --- design the shared
spine once.

**MEMBERSHIP-BLIND GATE CLASS --- KILLED (4th and final occurrence):**
operator (platform super, no memberships\[\] row) was invisibly locked
out of Proposals tab, Team, Data Input writes, CEI cycle controls ---
local membership?.role derivations bypassed the fixed hook. Fix: admin
escalation for platform staff/super centralized at BOTH hook seams
(useCompanyAccess, useAccessMode); local derivations eliminated
(initiatives.tsx, team.tsx); Proposals tab now renders on companyId for
any signed-in viewer (honest empty/error states). Standing rule
reinforced: role gates derive ONLY from the central hooks, never
locally. (\"Not Adopted\" tab = Register\'s D-band, unrelated to
proposals --- clarified.) **Pass #2 verdicts (Lovable,
evidence-first):** framework panel FIXED (inline descriptions,
normalize-to-100, honest not-initialized notice, Save/Saved states) ---
the can\'t-click mystery = SEAM IN FRONTEND FORM: useCompanyAccess
derives canWrite from membership only, blind to platform_role; global
fix fired (canWrite = admin/owner OR super/staff). Logo \"persistence\"
bug EXONERATED --- enterprise.tsx never rendered a logo element at all
(mount being added). Documents surfaces confirmed split (two fetch
paths; reconciliation in flight). Readiness = CONFIRMED backend gap
(frontend rightly refused sessionStorage fakery) -\> post-7L item 3 now
definite. Invite roster = likely backend gap -\> ADDENDUM item 5 to
post-7L batch (GET /companies/{id}/invites + revoke/resend). Session
frontend COMPLETE (localStorage + silent re-auth + cross-tab); friction
is purely backend TTL -\> post-7L item 2. Save-button full sweep =
dedicated Lovable pass, queued after 7L surfaces. Valuation-tab verdict
AWAITING USER\'S network trace (hypothesis: honest refusal on
mixed-scale v3 data). Expected-behavior (UX must self-explain): CEI
empty until a cycle opens/closes; Initiatives/SWOT empty until adoptions
(12 proposals STILL awaiting user review --- also the data-alive
diagnostic for the documents bug). Real bugs -\> Lovable pass #2:
framework panel interactions dead + no item descriptions;
Additional-Documents surface shows empty (two doc surfaces, one unwired
--- if proposals still cite, data is alive); logo persistence THIRD
occurrence (root-cause to one source of truth); Valuation tab not
populating (evidence first); readiness scores not persisted (diagnose
which side). **NEW STANDING RULES: every input surface has explicit
Save + saved/unsaved feedback; new companies are BORN with the full
13/78/361 framework selected and weights=100 (curation is the
exception)** --- seeding = Claude Code item post-7L (+ Milliner
backfill). New features specced: 30-day remember-me session (TTL/refresh
backend + frontend persistence); admin invite roster (assessors +
viewers, status, resend/revoke). Claude Code post-7L queue: framework
seeding+backfill, session TTL/refresh, readiness endpoint if missing,
doc-list curl confirm.

**4u. TRUST & ASSURANCE --- \"how do I know your numbers are correct?\"
(locked 26 Jul)**

The likely CFO-buyer question. KEY INSIGHT: no financial model is
\"certified correct\" (valuation = judgments about the future; even SOC
2 Processing Integrity certifies the system PROCESSES correctly, NOT
that inputs/answers are true). Don\'t overclaim --- the HONEST answer is
stronger and disarming. FOUR-LAYER DEFENSE:

-   **Layer 1 --- GLASS-BOX / auditability (our strongest, ALREADY
    BUILT):** every number traces to inputs + method; drill-downs,
    citations, WACC/DCF/DLOM shown, direction assumption
    printed+correctable, \"AXIOM cannot compute this reliably\" instead
    of fabricating. This IS the §4l honesty-analytics principle + CXO
    override (immutable computed truth + attributed \"adjusted by
    \[CXO\]\"). Pitch: \"you\'re not trusting a black box, you\'re
    auditing our work like you\'d audit an analyst.\" For a CFO,
    AUDITABLE \> CERTIFIED (auditable is what they defend to THEIR
    board).

-   **Layer 2 --- methodology conformance (do NOW, no cost):** document
    which recognized standards the methods follow --- IVS (International
    Valuation Standards) + AICPA valuation guidance (valuation);
    Damodaran / McKinsey Valuation canon (DCF/WACC/multiples); GAAP/IFRS
    (statements). Produce a \"How AXIOM Computes Its Numbers\"
    METHODOLOGY WHITE PAPER (sales/trust asset; lets a CFO\'s team
    verify conformance themselves). No certification needed to CONFORM
    --- just document it.

-   **Layer 3 --- independent methodology ATTESTATION (later,
    deal-driven):** engage a valuation specialist / Big Four to review
    models + issue \"\[Firm\] reviewed AXIOM\'s methodology, conforms to
    IVS/AICPA.\" The credible version of \"certified\" (= independently
    reviewed for soundness, NOT \"certified correct\").
    Board-presentable. Not a pre-launch blocker; the artifact to point
    at when a big deal hinges on it.

-   **Layer 4 --- SOC 2 Type II + Processing Integrity (table-stakes,
    fund pre-launch/early-commercial):** \~65% of buyers demand
    compliance proof; procurement baseline. Include the PROCESSING
    INTEGRITY criterion (rare --- mostly fintech --- so it\'s a
    DIFFERENTIATOR signalling output-reliability; cost: formalize
    validation logic, processing SLAs, reconciliation evidence, make
    manual reviews visible --- exactly the work a trustworthy-financials
    platform WANTS done). CFO will want Type II (operating effectiveness
    over time), not Type I.

**The honest CFO answer (script):** \"No financial model --- ours, your
team\'s, or a Big Four\'s --- is \'certified correct,\' because
valuation is judgments about the future. What we guarantee: every AXIOM
number is fully traceable to its inputs + methodology, our methods
conform to \[IVS/AICPA/corp-finance canon\], and where the data doesn\'t
support a reliable answer AXIOM tells you rather than guessing. You
audit every calculation, adjust any assumption, sign off with your
adjustments attributed and the computed baseline always visible. SOC 2
Type II incl. Processing Integrity \[when true\].\" Conceding the limit
honestly + reframing to auditability/control/honest-silence beats any
logo --- a CFO has never heard a vendor say \"no model is certifiably
correct, including ours.\"

TODO: (1) methodology white paper (now, no cost); (2) SOC 2 Type II +
Processing Integrity (funded pre-launch item → add to §7 launch gates);
(3) independent methodology attestation (later, deal-driven). The
product architecture (§4l honesty-gating + CXO override + traceable
drill-downs) IS the correctness answer --- already being built.

**4x. CXO OVERRIDE & SIGN-OFF (#3 --- scoped 26 Jul, design pending user
decisions)**

Scoping pass done (read-only). Spec AXIOM_CXO_Signoff_Build_Spec.md
describes override at the ENTERPRISE dashboard; user wants it at the
DEPARTMENT Dashboard. KEY ARCHITECTURAL CALL (affirmed): ONE override
model scoped BY TARGET (enterprise metric OR department metric), NOT two
systems --- a second dept-specific override mechanism would
drift/diverge from the enterprise one = the \"two surfaces one concept\"
bug class deliberately seeded. IMMUTABLE-TRUTH MODEL (the property the
feature rests on): computed value stored + NEVER overwritten; override =
separate overlay row keyed to metric+author+timestamp+reason; both
always retrievable; override CANNOT exist without
author+timestamp+reason (NOT NULL, schema-enforced --- an unattributed
override IS number-laundering). AUTHORSHIP TRAVELS TO EVERY SURFACE
incl. PDF export + Ask AXIOM (an overridden number appearing BARE on any
one surface is THE leak --- the number + its \"adjusted by \[CXO\]\"
provenance travel as ONE object, not value + droppable decoration).
AUTHORITY server-side enforced (dept CXO overrides own dept only ---
CHRO→HR, CTO→IT; a CFO must NOT silently adjust HR; UI-only enforcement
is bypassable, board-facing needs write-path enforcement). RE-SIGN-OFF:
new data invalidates a prior sign-off (a \"signed off\" number that
silently changed = trap). Full immutable exportable audit trail
(who/what/old-computed/new/reason/when) = board-defensibility backbone.
PENDING USER DECISIONS: (1) one model scoped by target \[rec yes\]; (2)
staged build riskiest-first --- immutable-truth schema +
authorship-travel PROVEN before the write UI \[rec yes\]; (3) first
stage = data model + read path (show computed-vs-adjusted w/ attribution
everywhere) WITHOUT write UI, prove provenance-travel on a test override
before anyone can create one \[rec yes\]; (4) authorship must reach Ask
AXIOM (override a KPI → Ask AXIOM says \"adjusted by \[CXO\]\" not the
computed value as fact) --- design in, don\'t bolt on. WHY DESIGN-FIRST
HARD: every other feature\'s bug = wrong display; here a bug = a board
sees a quietly-altered number without knowing = trust/liability failure.
\*\*USER AFFIRMED ALL (26 Jul) + added the DEFAULT-NO-CHANGE PRINCIPLE:
the CXO changes NOTHING by default --- computed truth STANDS unless a
CXO has a specific reasoned cause to adjust ONE number. Override is the
EXCEPTION not the workflow; the resting state is \"computed numbers,
untouched.\" UI: computed value is the quiet default, override a
deliberate visible act (NOT an editable field inviting fiddling --- the
dashboard is not a spreadsheet). Most numbers most of the time carry NO
override, so \"adjusted by \[CXO\]\" appears RARELY --- which is exactly
what makes it MEANINGFUL when it does (common overrides = noise; rare =
signal). This IS what makes the §4u correctness story credible: computed
numbers stand by default (nobody massaging them), rare adjustments are
attributed exceptions with the original computed value beside them. A
tool where execs routinely overwrite = untrustable; default-no-change +
attributed-rare-exception = trustable. CONFIRMED: authorship reaches Ask
AXIOM (Ask AXIOM keeps a record of any CXO changes; an overridden KPI →
Ask AXIOM reports \"adjusted by \[CXO\]\" + the record, never the
computed value as bare fact). All decisions (1)-(4) APPROVED --- proceed
to staged build, first stage = immutable data model + read path (prove
provenance-travel incl. export + Ask AXIOM) BEFORE any write UI.
\*\*SIGN-OFF IS THE CXO\'s PRIMARY ACTION (user 26 Jul): given
default-no-change, the CXO\'s normal workflow is REVIEW → SIGN OFF (one
button: \"I\'ve reviewed these and attest they\'re correct\"), NOT
editing. Override is the rare exception; sign-off is the everyday act. A
\"Sign off\" button on the Department Dashboard → shows \"Signed off by
\[CXO\], \[date\]\" visible to CEO/board = a named executive personally
attesting to the numbers (board-grade governance artifact --- the CEO
sees which depts\' CXOs have stood behind their numbers). Re-sign-off on
data change (locked): data changes after sign-off → sign-off
INVALIDATED, dashboard shows \"awaiting re-sign-off\" (an exec attested
to the OLD numbers; stale \"signed off\" on changed numbers = the trap).
If the CXO has overrides, sign-off attests to the dashboard AS SHOWN
(computed + his attributed adjustments). This is Stage 2 (interaction
layer) but the interaction is locked now. **USER APPROVED ALL (26 Jul):
(1) one model scoped by target ✓; (2) staged riskiest-first ✓; (3) first
stage = data model + read path with attribution-everywhere, NO write UI
yet, prove provenance-travel on a test override first ✓; (4) Ask AXIOM
keeps a record of / surfaces any CXO change (never cites the computed
value as fact once overridden) ✓. ⭐ GOVERNING DEFAULT (user, emphatic
26 Jul): A CXO CHANGES NOTHING BY DEFAULT. The computed value is the
default authority --- it stands exactly as computed unless a CXO
EXPLICITLY, deliberately overrides with a reason. No override exists
unless actively created; its absence = \'computed number stands,
unmodified\'. Most numbers carry NO \'adjusted by\' label → the label is
SIGNAL not noise, conspicuous precisely because everything else is
untouched computed truth. The friction (mandatory reason + attribution +
audit + board-visible label) is a FEATURE --- an easy override is an
over-used override, eroding the trust the feature protects. Untouched
dashboard = HEALTHY; many overrides = a pressure-gauge that
data/definitions are wrong, not a normal workflow. System NEVER
auto-overrides / pre-fills / suggests a value into place. FLAGSHIP:
Meridian carries FEW/ZERO overrides (demonstrate the capability on \~ONE
example, never a dashboard littered with adjustments --- an
over-overridden flagship signals \'their numbers always need fixing\').
Reinforces §4u: \'every number is exactly what AXIOM computed,
untouched, unless a human deliberately + visibly says otherwise.\'**



### §4x — STAGE 1 VERIFICATION RECORD (27 Jul 2026)


## LEDGER HEADER — REPLACEMENT STATE LINE

**IMMEDIATE STATE: CXO Override & Sign-off (#3) — Stage 1 (immutable data model +
read path) BUILT (638bd3a model+read path, 5932c41 proof; 441 passed, exit 0;
backend deployed) and REVIEWED 27 Jul. Verdict: PASS ON INTENT, NOT CERTIFIED.
Stage 2 (write UI + sign-off button) REMAINS BLOCKED pending Stage 1b (6 items,
below) and 2 open rulings. Stage 1 report read clean on second attempt (first
paste corrupted again — file upload, never paste).**

---

## 1. WHAT STAGE 1 ACTUALLY PROVED (scope corrected)

Schema `ax_metric_overrides`:
- Target: `company_id` · `target_scope` (enterprise|department) · `department_id`
  (nullable) · `metric_ref` · `metric_label`
- Assertion: `override_value` · `computed_value_at_override` · `reason_category` ·
  `reason_note`
- Authorship: `author_user_id` · `author_label` · `created_at`
- Supersession: `superseded_at` · `superseded_by_id` · `supersession_kind`

NOT NULL, schema-enforced (not code-enforced): `override_value`,
`computed_value_at_override`, `reason_category`, `author_user_id`,
`author_label`, `created_at`. A direct INSERT cannot produce an unattributed
override. `reason_note` nullable per spec B.5 — CONTESTED, see open ruling.

**Three design calls, all correct, all locked:**
- **No UPDATE path.** A change is a new row. Editing in place would destroy the
  audit trail of the override itself.
- **`computed_value_at_override` is a snapshot, not a mirror.** Datasets are
  re-uploaded quarterly; what AXIOM said at the moment of the decision cannot be
  re-derived later.
- **`author_label` is frozen text, never a join.** A board reading a two-year-old
  figure needs the title as it was then, not as the org chart is now.

**Resolver:** value and provenance return as one unit. No attribute yields a
stripped figure (`.display` / `.attribution` / `.to_dict()` / `.sentence()` for
prose surfaces). `resolve_many()` is one query per page — a resolver expensive
enough to skip on hot paths is a resolver that gets skipped.

**Structural single-seam achieved:** `_serialize_kpis` is now the only place a
department KPI becomes JSON (`/kpi-variance` and `okr-map` built it inline before
— two escape routes for a bare figure). Export disclosure attaches to
`_report_extras`, feeding all three formats, printed BEFORE the legal section.

**⚠ SCOPE CORRECTION — what the 7/7 proof does and does not establish.**
`kpi_strip` financial KPIs reach reports/PDF/Ask AXIOM; department KPIs do NOT.
The overridden metric is a department KPI. Therefore what travels to PDF and Ask
AXIOM is the `_report_extras` DISCLOSURE SECTION, not a rendered number carrying
its marker. Proven: (a) value+provenance as ONE OBJECT on the department
dashboard card/drill-down; (b) a disclosure block reaching exports. NOT proven:
that a rendered number on PDF or Ask AXIOM carries its marker — no rendered
number existed on those surfaces to test. This is an honest and useful result,
but it is NOT the full ledger property ("the number + its provenance travel as
ONE object"). Consequence: the `metric_ref` whitelist (Stage 1b item 2) is
LOAD-BEARING, not precautionary — the first override targeting a `kpi_strip`
metric produces a bare adjusted figure in a board PDF.

**Also proven:** `KpiPlan` re-read after override still holds computed 19.4
(never written over). Removal restores resting state exactly, including the
variance verdict flipping back. Supersession: both rows survive, exactly one
active, superseded row keeps its own value and author. `audit_rows()` returns
every override that has ever existed by default.

**Default-no-change verified live:** Meridian Finance EBITDA margin % actual=19.4,
`provenance_override` present: False. Ask AXIOM context byte-identical (a changed
context is a busted prompt-cache prefix).

**Authority (modelled + tested, enforced at Stage 2 write path):** three refusals
— no cross-department authoring; a company admin may grant authority but never
exercise it; platform staff excluded explicitly (operator bypass grants us
`require_company_admin` everywhere else — we must never be able to author a
customer's signed board figure). Authority is an explicit grant, deliberately NOT
an email match on `Department.head_email` (fine for a label, unacceptable for a
permission — an admin editing that field would silently transfer the right to
author board figures). No grant table yet ⇒ fails closed, nobody can author
anything. CORRECT.

---

## 2. LOCKED THIS SESSION (user rulings, 27 Jul)

**⭐ NO ROLLUP (user, emphatic).** CXO department-level overrides DO NOT propagate
to enterprise figures. Enterprise stays untouched computed truth. Architecturally
free: the resolver covers department KPIs, which do not render on enterprise
surfaces. No propagation logic to build; no aggregate-provenance concept needed.

**⭐ OVERRIDE = CORRECTION REQUEST, NOT PERMANENT OVERLAY (user, 27 Jul —
supersedes the spec's standing-overlay model).** The CXO asserts the right figure
on his department dashboard. The Admin then corrects the SOURCE inputs (KPIs, raw
data) within a reasonably short period so actual inputs match — or the CXO is
found to have been wrong and withdraws. Enterprise figures change ONLY when the
Admin changes the source. Truth is restored AT SOURCE, not maintained as a
parallel layer. This is stronger than the spec and is now the governing model.

**⭐ OVERRIDE RETIREMENT LIFECYCLE (advisor-proposed, PENDING USER LOCK).** Without
it the mechanic fails specifically: Admin corrects source → computed becomes 21.8
→ the override, also 21.8, now labels a number that needs no adjusting. Four
quarters of that and stale attributions accumulate on correct numbers, inverting
rare-equals-signal. Proposed: reuse the existing re-sign-off-on-data-change
trigger. Recompute lands → active override's value now matches (or is within
tolerance of) new computed → surface in the re-sign-off flow: "this adjustment
appears absorbed into the source data — retire it?" Retirement SUPERSEDES rather
than deletes; `supersession_kind` gains its second value. The CXO-was-wrong case
takes the same path with a different `supersession_kind` — the withdrawal is
recorded, never vanished (an override that disappears without trace is a worse
artifact than one that stands).

**⭐ DIVERGENCE WINDOW MUST BE BOUNDED AND VISIBLE (advisor-proposed, PENDING USER
LOCK).** Between override and source correction, department says 21.8 and source
says 19.4. Correct and intended, but only briefly. Overrides carry age; aged
overrides surface in an Admin queue as pending source corrections. This is the
pressure-gauge the ledger already describes — many standing overrides = data or
definitions are wrong, and it should be legible as that rather than accumulating
quietly.

---

## 3. DIRECT IN-SYSTEM EDITING — STATUS (user asked 27 Jul; answered exactly)

**CONFIRMED AND SHIPPED — OKR/KPI layer.** In-app CRUD with provenance stamping,
`source` = `'template' | 'in_app'`, reconciliation rules (in-app rows survive
re-uploads; template-absent rows flagged not deleted; collisions surfaced for
human resolution). 7L delivered KPI CRUD. Real and verified.

**NOT IN THE LEDGER — financial/raw-data layer.** The statement line items feeding
valuation, forecast and variance still enter through the locked versioned
template ONLY. Ledger searched; no entry. Per the standing rule (nothing is
locked until it is in this ledger), it is NOT in the design regardless of what
was said in conversation. **NEW LEDGER ITEM OPENED — see §4x-DE below.**

### §4x-DE. ADMIN DIRECT EDIT OF FINANCIAL/RAW DATA (NEW — opened 27 Jul)

Excel template must not be the only entry/edit point; Admin must be able to edit
figures directly in AXIOM. Required by the correction-request mechanic above —
that mechanic assumes an Admin correction path exists.

**Architectural constraint to settle before build:** `KpiPlan` is written per
dataset version; forecast snapshots are immutable; line-level variance computes
against them. An Admin editing a financial figure directly must either (a) MINT A
NEW DATASET VERSION — clean, preserves every downstream immutability property,
heavier; or (b) EDIT IN PLACE — breaks the snapshot guarantee valuation and
variance depend on.

**Advisor recommendation: (a) mint a version.** The Admin's correction is a
genuine new statement of the data. It triggers recompute → which triggers
re-sign-off invalidation → which is exactly where the override retirement prompt
fires. The whole loop closes on machinery that already exists. PENDING USER LOCK.

---

## 4. STAGE 1b — SIX ITEMS, ALL SMALL, NO REBUILD (gates Stage 2)

1. **Partial unique index.** Current `UniqueConstraint(company_id, metric_ref,
   superseded_at)` does NOT constrain active rows — Postgres treats NULLs as
   distinct, so every active row (`superseded_at IS NULL`) inserts cleanly and
   unlimited concurrent active overrides on one metric are possible. The report's
   "exactly one active assertion" claim is false as written and is load-bearing.
   Fix: partial unique index `WHERE superseded_at IS NULL` (or PG15+
   `NULLS NOT DISTINCT`).
2. **Scope in the constraint + `metric_ref` enum.** The constraint omits
   `target_scope` / `department_id` — two departments overriding the same
   `metric_ref` collide or resolve ambiguously. Fix to
   `(company_id, target_scope, department_id, metric_ref)` with the partial
   predicate. Separately: constrain `metric_ref` to an enum of resolver-covered
   metrics, rejected at BOTH write path and schema. Fail closed. (See scope
   correction, §1.)
3. **Enterprise read path.** `target_scope` accepts `enterprise` but everything
   proven runs the department path via `_serialize_kpis`. Either confirm the
   enterprise read path resolves, or drop `enterprise` from the enum until it
   does. A representable-but-unresolved scope is the same leak at a
   higher-visibility surface.
4. **Reason-category ruling.** OPEN — see §5.
5. **Route-table assertion.** `test_stage_1_exposes_no_write_endpoint` asserts
   `overrides.py` contains no router. That is a grep, not a guarantee — it says
   nothing about a write path added elsewhere. Assert against the app's actual
   route table: no POST/PATCH/DELETE resolving to an override path.
6. **[DEFERRED 27 Jul — blocked on an admin token. RE-GATED: must complete
   before Stage 2 SHIPS TO A CUSTOMER, not before Stage 2 is built. Leaves the
   FinancialDataset fixture caveat UNCLOSED — see IMMEDIATE STATE. Target
   confirmed: populate company 38 "AXIOM Test Fixture Co" (existing, non-
   showcase, 0 departments / 0 KPIs) through the application code path — do NOT
   create a fresh company and do NOT direct-INSERT; restore it to 0/0
   afterwards.]** **Production proof on a THROWAWAY COMPANY — NOT MERIDIAN.** Anonymous visitors
   land directly in Meridian; a test override in the flagship violates the
   few-or-zero rule in front of live traffic. Run as a one-off script in the
   Railway environment using the existing backend session. Insert → verify all
   surfaces → remove → verify restoration. Run `scripts/auth-regression.py`
   either side of insert AND removal (silent-empty is the failure mode; the
   sidebar-presence assertions catch what render checks miss). **Do NOT build a
   temporary Stage-2 endpoint to achieve this** — it puts the highest-risk
   artifact in the codebase into production ahead of its authority enforcement,
   inverting the point of the staged plan. This run also closes the fixture
   caveat (item 2 below), since `FinancialDataset` on `core.db.Base` is the
   accounts-world/legacy-identity seam that produced the last eight bugs — a stub
   across that bind is where a ninth would live.

**Report flags dispositioned:** (1) production proof → 1b item 6, no temp
endpoint. (2) fixture stub → folds into item 6, not chased separately. (3)
variance-on-displayed → CONFIRMED with condition, see §5. (4) `kpi_strip` outside
resolver → 1b item 2 whitelist; disclosure section is NOT sufficient cover for a
gap a valid user action can walk into.

---

## 5. RULINGS — CLOSED 27 Jul (both were blocking the 1b script)

**(A) Recomputed RAG badge provenance — ⭐ LOCKED 27 Jul. CONDITION CONFIRMED.**
Variance recomputing on the DISPLAYED value is correct — sign-off attests to the
dashboard AS SHOWN, and a card showing 21.8 with a RAG derived from 19.4 is
self-contradictory, which is not a thing to ask a CXO to personally attest to.
**The derived verdict MUST carry the provenance marker too.** Rationale, recorded
as the governing reason: a RAG badge that flips favorable→unfavorable **is itself
an adjusted figure**, and a bare flipped badge is a smaller version of the same
leak the feature exists to prevent — smaller only in pixels, not in consequence,
because a badge is what a reader scanning a dashboard actually processes.
Computed variance stays derivable from `provenance_override.computed_value` —
already satisfied by the Stage 1 payload.

**THIS IS A STAGE 2 BUILD CONDITION, NOT BUILT.** Recorded here so it gates the
write UI rather than being rediscovered after it ships. Stage 1 already emits
`variance` computed on the displayed value; what Stage 2 must add is the marker
on the badge itself, wherever a badge is rendered from an overridden figure —
department card, drill-down, and any export surface that renders a RAG.

**(B) `private CXO information` reason category — ⭐ LOCKED 27 Jul. REMOVED
ENTIRELY.** (Superseding the earlier advisor recommendation of a conditional
NOT NULL on the note.) The category, combined with a nullable `reason_note`, let
an override tell a board: *this number was changed, by the CFO, for reasons we
are not giving.* That is attributed number-laundering — the attribution real,
the reason a refusal to give one — and it would have been the most-selected
category precisely because it demanded nothing.

Every remaining category is substantive and stateable, which is what lets
`reason_note` stay nullable per B.5: **with the laundering option gone, the
category alone IS an explanation.** "Wrong input data" tells a reader where the
defect is; "private CXO information" told them only that they may not ask. The
four survivors — `calc_error`, `data_error`, `definition`, `other` — each also
name a place a fix belongs, which is what Stage 3's reason-routing acts on; a
category that routes nowhere was never carrying its weight.

**BUILT (see §4x STATUS below).** Removed from `REASON_CATEGORIES` and
`REASON_LABEL`, and rejected at the SCHEMA via
`CheckConstraint(ck_override_reason_category)` so a direct INSERT cannot
resurrect it. No data migration was required: zero rows in production and no
write endpoint — both confirmed before the change, not assumed.

**(B) `private CXO information` reason category.** Currently a `reason_category`
value, and `reason_note` is nullable per B.5. Combined, an override can tell a
board: this number was changed, by the CFO, for reasons we are not giving. That
is attributed number-laundering — the attribution is real, the reason is a
refusal to give one — and it will be the most-selected category because it
demands nothing. Two acceptable fixes: DROP the category, or make `reason_note`
NOT NULL when it is selected (schema-level check constraint, not form
validation). Advisor recommendation: the second — a CXO legitimately may know
something the data does not, and the prose can be internal-only while the
category stays board-visible; but an override whose reason is unstateable even
internally should not be creatable. **Note: the ledger says reason NOT NULL,
schema-enforced. Spec B.5's change-and-sign-without-prose carve-out is the looser
reading, and THE LEDGER SUPERSEDES THE SPEC.**

---

## 7. STAGE 2 GRANT MODEL — ⭐ LOCKED 27 Jul (user rulings). DESIGN ONLY, NOT BUILT.

The authority layer Stage 1 fails closed against. Stage 1's
`department_authority()` returns False for everyone because no grant table
exists; this is that table's design. **Recorded, not built.**

### 7.1 WHO GRANTS — the company admin

The **company admin** grants departmental authority. **Not the CEO** — a CEO has
no time for grant administration, and this is operational work.

The already-locked rule stands unchanged and is the spine of the whole feature:
**the admin may grant authority but may never exercise it.** The admin decides
who speaks for a department and can never speak for one.

### 7.2 GRANTS ARE ROWS, NOT A ROLE FIELD

Each grant is its own row with its own lifecycle: `granted_by`, `granted_at`,
`revoked_at`. **Revocation is a timestamp, not a deletion.**

Mirrors the override model's new-row-never-update discipline, for the same two
reasons: history is untouched **by construction** rather than by remembering to
preserve it, and multi-department support falls out free instead of needing a
join table bolted onto a role enum.

### 7.3 ONE PERSON MAY HOLD MULTIPLE DEPARTMENTS

E.g. one CXO over both Sales and Marketing. **Two grant rows.** Revoking one must
not disturb the other — which is automatic once grants are rows, and would have
required special-casing under a role field.

### 7.4 ⭐ REVOCATION NEVER TOUCHES HISTORY

Past sign-offs and overrides stand **exactly as made**, with the departed
executive's frozen `author_label` intact.

**A revocation that cascaded into historical attestations would be the worst
possible defect on this feature.** A board figure that loses its attester is
worse than one that never had an attester: the first looks like a covered-up
authorship, the second merely looks unsigned.

**TEST-PIN THIS (Stage 2 build requirement):** revoke a grant, then assert every
prior sign-off and override row is **byte-identical**. Per the standing principle
above, this must be asserted behaviourally — perform the revocation and compare
the rows, not merely observe that no cascade is declared.

### 7.5 DEPARTMENT CHANGE

The admin **moves the grant** to the new department head. Prior sign-offs remain
valid **for the date they were made**.

Display renders the role **as it was**: *"Signed off by J. Chen, then CHRO,
14 Mar."* Without the "then", a CEO reading the dashboard wonders why the head of
Operations signed HR's numbers — the attestation looks wrong precisely because
the display is showing today's org chart against a historical act. This is the
same reason `author_label` is frozen text and never a join (§4x Stage 1).

### 7.6 ⭐ VACANCY — NO ADMIN SIGN-OFF, EVER

When a CXO leaves, **authority does NOT revert to the admin.**

An admin who can sign off **collapses the separation the feature rests on**: the
person assigning authority would also be exercising it, and the board-facing
claim that *a named executive personally attested* becomes unverifiable from
outside. The signature would still exist; what it certifies would not.

**Two permitted paths, in order:**

**(a) INTERIM GRANT — primary.** The admin grants the department temporarily to
an **existing CXO** — e.g. Finance to the COO during a CFO search. A real
executive with a real name attests, so the sign-off means what it says. Uses the
multi-department machinery in 7.3 and **requires nothing new**. When the
replacement joins, the admin moves the grant per 7.5.

**(b) VACANCY STATE — fallback, only when there is genuinely no one to grant
to.** No grant. The dashboard **states it explicitly** — e.g. *"Finance: no CXO
assigned since 14 Mar."*

**A department with nobody accountable and a department whose CXO simply hasn't
acted yet are DIFFERENT STATES and must render differently.** An unsigned
dashboard that looks identical in both cases is the trap: it reads as executive
inattention when the real condition is an unfilled role, and it silently converts
an organisational gap into an apparent individual failure. (Same
three-state discipline as §4x suppression reasons and the CEI cards — absence is
never one state.)

**If admin involvement is ever needed during a vacancy,** the only acceptable
form is **admin acting on behalf of a named executive, rendered as such** —
reusing the existing admin-on-behalf-of audit attribution
(`_on_behalf_suffix`, §4s), **not a new mechanism**. Never a sign-off in the
admin's own name.

### 7.7 Consistency notes for whoever builds this

- `_on_behalf_suffix` matches the department head **by email string**. That is
  fine for the on-behalf LABEL in 7.6 and remains **unacceptable for the GRANT
  itself** (§4x Stage 1): an admin editing `Department.head_email` would
  otherwise silently transfer the right to author board figures. Grants are
  explicit rows; the label may keep using the email heuristic.
- Platform staff remain excluded from authoring, explicitly, even though the
  operator bypass grants them `require_company_admin` everywhere else.
- Stage 1's `department_authority()` already reads a grant model through
  `Base._department_authority_model` and fails closed when absent — this design
  is what fills that slot.

---

## 8. SIGN-OFF INVALIDATION — ⭐ LOCKED 27 Jul (user ruling). DESIGN ONLY, NOT BUILT.

How a sign-off stops being valid. Spec B.7 said new data un-signs an affected
KPI; these five rulings settle what "affected" means, which is the whole
difficulty. **Recorded, not built.**

### 8.1 THE TRIGGER — DISPLAYED VALUES ONLY

**A sign-off is invalidated by a change to any value the signed dashboard
actually displays, and nothing else.**

A correction to a department head's email — or any other artifact not rendered
on that dashboard — does **NOT** invalidate a CFO's attestation to the
financials.

**Rationale, recorded because this failure mode is quiet rather than loud:**

- **Too broad** and executives re-sign constantly for reasons they cannot see.
  The button becomes noise, and they click it without reviewing. **This destroys
  the feature more subtly than a bug would**: every signature still exists, the
  audit trail still looks complete, and not one of them means anything. Nothing
  in the system reports a fault.
- **Too narrow** and the original trap returns: a signed-off number that
  silently changed, with an attestation still attached to it.

The rule is therefore neither "any write to the company" nor "only this KPI
row" — it is exactly the set the signature actually covered, because sign-off
attests to the dashboard **as shown** (the same premise that made variance
recompute on the displayed value, §4x §5(A)).

### 8.2 THE DEPENDENCY SET IS COMPUTED, NEVER HAND-MAINTAINED

The resolver already knows which artifacts feed which surface. **The set of
values a signed dashboard depends on must be DERIVED from that machinery**, so
it cannot drift as the dashboard grows.

**A hand-maintained list of "things that invalidate" is a list that goes stale
silently — the same defect class as a declared-but-unbound constraint.** It would
be correct on the day it was written, and every subsequent panel added to the
department dashboard would be a value that changes without invalidating anything,
discovered only when a board asks why a signed figure moved. Nothing would fail;
the list would simply be incomplete.

This is the third application of the standing principle (see IMMEDIATE STATE):
derive the guard from the system, never restate the system in a second place
that can disagree with it.

### 8.3 SHOW THE DIFF AT RE-SIGN-OFF

**Not a bare "awaiting re-sign-off" — show which values changed and by how much
since the signature.**

This converts a chore back into the review it is supposed to be. A CXO who can
see what moved will re-review it; one facing an unexplained prompt will just
click. **The signature is only worth what the review behind it is worth**, and a
prompt with no diff is a prompt engineered to be dismissed.

### 8.4 THE RETIREMENT PROMPT FIRES HERE

The re-sign-off diff is the natural home for the **override retirement prompt**
(§4x §2, "override retirement lifecycle").

A source correction that absorbed a CXO's adjustment appears **in exactly that
list of changed values** — it is, definitionally, a displayed value that moved.
**One surface, both purposes:** the CXO sees what moved and is asked whether the
now-redundant override should be retired, in the same act.

This also closes the stale-attribution problem the retirement lifecycle was
opened for: without it, an absorbed override keeps labelling a number that no
longer needs adjusting, and four quarters of that inverts rare-equals-signal.

### 8.5 NO THRESHOLD

**Do NOT gate invalidation on magnitude.** No "only if the change exceeds X%".

Two reasons, both recorded:

1. **A silent small change to a signed figure is precisely the trap the
   mechanism exists to prevent.** A threshold does not reduce noise; it selects
   which silent changes are permitted, and it selects the small ones — which are
   the ones a reviewer would never catch unaided.
2. **Any threshold is a number someone will later have to defend to a board.**
   "Why did the CFO's attestation survive this change?" has no good answer that
   begins with an arbitrary percentage.

Noise is managed by 8.1 (scope the trigger correctly) and 8.3 (make the prompt
worth reading), **not** by suppressing invalidations.

---

## 6. OPERATIONAL NOTE (recurring, now twice)

Stage 1 report pastes corrupted in-window on first attempt both sessions —
mangled tables, sentences truncated mid-word, clauses dropped (one dropped clause
inverted the meaning of flag 4 and produced a wrong reading on first pass).
**STANDING RULE: build reports and any long document come in as a FILE UPLOAD
(.md/.txt), never a paste.** A dropped clause in a verification report is a
verification failure, not a formatting annoyance.


---

**4w. DICTIONARY / DEFINITION REGISTRY (concept locked --- 26 Jul)**

The tangible form of the transparency principle (§4u trust + the
one-canonical-definition standing rule). A repository of ALL
definitions/acronyms/methods/models (CEI, WACC, DCF, DLOM, attainment
bands, k-anonymity, etc.). TWO halves, ONE source: (1) a browsable
DICTIONARY page (search + categories:
Metrics/Acronyms/Methods/Models/Valuation) --- the \"Wikipedia\"; (2)
INLINE HOVER definitions (the killer half) --- any defined term,
wherever it appears, hoverable to show its definition (Wikipedia-style
hover-preview), delivering the definition at the moment of confusion.
KEY: it\'s NOT a parallel content system --- it\'s a VIEW over the
definition constants we\'re ALREADY centralizing (per the
one-canonical-definition rule: export the definition string once,
consume everywhere). One source (the definition constant), three
consumers (inline caption, hover tooltip, Dictionary page). STRATEGIC:
directly embodies the positioning (§4t rigor-as-moat made ACCESSIBLE not
off-putting --- a non-quant CEO hovers and learns instead of being
intimidated) + the correctness answer (§4u glass-box). Also a
sales/trust asset (a prospect seeing hover-definitions everywhere reads
transparency + rigor). BUILD: staged, later (not a sequence-jumper) ---
(1) establish definition-registry pattern (partly done via the standing
rule), (2) Dictionary page reading the registry, (3) inline hover as
definitions get registered. Every definition written from here (CEI
banding, etc.) should feed the registry.

**4v. CEI ORG-DISPLAY (#2 --- diagnosed 26 Jul, build pending 2 fixes +
decisions)**

User wants dept CEI on org cards + enterprise CEI breakdown. Diagnostic
findings:

-   **Sentiment pill is NOT the CEI --- keep it, don\'t replace.** Pill
    = comment-TONE composite (what people WROTE, tone-labelled
    free-text, 0-100, n=comments, floor \<3 comments). CEI = scored-ITEM
    composite (what people RATED, 0-10). They ACTIVELY DISAGREE on
    Meridian: Sales & Marketing = worst tone (0·Poor) but HIGHEST CEI
    (6.67) --- a valuable divergence (rates boxes high, vents in
    comments). Replacing the pill w/ CEI would DELETE a real independent
    signal. So CEI is a THIRD card measure (border=objective attainment,
    pill=tone, +CEI), own slot + label, not a swap.

-   **Build: add Dept CEI to /departments server-side** via
    \_pick_dept_slice alias logic → {cei, n, suppressed, reason}. NOT
    client-side join: summary.departments is keyed by RESPONSE-TIME
    names, only 2 of 7 Meridian match (misleadingly Finance+IT, the very
    two requested --- would look like it worked while dropping 5).

-   **THREE card states** (not two): scored (show n+value) · suppressed
    (responses exist, withheld for anonymity) · absent (not in cycle ---
    e.g. Exec). Shape differs: suppressed uses n, scored uses
    n_participants (reading the wrong one → undefined).

-   **Enterprise breakdown: data ALREADY in /cei payload** ---
    cei.tsx:589 calls Object.keys() and DISCARDS the values
    (cei/subscores/radar/suppression per dept). Breakdown needs no
    endpoint, just stop discarding.

-   **⚠ SCALE DEFECT (same class as the objective-status fix just done):
    CEI banded 3 ways across 2 scales** --- pill 0-100 (Good ≥70), /cei
    bands CEI ≥7.5/≥5/\<5, cards none. \"6.02\" beside \"Good ≥70\"
    invites reading 6.02 as catastrophic. DECISION PENDING: (1) always
    render CEI as \"6.0/10\" denominator-visible, never bare, never
    adjacent to pill without label \[advisor rec\]; (2) ONE canonical
    CEI banding everywhere (reconcile /cei\'s ≥7.5/≥5/\<5 into a single
    named scheme) \[advisor rec --- else it\'s the objective-status bug
    reincarnated\]; (3) pill stays as distinct tone signal.

-   **⚠ DEFECT FOUND (unfixed, FIX BEFORE display --- advisor OWNS a
    prior miss): the trend no_responses annotation is FALSE for
    suppressed depts.** HR (n=3) + Supply Chain (n=2) trend last-point
    says \"n=0, no responses from this department\" --- but they DID
    respond; they\'re SUPPRESSED for anonymity (k-floor +
    complement-inference). Blames non-participation when cause is
    privacy protection. The 4 unsuppressed depts match both surfaces
    perfectly (not alias --- the suppression path zeroes count +
    mislabels). **Advisor reviewed this annotation when it shipped
    (083deec) and recorded it as CORRECT --- it is not; checked the line
    broke at the gap but not that the reason string was true.** Fix:
    suppressed point carries suppression reason not no_responses;
    distinguish scored/suppressed/absent at the SOURCE so trend AND
    cards inherit correct reasons. \*\*FIXED: three states now flow from
    the source --- SCORED (value+n) · SUPPRESSED (\"withheld for
    anonymity --- responses exist but below the k-anonymity floor\", HR
    n=3 / Supply Chain n=2) · ABSENT (\"no responses from this
    department in this cycle\", Executive genuinely). Root: the merge
    collapsed suppressed+absent into \"no responses\" though
    department_slice knew the difference. Verified live. CAUGHT A SECOND
    SURFACE: the READINESS panel had the identical falsehood --- fixed
    both from one source. (Advisor\'s original sign-off missed not one
    string but a CLASS --- the suppressed/absent collapse propagated to
    multiple surfaces, none verified. Lesson: when a mislabel is found,
    check whether it\'s elsewhere too.)

-   **#2 CEI-DISPLAY DONE:** canonical CEI banding exported once,
    consumed everywhere --- reconciled a REAL pre-existing disagreement
    (/cei\'s deriveBand was actually ≥6.5 strong / ≥4.5 stable, NOT the
    ≥7.5/≥5 assumed; the existing in-use scheme was preserved as the one
    canonical). Scale-confusion trap caught IN THE ACT (CEI 0-10 beside
    tone pill 0-100) → denominator always shown + visually distinct so
    \"6.0/10\" can\'t be misread against \"Good ≥70\" (the #1-class bug
    prevented by design, not after shipping). Server-side dept CEI via
    alias slice (avoided the client-name-join that silently drops 5 of 7
    depts). Three states on cards (scored/suppressed/absent),
    definitions shown, feeds the future Dictionary. Enterprise breakdown
    renders (stopped discarding payload values). Publish-pending. \*\*#2
    FULLY VERIFIED (27340aa + frontend): all 3 states confirmed on cards
    --- scored (Finance 6.0/Ops 6.4/IT 6.5/Sales 6.6 + band), SUPPRESSED
    (HR + Supply Chain → \"CEI ---\" + \"withheld for anonymity\", NO
    number), ABSENT (Executive → \"CEI ---\" + \"no responses this
    cycle\"). Canonical scheme cei-band.ts ↔ assessment_engine.py
    byte-identical (GOOD ≥7.5 / NEUTRAL 5.0-7.4 / POOR \<5.0); /cei
    headline ternary now reads it (3 copies → 1). apply_kfloor runs
    BEFORE the cei map is read (no suppressed CEI exists to leak). DEMO
    HIGHLIGHT: Sales & IT near-identical CEI (6.6 vs 6.5) but OPPOSITE
    tone (0 red vs 75 green) --- the divergence that justifies keeping
    tone-pill + CEI as separate measures, visible on the flagship.
    \*\*#2 FULLY VERIFIED (27340aa + cei-band.ts): all 3 states
    confirmed on cards --- HR/Supply Chain \"CEI ---\" + \"withheld for
    anonymity\", Executive \"CEI ---\" + \"no responses this cycle\",
    scored depts show \"X.X/10\". Four misread-defences (denominator
    always shown, visual distinction from tone pill, band label, \"---\"
    never renders as 0). Canonical scheme byte-identical both sides
    (cei-band.ts ↔ assessment_engine.py, GOOD 7.5/NEUTRAL 5.0; /cei\'s
    local ternary now reads the shared constant --- three copies → one;
    Dictionary-ready). apply_kfloor runs BEFORE the map is read (no
    suppressed CEI exists to leak). DIVERGENCE SIGNAL VISIBLE (the
    payoff of keeping pill≠CEI): Sales CEI 6.6/tone 0-red vs IT CEI
    6.5/tone 75-green --- near-identical effectiveness, opposite tone
    (\"same by numbers, different in the room\").

**PRE-LAUNCH --- TESTING STRATEGY FOR V1.0 (added 26 Jul):** No single
app tests AXIOM end-to-end --- it\'s a STACK + human review, and the
most important layer (correctness) is bespoke. FIVE LAYERS: (1)
Functional/E2E UI flows --- Playwright (2026 consensus; complements the
existing auth-regression crawler + pytest, doesn\'t replace); (2) API
--- Postman (pytest already covers much); (3) LOAD/perf --- k6 or Locust
(Python-fit); MUST load-test MULTI-TENANT isolation specifically
(EID/CID many-companies shape = exactly where QA teams struggle); (4)
SECURITY --- OWASP ZAP + Snyk continuously, PLUS a human PEN-TEST from a
security firm before enterprise launch (compliance-sensitive SaaS
requires manual pen-test; pairs w/ SOC 2 §4u; non-optional for a
financial platform --- procurement demands the artifact); (5) production
monitoring --- Datadog/New Relic synthetic checks once live. ⚠ THE
AXIOM-SPECIFIC LAYER NO TOOL COVERS --- CORRECTNESS: golden-master /
known-answer tests YOU author (known inputs →
hand-computed/textbook-verified valuation/CEI/forecast outputs; assert
AXIOM matches) + independent methodology review (§4u Layer 3). THIS is
what answers the CFO\'s \"how do I know your numbers are right\" ---
bespoke, not bought, highest-value. Tools solve \~half; methodology +
strategy solve the rest.


**4y. DATAROOM — ADMIN DATA CONTROL CENTER (LOCKED 27 Jul 2026)**


## AXIOM ZERO — ARTIFACTS ARE CANONICAL, THE TEMPLATE IS AN ADAPTER

**This is the first stated principle of the data layer and everything below hangs
off it.** The AXIOM data model is a set of traceable ARTIFACTS, each carrying its
own provenance and timestamp. The Excel template is a VERSIONED ADAPTER that maps
cells → artifacts, forward- and backward-tolerant. It is NOT the schema.

- In-app edit writes an artifact immediately.
- Template upload PROPOSES artifact-changes for approval.
- Snapshots version the artifact set.
- The Data Update Wizard reviews artifact-diffs BY CATEGORY.
- Future ERP ingestion maps ERP fields → the SAME artifacts.

**⚠ THE DATAROOM IS A VIEW OVER ARTIFACTS, NOT A MIRROR OF CELLS.** User
description ("every cell in the spreadsheet must populate the Dataroom") is
directionally correct — the admin sees every filled data point, timestamped — but
the Dataroom's SHAPE must be artifact-shaped, not spreadsheet-shaped. If the
Dataroom is cell-shaped, the template silently becomes the schema again and
FUTURE ERP INGESTION HAS NOWHERE TO LAND (ERP data has no cells), forcing a
second parallel path. Artifact-shaped: template and ERP are both just adapters,
the Dataroom renders identically regardless of origin. Same visible result for
the admin, materially different future.

**Cost, on the record:** artifact-canonical is the more expensive architecture up
front (artifact layer, version→artifact mapping, per-artifact provenance,
snapshots, adapter tolerance) versus template-as-schema which is cheap to start.
Accepted deliberately: it is the difference between a data model hostage to a
spreadsheet and one that can evolve for years. Retrofitting after another year of
template-coupled features would be far worse.

**PREREQUISITE DIAGNOSIS (must run before scoping the build):** how coupled to
the template is the current data model, really? The honest answer determines
whether this is "add an artifact layer on top of a clean model" (moderate) or
"the template schema is load-bearing in the parser/storage and needs decoupling
first" (larger). Verify actual state before assuming.

---

## THE MOTION THIS SERVES (user, 27 Jul — full lifecycle)

1. Pilot completes. We receive 2 spreadsheets from the client — (a) financial +
   organizational data, (b) participant list.
2. **We upload on the client's behalf** and open the survey.
3. Feedback submitted → reports generated → reviewed with the customer.
4. Customer buys. **EID/CID account transferred to customer — NO DATA
   MIGRATION** (as previously decided).
5. Customer has full dashboard + results + Ask AXIOM. CXOs invited to review.
6. Ideas/recommendations flow into Projects & Initiatives supporting OKRs.
   Under-performing KPIs surface. Employees' voices are heard.
7. **From here on, data corrections are a normal ongoing need** — and must not
   require re-uploading a spreadsheet.

---

## THE DATAROOM

Lives in the **admin area**. Contains every data input — departmental AND
enterprise-wide — timestamped and provenance-stamped, editable in place.

**Locked properties:**

1. **The WebApp is the admin's control center, not the spreadsheet.** (user,
   verbatim principle)
2. **Instant in-place editing.** No re-upload required to change a number. The
   admin has maximum flexibility to make corrections.
3. **Template re-upload remains available** as a bulk alternative — not the only
   path, never the required path.
4. **Upload requires approval before overwrite.** An upload does not silently
   replace live data. The admin approves **cell-by-cell, category-by-category, or
   all**. (Data Update Wizard; diffs artifacts by category, so it is future-proof
   by construction — when the template grows, the Wizard automatically has more
   categories with no Wizard rework.)
5. **Revert.** If an upload was approved and the new dataset contained errors, the
   admin must be able to undo and revert to an earlier version of the dataset.
6. **Future ERP ingestion populates the same Dataroom** via the same artifact
   layer.

---

## FIVE CONSTRAINTS SETTLED 27 Jul

**(A) BATCHED PUBLISH, NOT PER-EDIT RECOMPUTE.** Instant editability yes; instant
recompute no. If every cell edit mints a dataset version and fires recompute, an
admin correcting 40 cells triggers 40 recomputes (forecast switch alone is
~8.7s eager). LOCKED: edits write artifacts immediately with provenance +
timestamp; an explicit PUBLISH mints ONE version and fires ONE recompute. Audit
trail records both the individual edits and the publish. Preserves the
immutability guarantees `KpiPlan`-per-dataset-version, immutable forecast
snapshots, and line-level variance depend on.

**(B) ADMIN EDITS AT SOURCE; CXO OVERRIDES ON THE DASHBOARD. NEVER MERGED.**
Dataroom write access is **Admin-only, explicitly excluding CXOs even for their
own department.** Two different acts on two different surfaces, and the
separation is what makes both trustworthy: if a CXO could edit the Dataroom he
could quietly fix his own number at source and the override trail would never
exist — the board-visible attributed exception replaced by a silent correction.
Ties directly to §4x.

**(C) OPERATOR FENCE — POST-TRANSFER.** During the pilot we hold admin and upload
on the client's behalf (correct). **After EID/CID transfer, the operator bypass
must NOT grant us Dataroom write on the customer's live data.** Same refusal
Stage 1 already models for overrides: we must never be able to author a
customer's signed board figure — and editing the source is authoring it more
thoroughly than an override does. Transfer must hand over Dataroom rights cleanly
and fence us out. (Note: `_operator_bypass_ok` currently fences on Transferred
pilots; this needs the equivalent on the Dataroom write path.)

**(D) PARTICIPANT-LIST EDITS ARE CONSTRAINED ONCE A CYCLE OPENS.** The second
template carries respondents — emails, departments, seniority bands. Editing
department or seniority after responses exist can retroactively break the
k-anonymity floor or shift department slices under collected data. This is the
partition-leak class that seeding exposed and that was LIVE in prod once already.
LOCKED: participant records freely editable before a cycle opens; constrained
once responses exist. Exact constraint set = pending spec.

**(E) THE §4x LOOP CLOSES HERE.** CXO overrides a figure on his department
dashboard (attributed, board-visible, no rollup to enterprise) → Admin corrects
the source in the Dataroom → publish mints a version → recompute → enterprise
figures change ONLY NOW → re-sign-off invalidation fires → override retirement
prompt fires ("this adjustment appears absorbed into the source data — retire
it?"). The override is a CORRECTION REQUEST WITH AN AUDIT TRAIL, and the Dataroom
is where the correction actually lands.

---

## ACCESS RULE — RE-AFFIRMED 27 Jul (user, explicit)

**⭐ THE CXO CANNOT EDIT SOURCE.** Dataroom WRITE access is Admin-only. This is
not a UI convention — it is the premise §4x Stage 1 was built on, and it is
server-side enforced at the write path. If a CXO could edit source he could
quietly correct his own number and the override trail would never exist: the
board-visible attributed exception replaced by a silent correction. The two acts
stay separate and stay on separate surfaces:

- **CXO** asserts on his department dashboard → attributed, board-visible, rare,
  reasoned, audited. No rollup to enterprise.
- **ADMIN** corrects at source in the Dataroom → publish → recompute →
  enterprise figures change.

Platform staff excluded post-transfer per constraint (C).

**OPEN (small, advisor recommends YES):** CXO *read* access to the source inputs
behind his own department's numbers. No write, no flag — just visibility, which
supports genuine review before sign-off ("what is this figure actually built
from?"). Costs nothing architecturally and strengthens the sign-off act. Pending
user confirmation.

---

## EDITING MODEL — MAKING THE RIGHT ARTIFACT EASY TO REACH

Cell-shape was never what made editing easy; a 1,000-cell grid is a poor
interface for "fix Q3 marketing headcount." Artifact-canonical makes it EASIER,
because every artifact has a stable identity and a label. Five affordances, in
priority order:

**1. EDIT-IN-CONTEXT FROM WHEREVER THE NUMBER APPEARS (the important one).** The
admin does not notice a wrong number in a data browser — he notices it on a
dashboard or in a report. So every rendered figure tracing to an editable
artifact carries an ADMIN-ONLY affordance: *edit source*. Click → land in the
Dataroom focused on that exact artifact → fix → publish. This works ONLY because
the rendered number already carries its artifact ID; a cell has no stable
identity across template versions, so cell-shape cannot offer this at all.
**Closes the §4x loop tightly:** Admin receives the override notification →
clicks straight through to the source input the CXO was asserting about →
corrects → publishes → retirement prompt fires.

**2. SEARCH-FIRST.** Type "EBITDA margin" or "Finance headcount" and jump to it.
Free once artifacts carry labels; faster than any spreadsheet navigation.

**3. STRUCTURE FOLLOWS THE MENTAL MODEL, NOT THE SHEET LAYOUT.** Entity →
statement/section → line item → period. *Income Statement › Revenue › FY2025.*
*Departments › Finance › head email.* How someone actually thinks about the
number they want to change.

**4. GRID VIEW AS A PROJECTION, NOT THE MODEL.** For bulk work (a full year of
actuals), offer a spreadsheet-like grid over the artifact set: inline edit, tab
between fields, paste a column straight out of Excel. Because it is a VIEW over
artifacts, the paste maps onto artifacts and provenance stays intact.
Spreadsheet ergonomics without the spreadsheet schema.

**5. PROVENANCE FILTERS + PRE-PUBLISH DIFF.** Filter by origin ("everything from
the v7 upload," "everything I changed this week," "everything never touched since
upload"). And a diff view before publish that REUSES THE DATA UPDATE WIZARD
SURFACE — one review surface for both channels (in-app edits and template
uploads), not two.

---

## EDITING MODEL — HOW AN ADMIN REACHES THE DATA ELEMENT HE WANTS (LOCKED 27 Jul)

Requirement (user): it must be EASY for the admin to edit the specific data
element he wants. Note that cell-shape was never what made editing easy — a
1,000-cell grid means scrolling and ctrl-F. Artifact-canonical makes it EASIER,
because every artifact carries a stable identity and a label. Five affordances,
all of which depend on that:

**1. EDIT-IN-CONTEXT FROM WHEREVER THE NUMBER APPEARS (the important one).** The
admin almost never notices a wrong number in a data browser — he notices it on a
dashboard or in a report. Every rendered figure tracing to an editable artifact
carries an ADMIN-ONLY affordance: *edit source*. Click → land in the Dataroom
focused on that exact artifact → fix → publish. **Only possible because the
rendered number already knows its artifact ID.** A cell has no stable identity
across template versions, so a cell-shaped Dataroom cannot offer this at all.
Closes the §4x loop tightly: Admin receives the override notification → clicks
through to the exact source input the CXO was asserting about → corrects →
publishes → recompute → retirement prompt.

**2. SEARCH-FIRST.** Type "EBITDA margin" or "Finance headcount", jump to it.
Free once artifacts carry labels; faster than any spreadsheet navigation.

**3. STRUCTURE FOLLOWS THE MENTAL MODEL, NOT THE SHEET LAYOUT.** Entity →
statement/section → line item → period. *Income Statement › Revenue › FY2025.*
*Departments › Finance › head email.* How someone actually thinks about the
number they want to change.

**4. GRID VIEW AS A PROJECTION, NOT THE MODEL.** For bulk work (entering a full
year of actuals), offer a spreadsheet-like grid OVER the artifact set: inline
edit, tab between fields, paste a column straight out of Excel. Because it is a
view over artifacts, the paste maps onto artifacts and provenance stays intact.
Spreadsheet ergonomics without the spreadsheet schema.

**5. PROVENANCE FILTERS + PRE-PUBLISH DIFF.** Filter by origin: "everything from
the v7 upload", "everything I changed this week", "everything never touched since
upload". And a diff view before publish that REUSES THE DATA UPDATE WIZARD
SURFACE — one review surface for both channels (in-app edit and template upload),
not two.

---

## ⭐ ACCESS RULE — HARDENED (user ruling, 27 Jul: "CXO cannot edit source")

**DATAROOM WRITE IS ADMIN-ONLY. A CXO CANNOT EDIT SOURCE DATA — NOT ENTERPRISE-
WIDE, NOT HIS OWN DEPARTMENT, NOT ANY ARTIFACT, EVER.** This is not a UI
convention; it is a server-side write-path rule, enforced the same way §4x
enforces override authority. It is the premise Stage 1 was built on and it must
not drift.

Rationale, on the record so it survives re-litigation: if a CXO can edit source,
he can quietly correct his own number at the input and **the override trail never
exists** — the board-visible attributed exception is replaced by a silent
correction. The entire §4x trust architecture (default-no-change, rare-equals-
signal, attributed exceptions with the computed value beside them) rests on the
CXO having exactly ONE way to change a number, and that way being visible.

**⭐ CXO READ ACCESS — LOCKED 27 Jul (user ruling). GRANTED, DEPARTMENTALLY
SCOPED.**

A CXO gets **READ** access to the Dataroom: the source inputs behind **his own
department's** numbers, and no others. **Write remains Admin-only, explicitly
excluding CXOs, enforced server-side** — the hardened rule above is unchanged and
this ruling does not soften it.

Rationale, recorded so it survives re-litigation:

1. **Read is what makes review-before-sign-off meaningful.** A CXO is being asked
   to personally attest to numbers and defend them to a board. Attestation
   without the ability to see what produced the figure is a signature on
   someone else's work — which is precisely the "the system's claims" posture the
   whole trust arc exists to replace.
2. **Read creates no laundering path.** Laundering requires the ability to
   *change* a number without leaving a trail. Reading changes nothing; the CXO's
   only channel for changing a figure remains the attributed override, and the
   §4x architecture (default-no-change, rare-equals-signal, attributed exceptions
   with the computed value beside them) is untouched by it.
3. **Departmental scoping applies to read, not only to write.** A CXO reads his
   OWN department's inputs, not another's. Same scoping rule and same server-side
   enforcement as §4x override authority — an explicit grant, never an inference
   from `Department.head_email`. Cross-department read would hand every CXO
   visibility into every other department's raw inputs, which is a confidentiality
   change nobody asked for and would be discovered by a customer rather than by
   us.

**STAGE / SCOPE: §4y, NOT BUILDABLE NOW.** Recorded, not built. It depends on the
Dataroom itself, and on the §4x Stage 2 department-authority grant table that
scoped read would reuse.

**NO SEPARATE "FLAG THIS INPUT" MECHANISM.** The CXO's correction channel already
exists and it is the override itself — §4x defines an override as a correction
request with an audit trail. A second flag path would be a second mechanism for
the same act (the "two surfaces one concept" bug class, deliberately seeded).
ONE channel: attributed, board-visible, routed to the Admin, retired when the
source correction lands.

---

## OPEN — NAMING (user call, non-blocking)

"Dataroom" collides with the M&A virtual-data-room meaning, and AXIOM already has
a document repository (R2 docs, 7k Document Intelligence). Two repositories, one
called the Dataroom and the other holding the actual documents, invites the
"two surfaces one concept" confusion flagged for Department Dashboard naming.
Either KEEP with an explicit split (**Dataroom = structured data; Documents =
unstructured**) or rename. User's call.

---

## BUILD ORDER (from prior session, re-affirmed)

Do NOT build the visible CRUD tab first and figure out reconciliation later. If
the tab ships and admins make in-app edits before reconciliation rules exist, the
next template upload can wipe their edits and users are trained to distrust the
feature. **The feature IS its reconciliation rules.**

1. Coupling diagnosis (how template-bound is the model, really?) + stable-ID
   prerequisite check.
2. Reconciliation rule set ratified as spec — create/rename/delete/edit/collision
   across both channels. Inherits the platform's standing collision philosophy:
   in-app survives, absent flagged not deleted, collisions surfaced for human
   resolution, provenance stamped, stable-ID keyed.
3. Read + edit Dataroom (valuable on its own).
4. Two-way reconciliation with the template + Data Update Wizard + revert.


---

**6. THE QUEUE (canonical order, as of 21 Jul close)**

**Claude Code lane:**

1.  **DONE (ed7e85a)**: root cause --- statement_units stored but NEVER
    consumed; pipeline hardcoded millions. Fix: normalize to canonical
    millions AT INGEST (UNIT_SCALE
    actual:1e-6/thousands:1e-3/millions:1) --- downstream correct by
    construction; template \_AXIOM metadata carries units
    (TEMPLATE_VERSION 7k-v2); sentinel 422 + cross-sheet magnitude
    (hard-reject \>50x or \<0.01x, warn 20-50x), human-readable
    messages; sample relabeled illustrative/in-thousands. Showcase
    untouched (STABLE 0.5156 unchanged). Milliner v3 data correctly left
    mixed (re-upload is the cure; would now 422). **Consequence:
    Lovable\'s units-display pass shrinks to label verification against
    clean re-upload.**

2.  **7L --- SHIPPED (Business Planning & Forecasting).** Template 7L-v3
    (full IS/BS/CF detail sheets, 3-15 yr horizon, kernel horizon
    follows client forecast to 10); ax_dataset_detail_lines sidecar
    (±0.5% subtotal 422s naming line+gap; certified kernel UNTOUCHED ---
    legacy valuations byte-identical); Forecast Studio: 5 methods (trend
    / driver / damped-trend smoothing \[honestly labeled\] / MC
    P10-P50-P90 / Ensemble w/ inverse-MAE weights \>=6pts persisted +
    divergence flag) + client-own set; PRIMARY rule wired
    (own-else-Ensemble default; primary-only feeds
    valuation/viability/frontier; switch = eager \~8.7s recompute w/
    progress); immutable forecast snapshots + line-level variance
    (abs/%/fav-unfav) on twin + standard KPI set + self-defined KPIs v1
    (simple arithmetic over named lines). Report print-tables cap 5
    cols + in-app note. Migration: 7k-v2/legacy valid, honest
    degradation. **Milliner re-entry MUST use template v3 --- strategy
    doc\'s 10-yr plan goes in forecast columns = client-forecast set
    (kills \"no client plan on file\").** Lovable integration points
    delivered (Forecast Studio UI, wizard step 3.5 ask-the-user flow,
    variance surfaces, KPI CRUD).

3.  **Post-7L batch --- SHIPPED (items 2-4 verified; item 1 details
    pending user paste; addendum item 5 invite-roster status
    unconfirmed):** (2) remember-me: login remember flag -\> 30-day JWT
    (24h default), expires_in returned; revocation = global secret
    rotation only (client-side logout is v1 floor) -\> **token_version
    per-user log-out-everywhere ADDED TO HARDENING LIST
    (pre-launch)**. (3) readiness: ax_readiness + GET/PUT
    /companies/{id}/readiness (admin write, 6 ANFIS sliders 0-10,
    computed score returned) --- Lovable wiring shape delivered,
    queued. (4) GET /companies/25/documents -\> 200, strategy doc
    extracted:true 46pp/97,982 chars --- **DOCUMENT ALIVE;
    Additional-Documents emptiness = frontend-only, closed.** Pattern:
    framework + document \"empty panels\" both backend-complete,
    frontend-display. **7k --- DOCUMENT INTELLIGENCE: SHIPPED.**
    documents.py analyzer + ax_document_text/chunks +
    ax_document_proposals; pdfplumber/python-docx, watermark strip, no
    OCR (extracted:false honest); Prescience injection on
    delimited-untrusted seam w/ \[doc.slug.pN\] citations (adversarial
    test: quoted, not obeyed); synthesis (Sonnet, cite-or-decline,
    \~\$0.19/run, doc-set-signature cached) -\> proposals into shared
    disposition machinery; SWOT-proposals -\> SWOT quadrants w/ source
    tags (never Initiatives); rec-proposals -\> Initiative on adopt.
    Milliner: 46pp strategy doc extracted, 12 cited proposals LIVE
    awaiting user review; **synthesis itself flagged the
    template-vs-document revenue contradiction as a proposed Weakness
    --- traceable-or-silent proven in production.** Truthful wizard
    step-4 copy delivered for Lovable swap.

4.  7j --- rooms + Brief backend, NOW LAST in arc per 4f (+ prompt
    caching; capex caveat; radar events + doc grounding feed Brief).

5.  Commercial Architecture phase
    (EID/multi-seat/transfers/tiers/limits/subscriptions/partner
    attribution; CID semantics Q still open).

6.  EID-on-artifacts + content-packing pass (cross-tool, below). DONE
    this session: /companies/{id} GET (+anon showcase carve-out) + PATCH
    (c7c425d) · 7i shipped · SENTINEL nightly armed · AXIOM_SECRET
    rotated.

**Lovable lane:**

1.  Setup Wizard SHIPPED (bundle index-CtzWPLPm.js; anon sweep 46/46
    incl /wizard). PENDING: operator sweep + automated walkthrough
    (needs fresh post-rotation token) + user\'s broken-buttons list -\>
    friction fix pass. Original script was (contained flow, START/NEXT,
    in-place upload w/ friendly-failure contract, mandatory =
    basics+template only, optional = logo/docs/invites, two-speed finish
    \[financials now, assessment as feedback lands\], resume-from-data,
    finish -\> Download Reports / Share Results / Key Initiatives;
    crawler stays green w/ wizard route).

2.  \[EXTENDED\] Wizard-fix pass + 7k surfaces: original fixes (logo
    persistence, resume, invite-kind split w/ landing verification,
    units display verdict, sample-sentinel warning) + extraction badges
    on documents + PROPOSAL REVIEW SURFACE (12 live Milliner proposals
    need a home: citation chips, Accept/Dismiss -\> adopt/disposition
    endpoints) + wizard step-4 truthful copy swap.

3.  Commercial script: DCT Advisory page (/advisory, copy
    drafted+user-revised, single 5-hr/\$8,500 SKU) + About page (founder
    & chief architect) + partner Tier 1 pricing presence + Step-7
    tooltip Activation-Session sentence. **BLOCKED ON: user bio facts +
    photo.**

4.  Ask-AXIOM panel (Prescience sub-tabs under Enterprise Optimization:
    Recommendations · Multiverse · Resilience · Causal Map · Prescience
    Brief; cited answers w/ source chips deep-linking to tabs; demo =
    scripted exchange, zero API calls).

5.  7j room frontends as backend lands.

6.  Possible rider: \"Back to axiomdynamics.app\" link in /free-pilot
    minimal header (user hasn\'t ruled).

**DONE this era (Lovable):** landing/pricing Log in+Register · Pilot
Companies tab + transfer UI · Executive button removal · /free-pilot
header trim + dark-pine header w/ white logo · Wasserstein copy edit ·
Railway hostname + console-log strip · pricing multi-company line ·
Learning Lab nav removal · single-sample demotion (Meridian only
visible; Halcyon/Helois backend-side via /c/{cid}) · global asArray
hardening · the crawler.

**Cross-tool / end-stage (locked order):** content-packing pass (ONE
artifact refresh at feature-complete: PDF+PPT+User Manual all features;
**Meridian\'s artifacts only --- Halcyon/Helois FROZEN per single-sample
ruling**; logos bake in; EID on artifacts) -\> mobile responsive pass
(Tier 1, LAST feature item) -\> final verification pass (f4 member
account creation + crawler member mode + full sweep all modes + mobile
viewports).

**7. LAUNCH GATES (after feature-complete; unchanged unless noted)**

ABC scoring run (first real CEI/SWOT) · full-loop walkthrough
(flag→adopt→lead→claim→RAG) · hardening: rotate AXIOM_SECRET; (done
early via CORS fix once verified); DMARC→quarantine; FRIENDS100 off
(**superseded/structured by pilot flag --- decide whether code still
exists to turn off**); legacy user id 8; **token_version column for
per-user log-out-everywhere (30-day tokens currently only globally
revocable);** live-Stripe flip-back note; Lovable security scan;
EULA/disclaimer→counsel; strip console debug logging.

**PRE-LAUNCH (V1.0) --- PARTICIPANT ALLOWANCES (added 26 Jul):**
Increase participant allowances (assessors AND CXOs) in both AXIOM
Business and AXIOM Prescience packages --- current §4d seat limits
(Business 10/50/5, Prescience 25/150/15) are too low for launch. When
actioned: (1) set new Business vs. Prescience seat counts, (2) update
assessor seat counter (§4d) + k-anonymity floors on Department ×
Seniority intersections for the higher counts, (3) update in-app
seat-limit enforcement + overage rules. Exact numbers deferred to
pre-launch decision.

**PRE-LAUNCH / EARLY-COMMERCIAL --- SOC 2 TYPE II + PROCESSING INTEGRITY
(added 26 Jul, see §4u):** table-stakes for enterprise procurement
(\~65% of buyers demand compliance proof). Fund it. Include the
Processing Integrity criterion (differentiator for a financial-outputs
platform; requires formalizing validation logic, processing SLAs,
reconciliation evidence). Type II (operating effectiveness over time),
not Type I. Also: methodology white paper (do now, no cost) +
independent methodology attestation (later, deal-driven).

**8. STANDING DISCIPLINE**

**MERIDIAN FLAGSHIP RULE (locked 26 Jul):** Meridian (company 20, the
flagship showcase) must have ABSOLUTELY ALL possible data inputs
populated so EVERY feature demonstrates in full glory --- no empty
states, no placeholders, no \"no data\" on the showcase. An empty SWOT /
blank chart / unpopulated slice on Meridian is the flagship UNDERSELLING
the product, not an honest-empty-state doing its job. When any new
feature ships, check: does Meridian have the data to show it richly? If
not, seed it. (This is the demo counterpart to traceable-or-silent: on
the flagship, ensure the data EXISTS so nothing has to be silent.
Applies to every department slice, every analytics surface, every tab.)
**⚠ CAVEAT (26 Jul): before seeding, DIAGNOSE whether an empty state is
missing-data or a BUG --- the department-page empty SWOT / placeholder
trend turned out to be the alias-resolution gap (page reads used current
dept name against old-named frozen history), NOT missing data. Seeding
would have been misdiagnosis. Verify the data doesn\'t already
exist-but-unreachable before seeding.** **⚠⚠ FURTHER CORRECTION (26 Jul,
commit 3389c47): even the \"alias gap\" diagnosis was WRONG. The empty
SWOT was a RENDERER FIELD-NAME BUG --- renderer read it.label ?? it.text
?? it.axis but the key is it.title; the slice was fully populated +
already alias-resolved (since 4a9cdf4), it just drew as blank bullets.
Same one-word bug (title) caused the \"Category 1..13\" subscore labels
and fed the truncation confusion. Found ONLY by querying live data, not
re-reading code (re-reading code re-confirms the wrong assumption).
LESSON: to find a bug in your assumptions, inspect REALITY not your own
code. And: an empty state can be (a) missing data, (b) unreachable data
(query/alias), or (c) present-but-mis-rendered data (field name) ---
diagnose WHICH before fixing. The one genuine data gap: Meridian has 1
closed cycle so the CEI TREND chart can\'t draw (a line needs 2+ points;
drawing 1 point would imply false history) --- THAT is a real
demo-population item (seed more Meridian cycles). Readiness/trend
per-department remain enterprise-only-by-construction
(assessment_summary(department=None) hardcoded; \_show_slice strips
departments) = the backend follow-up lane, not a name-mismatch.**

One script per tool at a time · evidence-first recon (recon gates on big
builds --- paid off repeatedly: tenant trap, no-DP-in-repo,
masquerading-500, hardcoded-tenant regression PREVENTED, phantom
endpoint) · published-domain verification with bundle hash · **the
crawler runs after every build (replaces hand-clicking); silent-empty is
the new failure mode, so presence assertions matter as much as render
checks** · authenticated-session checks mandatory for
auth/accounts/slots changes · **no unguarded iteration over fetched data
--- all list reads through asArray, empty states never crashes** ·
**cleanup deletes scoped to exact created ids, never
all-X-for-company-Y** · **no code may join accounts-world ids against
legacy-identity ids --- email is the only cross-world key** · **infra
start-flags via Railway env vars, not Procfile** ·
**⭐ MINT CAPABILITY IS FOR VERIFICATION READS — NOT STANDING WRITE PERMISSION
(recorded 27 Jul, beside the Railway capability fence). `scripts/mint_operator_token.py`
gives automated runs UNATTENDED SUPER-ADMIN JWT MINTING: the crawler now holds,
without a human in the loop, a credential that can do anything a super admin can
do. That is the correct trade for a verification tool that must never go stale,
and it is a real increase in what an automated run is capable of. THE RULE:
the mint capability exists for verification READS. PRODUCTION WRITES REQUIRE AN
EXPLICITLY AUTHORIZED LANE, NAMED BY THE USER, EACH TIME. The ability to mint is
not permission to write, and no future lane may treat "the crawler can already
authenticate" as authorization for anything beyond reading. §4x Stage 1b item 6
is such a lane — AUTHORIZED 27 Jul, SCOPED TO COMPANY 38 ONLY.** · no fabricated
artifacts · showcase = enterprises 20/21/22 via GET
/access/showcase-companies, never hardcoded · 4xx never retried · demo
fires zero authenticated calls · components never render null · gates
degrade visibly · PPT/deck regeneration deferred to content-packing pass
· **Claude Code verifications are single-pass and bounded (max 3
attempts, no long sleeps); anything requiring waiting --- deploys,
nightly jobs, interactive logins --- is reported as
pending-external-check, NEVER polled** · **nothing is locked until it\'s
in this ledger**.

**Added 26 Jul:** · **test data-migrations against production-shaped
DIRTY data (duplicates/orphans/multiple-roots), not clean seeds; deploy
data-migrations WATCHED (tail logs)** --- the re-key migration passed
clean-data tests and CRASHED production on real dirty data · **FRONTEND
TOOLING TRAPS (routetree era):** (a) bun run build = tsc && vite build,
but a new route can\'t typecheck until built --- run build:vite first;
(b) adding any route regenerates routeTree.gen.ts --- the committed tree
MUST stay the LOOSE \@ts-nocheck variant or Register augmentation breaks
\<Link\> typing in \~80 untouched files (scripts/check-routetree.mjs
guards this); (c) a validateSearch on a route makes search REQUIRED on
every \<Link\> app-wide --- don\'t add it casually · **alias-resolution
must be wired into EVERY name-matching read (assessment/participant
paths store department as NAME string, not FK) --- resolve
name→stable-id through DepartmentAlias at READ time, never rewrite
frozen history; a leftover client-side name-filter silently re-imposes
the bug atop the backend fix** · **the advisor works FROM the ledger,
never from memory; every decision written into this file (the
\"parking\" failure mode is fixed by durable writes, not promises)**.

**Added 26 Jul (evening):** · **SERVED-BUNDLE-IS-TRUTH CUTS BOTH WAYS
--- do NOT assert Publish-queue depth by counting commits since the last
confirmed Publish; that OVER-reports pending work (advisor wrongly
claimed \"sixteen pending\" for several turns while 65501e3/d88a2d8 were
already LIVE). \"Pushed ≠ live\" also means \"committed ≠ pending\" ---
VERIFY against the served bundle before stating what\'s live vs.
pending. RELIABLE PROBE: fetch /assets/AppLayout-\*.js (or the relevant
served chunk) and grep for a STRING LITERAL unique to a given commit
(aria-labels, component names, placeholder text) --- survives
minification, isn\'t data-gated (unlike tab labels / KPI text which
SSR-render as loading states; CSS hashes also differ between Lovable\'s
build env and a local checkout, so those probes are inconclusive not
negative).** · **ONE CANONICAL BANDING PER METRIC + DEFINITION ALWAYS
SHOWN (design principle --- user-affirmed 26 Jul):** any user-facing
metric has exactly ONE band scheme (thresholds+colors) in ONE place,
consumed by every surface --- never two surfaces banding the same number
differently (objective-status bug AND the CEI-3-ways-across-2-scales bug
were both this class). Every number shows its measure + bands + scale
explicitly (denominator visible, e.g. \"6.0/10\"), ENFORCED not
hand-maintained (export the definition string + threshold constants,
interpolate --- one string, N consumers). \"Maximum transparency about
what each number means\" is a CORE design principle. Before shipping any
banded/scored display: one canonical scheme? definition shown? scale
unambiguous?

**9. OPEN QUESTIONS AWAITING USER / NEXT-SESSION STARTERS**

-   **Milliner clean re-entry** (all sheets, thousands, real BS/CF from
    strategy-doc actuals, sample rows replaced) --- the linchpin:
    triggers on-upload recompute, correct \$M rendering, first
    fully-clean document-informed company; also 7L\'s verification
    asset.

-   **Review Milliner\'s 12 live proposals** (Initiatives -\> Proposals
    tab): editorial verdict + spot-audit citation quotes; accept/dismiss
    for real.

-   **Paste Claude Code\'s contamination diagnosis** (script fired
    pre-sleep) -\> approve fix.

-   **Itemize the broken wizard buttons** from the Milliner run -\>
    Lovable fix pass.

-   **Tomorrow\'s nightly log line** (railway logs: \"nightly sweep
    done: {\...}\") -\> closes 7i final box.

-   **Fresh operator token to Lovable** for operator sweep + automated
    walkthrough (rotate after).

-   Wizard step-4 copy ruling: soften now (lean yes) vs wait for 7k.

-   **Founder bio facts + photo** --- blocks the commercial script
    (Advisory + About pages).

-   CID semantics (company-level per system vs per-report per user\'s
    description) --- one-line question to Claude Code before Entity
    Model.

-   Pricing: volume price points for HoldCo / consulting segments
    (Entity Model part b).

-   /free-pilot minimal header: add a \"Back to site\" link, or keep
    logo-only?

-   Customer quotes / Capterra / awards / book content for placeholder
    slots (whenever available).
