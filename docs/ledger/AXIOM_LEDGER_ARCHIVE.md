# AXIOM MASTER LEDGER — ARCHIVE (CLOSED ITEMS)

**Split from the master ledger 27 Jul 2026. Text is verbatim; nothing rewritten.**

**LEDGER-ARCHIVE is canonical for anything CLOSED.** For anything open — live
decisions, locked-but-unbuilt designs, active incidents, the queue, standing
rules, open questions — LEDGER-CORE is canonical. Upload this file only when a
specific question needs shipped history or a closed incident.

**Do not move an item back to CORE to re-decide it.** If a closed item needs
reopening, open a NEW entry in CORE that references this one; leaving the closed
record intact is what makes it evidence.

**Contents:** §1 Shipped & Verified · §2-FIXED KPI variance direction (closed
27 Jul) · §4q item 1 Department Dashboard build log (incl. the alias fix and the
k-anonymity partition defect) · §5 Incident Log, the seam-bug era, closed 21 Jul.

---

## 2-FIXED. KPI VARIANCE DIRECTION — CLOSED 27 Jul 2026 (e496444)

Moved from CORE §2 on 27 Jul. The original entry is reproduced VERBATIM below;
the resolution follows it. Nothing in the original text has been altered — per
the split rule, a closed record is evidence and is not rewritten.

### Original CORE §2 entry (verbatim)

> **⚠ REAL DEFECT --- KPI VARIANCE DIRECTION IS BACKWARDS PRODUCT-WIDE
> (found 26 Jul, commit d03c406):** \_kpi_variance.status is
> direction-blind --- documented \"favorable when actual \>= plan\" --- so
> EVERY lower-is-better KPI (unplanned downtime, cost, defect rate, churn,
> days-to-close, etc.) is labeled \"favorable\" when it\'s actually
> WORSENING. Meridian\'s Unplanned downtime 101 vs 95 plan returns
> \"favorable\" (wrong). This affects EVERYWHERE KPI variance status shows
> (main KPI surfaces, reports, dashboard), not just the department page.
> There is NO polarity field on KpiPlan (name/unit/plan/actual/target
> only). **DURABLE FIX (flagged, not built):** add a direction/polarity
> column to KpiPlan, captured in the UPLOAD TEMPLATE so the KPI\'s owner
> STATES direction (not guessed); \_kpi_variance must honor it. Until
> then: the department-page meters (d03c406) INFER direction from KPI name
> AND PRINT the assumption on each meter (\"lower/higher is better\") so
> it\'s visible + correctable --- a silent guess would be worse. This is a
> pre-launch correctness item.

### Resolution — built as specified (e496444, 27 Jul 2026)

The durable fix was built exactly as the entry specified, not worked around:

- **`direction` column on `KpiPlan`**, values `higher_better` | `lower_better`.
- **Captured in the UPLOAD TEMPLATE** — column I, `TEMPLATE_VERSION` `7M-v7.5`
  (7.0–7.5 accepted). The KPI's owner STATES direction; the system does not
  guess it.
- **`_kpi_variance` honours it**: `good = (actual <= plan) if lower else
  (actual >= plan)`. Magnitude is direction-independent; only the verdict flips.
- **The name-keyword heuristic survives only as a labelled fallback** for rows
  predating the column, and the department-page meter prints `(inferred)`
  wherever it is used — the entry's own "visible + correctable, a silent guess
  would be worse" principle, kept rather than discarded once the column landed.

**Why the column was necessary and the heuristic was not sufficient:** the B2
seed dry-run put the heuristic against 8 realistic KPI names and it
misclassified 4 — "Audit findings open: 5 against a target of 2" rendered
GREEN. That measurement is what converted this from a deferred item into a
shipped one.

**Verification:** Meridian's Unplanned downtime 101 vs 95 plan now returns
`unfavorable` — the exact case named in the original entry. Frontend consumes
the stored direction in `db23ded`. Tests: `tests/unit/test_kpi_direction.py`
(11 tests) pin the flip, the equality case, the unchanged higher-better path,
and the template round-trip.

**Related commits:** `e496444` (direction column + template capture + variance
fix) · `db23ded` (frontend reads stored direction, marks inferred rows).

---

## 1. SHIPPED & VERIFIED

**1. SHIPPED & VERIFIED (do not rebuild)**

-   Core product: purchase→create→CID→magic-link invites; ingestion
    (locked templates, versioned datasets, R2 docs); CEI (taxonomy v2
    13/78/361, anonymity, Haiku sentiment, dispersion); derived SWOT;
    Key Initiatives (lifecycle, RAG); 7e execution layer; recommendation
    dispositions; 7g Coherence backend.

-   Artifacts: ivory PDF (issued dates + logos); comprehensive deck
    (ivory design, **49 slides --- ruled in-spec**, design range
    49--57); showcase pre-generation (enterprises 20/21/22 via GET
    /access/showcase-companies, never hardcoded); share-by-link.
    Board-report page-16 four-bar chart: FIXED. Stat-card overlaps:
    FIXED. PPT: FIXED.

-   **Executive Presentation: DELETED** --- backend generation ceased
    (on-demand route returns 410); Lovable button removal pending (see
    queue). Stored old executive artifacts remain, not produced going
    forward.

-   <support@axiomdynamics.app> live (Zoho, MX/SPF/DKIM).
    ANTHROPIC_API_KEY live in prod.

-   **7h --- Prescience AI core (SHIPPED, commit 438fb29)**:
    prescience.py; build_company_context (source-tagged, cached per
    dataset/cycle/initiatives/focus); POST
    /companies/{id}/prescience/ask (Sonnet 4.6 pinned via
    AXIOM_PRESCIENCE_MODEL; viewers can ask, writes 403; cite-or-decline
    persona); conversations (10-turn window); daily cap 200 → 429; usage
    metering; 503 if no key; injection posture (instructions only in
    system prompt). Cost ≈ \$0.013--0.018/question. **Document/thread
    text NOT indexed --- context is metadata-only; extraction stage is
    prerequisite for quoting docs (must use delimited-untrusted seam).**

-   **FP-1 --- Free Pilot backend (SHIPPED)**: ax_pilot_companies
    (existence = is_pilot; per-stage timestamps), ax_transfer_offers;
    POST/GET /admin/pilots, status override (Transferred rejected 422),
    transfer offers CRUD + revoke (409 if claimed); Stripe webhook
    claims pending offer by buyer email (case-insensitive) → slot
    applies to transfer; tenant rewritten across Enterprise +
    Financial-Core (the \"tenant trap\" --- legacy /api/v1 routes gate
    on tenant only); seller fully revoked incl. operator-bypass fence
    (\_operator_bypass_ok, Transferred pilots only); pilots excluded
    from \_slots_used while non-transferred; no-offer checkout path
    byte-identical.

-   **7c-2 --- Multiverse kernel + Move Library + decision search
    (SHIPPED)**: prescience_decision.py, six ax\_\* tables. Move library
    (7 atoms + user-defined + acquisition/divestiture mini-intake →
    additive proforma deltas); evaluate_trajectory (cheap n=100 / full
    n=2000+overlays, cached); bounded beam search (≤3 moves, config via
    AXIOM_DECISION\_\*); frontier (λ=0.5 persisted,
    P(target)=P(EV\>current-plan mean EV), do-nothing evaluated at full
    tier for like-for-like percentile, Pareto points, DP policy surfaces
    for interpolation --- never live MC); async job pattern
    (ax_frontier_jobs); nightly recompute daemon + single-flight DB
    lock + POST /internal/frontier/recompute. Meridian: 10.7s search,
    \~11s/company/night. **Nightly scheduler: APPROVED ON --- set
    AXIOM_DECISION_NIGHTLY=1** (confirm first-night single-flight + wall
    time after first run).

-   **7i --- Viability Kernel (Sentinel) + Radar + unified watcher
    (SHIPPED, commits 1540d83+ad21ff0)**: sentinel.py; bisection
    shock-space to failure surfaces (cash-ruin MC, covenant, EV\<debt,
    DtD); STABLE/FRAGILE/CRITICAL bands (thresholds config, persisted in
    payload); named nearest-breach + 12-mo probability;
    minimum-intervention prescriptions -\> dispositions; CSD honest
    available:false (\<8 yrs history); ax_viability/ax_radar\_\* tables;
    radar events (band_transition, sequence/ΔEV changes); GET
    /companies/{id}/viability (showcase carve-out anon) + /radar/events
    (member-only); folded into ONE nightly scheduler, single-flight;
    +160ms/company incremental. **AXIOM_SENTINEL_NIGHTLY=1 LIVE;
    on-upload trigger live (env-independent, \~10s background recompute
    per real upload). AXIOM_SECRET ROTATED (86-char random; hardening
    item DONE-EARLY; old sessions dead).** Prod bands: Meridian STABLE
    0.516, Halcyon STABLE 0.406, **Helois genuinely CRITICAL (EV\<debt,
    p12m 0.96) --- demo asset: showcase spans full band range for 7j
    Resilience room.** Pending: first nightly log line (tomorrow) + user
    browser login confirm.

-   /free-pilot page + landing/pricing \"Start a Free Pilot\" buttons:
    built, published, user-reviewed (\"looks good\"). Bundle hash still
    owed by Lovable for the record.

**SHIPPED 26 Jul (post-21-Jul work --- this session)**

-   **Department stable-ID re-key + alias-integrity (SHIPPED, commits
    8e15831 → 574fd83 → f13ec79):** dept_key was sha1(name) (a NAME
    hash, not stable) --- renaming a department created a duplicate
    (root cause of Milliner\'s twin org trees). Now dept_key =
    uuid4().hex (opaque, minted at creation; name = mutable display
    attribute). ax_department_aliases (old-name→stable-id,
    first-writer-wins). Rename records aliases (both old + new resolve
    to same dept --- no re-upload duplication). Delete removes its
    aliases (was orphaning them → future upload of old name would
    re-duplicate). flagged_absent now fires on the GATE path (was dead
    code --- guard if departments and approved is None never fired since
    gate passes a dict; fixed via named_dept_ids vs seen_dept_ids so
    partial approval doesn\'t wrongly flag). **PRODUCTION CRASH +
    RECOVERY:** first re-key deploy CRASHED prod (SQLAlchemy
    IntegrityError uq_dept_alias --- production had duplicate depts
    colliding on normalized name; SessionLocal autoflush=False meant
    in-loop dedupe couldn\'t see pending inserts). Rolled back in
    minutes; fixed with in-memory claims set + SAVEPOINT-per-alias
    (skip-and-log on collision) + dirty-data test battery that
    REPRODUCES the crash on old code. LESSON: test migrations against
    production-shaped DIRTY data (duplicates/orphans/multiple-roots),
    not clean seeds; deploy data-migrations WATCHED. Baseline 305→316
    tests, 0 failed.

-   **Milliner cleanup (surgical merge):** 21 depts / 3 roots → 14 depts
    / 1 root (Executive Management). 7 delete-with-reassign merges
    (moved 32 objectives / 40 KPIs across all 11 dataset versions ---
    \_dept_out counts are active-dataset-scoped but delete reassigns
    across ALL versions; know this before running on a real client) +
    re-parent Internal Audit under Exec Mgmt. All KPIs preserved.
    Carries 7 inert dangling aliases from pre-fix merges (resolve to
    nothing = clean, not a trap) --- one-off sweep whenever.

-   **Meridian canonical rename (flagship, alias-safe):** in-place PUT
    renames (NOT re-upload --- avoids duplication trap), head fields
    echoed. Executive→Executive Management, Finance→Finance and
    Accounting, Technology→Information Technology, Supply Chain→Supply
    Chain and Logistics, HR→Human Resources. Operations already
    canonical; Sales & Marketing KEPT combined (client-real-names
    principle: canonical taxonomy is the standard MENU, not a mandate;
    clients use their own names). Alias-recording VERIFIED via
    throwaway-fixture probe (old name resolves to same dept, no dup) ---
    f13ec79 was live when renamed. 7 depts / 1 root, canonical,
    alias-protected.

-   **Frontend fixes SHIPPED + PUBLISHED (Lovable, verified live):**
    money formatters (Meridian \$1.38B was rendering as \$1.38k --- 42
    sites onto formatMoneyM; a09a2ec) · valuation render (equity
    bridge + WACC blanked because page read the analytics-fallback
    partial lacking the deterministic block --- analytics now returns
    it; b3654dc backend + 039ea3f frontend; also value_per_share
    honest-blank \"Add shares outstanding\" + Indicative badge closing
    the de8cfa3 gap) · dataset-resolution (/reports silent-empty from 4
    fail-open paths honoring a stale persisted dataset id vs active;
    fixed centrally in dataset-selection helpers; b14db32) · org-card
    canonical names (no truncation; 7a23c13) · org connector routing
    (spine was drawn through card centres, invisible until the merged
    tree wrapped into multiple rows; parked 12px left of leftmost card
    edge; a66f5f9) · Data Update Wizard \"Review changes\" + \"Revert
    this update\" (carries changeset id, calls /changesets/{cid}/undo;
    25d348f).

-   **H4 validator residuals CLOSED (commit d0b3c9a):** 301 passing / 0
    failed --- the 3 long-standing residuals were all
    intentional-changes-with-stale-tests (auto_forecast 422→201 per
    eb86fbc; simulate horizon cap 10→15 per 8e47a6f; halcyon per-share
    now computed + indicative per de8cfa3), updated to new contracts
    with MORE coverage. First clean baseline in many lanes.

-   **Ask AXIOM cost-control + anonymous demo access (SHIPPED, commits
    9d0467d + 4c2a992 + 3f9ef79):** GLOBAL_DAILY_CAP=90 → guaranteed
    ≤\$98.31/mo worst-case (\~\$40 realistic) --- sizes on COLD-WRITE
    worst case \$0.03524/q, since cache writes bill 1.25× and sparse
    demo traffic is mostly cold. Prompt caching enabled (cache_control
    leading the message array; kept in USER block not system, for
    prompt-injection safety since context carries uploaded-doc excerpts;
    context NOT trimmed --- trimming would break the decline path). Warm
    reads 38-49% cheaper. **Anonymous access DEMO-ONLY**
    (showcase/Meridian company 20): fail-closed \_is_showcase_company
    (any lookup error → treat as access-controlled; failure mode =
    locked-out demo, never exposed customer); real companies reject anon
    (401 --- verified against 25/38/1). Per-visitor cap 6
    (AXIOM_PRESCIENCE_ANON_CAP), conversion prompt on exhaustion (HTTP
    200 + limit_reached body, inline). Visitor key = daily-salted
    SHA256(IP+UA), a FRICTION BUMP not a security boundary (NAT-shared,
    resettable) --- the GLOBAL cap is the real cost guarantee.
    Conversation isolation by visitor_key (fixed: anon user_id=0 could
    otherwise resume a stranger\'s thread). Writes nothing to company
    data; no cross-tenant pivot (company_id path-gated before body read;
    AskBody carries no company id). PENDING: the Ask AXIOM chat FRONTEND
    (covers anonymous demo + magic-link viewer + real member).

-   **PUBLISHED + LIVE + VERIFIED (26 Jul) --- the full frontend queue
    is out:** commits 25d348f · a09a2ec · 7a23c13 · b14db32 · 039ea3f ·
    a51fcb8 · a66f5f9 · 3b016a4 (Ask AXIOM chat frontend) · d88a2d8 (Ask
    AXIOM → persistent top-nav drawer, sub-tab removed) · f46bf1d
    (language dropdown hidden). Verified in incognito: Meridian \$1.38B
    (was \$1.38k), Milliner valuation populated (WACC 13.05% / equity),
    Ask AXIOM working in top-nav (grounded answers + citation chips +
    anon 6-question conversion prompt) and \"impressive\", org canonical
    names + clean connectors, /reports renders, language dropdown gone.
    **The self-serve Prescience showcase is complete + LIVE at the
    guaranteed \$100/mo ceiling.** NOTE: Ask AXIOM tier gating is
    PRESENTATION-ONLY (useAskAccess reads best available signal) ---
    real tier-entitlement enforcement (Business vs Prescience seat
    rights per §4d) does NOT exist server-side, remains the Commercial
    Architecture phase (§4); only COST is bounded, not entitlement.


---

## 4q-item1 Department Dashboard build log

1.  **DONE + LIVE (65501e3 page + 4a9cdf4/c574d4d backend
    alias-resolution + 8133a86 server-side slicing).** Drawer→routable
    deep-linkable page; full view (roster, per-dept CEI slice, L1
    subscores, 13-axis, SWOT slice, KPI variance); reads sentiment ONLY
    from department_slice (trap avoided --- enterprise CEI 6.3716 ≠
    every slice, verified); honest states (CEI-trend/readiness
    enterprise-labeled w/ door; k-suppressed slices; empty→create/link
    door); roster admin-only; cross-company deep-link fails closed.
    **ALIAS FIX (the entangled bug):**
    Participant/AssessmentResponse/AssessmentInvite store department as
    NAME string (VARCHAR 80, not FK). Renaming Meridian\'s depts
    (3f9ef79) orphaned assessment history (responses carry
    name-at-survey-time). Fixed by resolving name→stable-id through
    DepartmentAlias AT READ TIME (frozen history never rewritten).
    Applied to every name-matching read: assessment/summary (slice +
    dept×seniority intersection), sentiment, swot, org-chart sentiment
    map, ?department= filters. Case/whitespace-insensitive, deliberately
    NOT wildcard (over-match would silently merge two depts\' data =
    worse than the bug; test-pinned). Frontend switched roster +
    dept-page from client-side name-filter to ?department=\<id\> (client
    filter DELETED --- leaving it would silently re-impose the bug atop
    the fix). VERIFIED LIVE ON SCREEN (published 26 Jul): filter
    \"Finance and Accounting\" → 3 Finance-tagged assessors
    (Robin/Priya/Marcus) appear (was empty --- the user\'s reported bug,
    FIXED). HR/IT rosters render, CEI slices k-suppressed (1-person =
    privacy, correct). Supply Chain genuinely empty. Suite 320/0.
    **FOLLOW-UP LANE (recorded, not built):** new responses/invites
    should CAPTURE the stable dept_id at write time, making read-time
    alias-resolution a FALLBACK for historical rows rather than the
    primary path (schema + write-path change). Read-time resolution is
    correct + sufficient now. **TABS REBUILD (3389c47, Publish-pending):
    6 tabs (Overview · OKRs & KPIs · Sentiment · SWOT · Stakeholders ·
    Trend & Readiness) --- no scrolling; SWOT/subscore empties were a
    RENDERER field-name bug (title not label), fixed; duplicate
    sentiment column dropped (kept l1_subscores w/
    dispersion+abstention+respondent counts); truncation fixed (wrap not
    w-44 truncate); readiness radar over 6 dims; CEI trend can\'t draw
    until Meridian has 2+ cycles. DEMO-POPULATION ITEM: seed additional
    Meridian assessment cycles so the CEI trend chart renders.
    Per-department trend + readiness = backend follow-up
    (enterprise-only by construction now).** **DEPARTMENT PAGE V2
    (locked 26 Jul --- expansion vision, build in passes):** (1) DROP
    the Overview tab (near-empty --- just accountable head). (2)
    CHARTS-FIRST --- the first tab should lead with visuals to
    impress. (3) NEW TAB ORDER: Objectives & Key Results → KPIs →
    Initiatives & Projects → Stakeholder Sentiment → Trend & Readiness →
    \[others\]. (4) HEADER additions: number of EMPLOYEES
    (per-department headcount) + PARTICIPATION RATE (respondents ÷
    employees). (5) EMPLOYEE HEADCOUNT IS NEW DATA TO COLLECT ---
    decision (user 26 Jul): add an employee-count field per department
    (org-structure template + department model + data-entry flow);
    participation rate derives from it. (6) SWOT with DRILL-DOWN to
    Projects & Initiatives (a weakness → the initiative addressing it;
    the no-dead-ends law). (7) \"More content / more depth\" --- a
    general enrichment pass. NAMING (resolved 26 Jul): trend metric
    STAYS \"CEI\" everywhere (user declined renaming department-scope to
    \"Department Effectiveness Index / DEI\" --- that would collide with
    DEI = Diversity/Equity/Inclusion, sequence item §4r). CEI stays CEI;
    DEI stays free for the diversity feature. **TOP-NAV DEPARTMENT
    SELECTOR (locked 26 Jul):** a persistent department-selector
    dropdown in the top nav (alongside Ask AXIOM) that navigates
    DIRECTLY to the selected department\'s routable page --- universal
    jump-to-department from anywhere. DISTINCT from the §4m Part 1 \"By
    Department\" page-level FILTER (which slices the current page\'s
    panels): the nav selector NAVIGATES to the department hub; the page
    filter SLICES the current page. Reuses the routable dept page
    (navigation, not new page work); lists current company\'s
    departments; inherits Ask AXIOM\'s chrome-free exclusions (not on
    assess/wizard/report); must not crowd header on narrow viewports.
    **SHIPPED (Publish-pending): KPI meters (d03c406 --- fill=actual,
    marker=target, distance=variance; scaled to max(actual,target);
    duplicate KPI/variance panel collapsed to one, redundant fetch
    deleted; direction inferred from name + assumption PRINTED on each
    meter per the variance-direction defect above) + top-nav department
    selector (16f0d99 --- navigates not filters, honest-absent when no
    depts, width-capped).** **DEPARTMENT-PAGE OPEN ITEMS (locked 26 Jul,
    pending build):**

    -   **OKR TAB:** label which rows are OBJECTIVES vs. their KEY
        RESULTS (currently undistinguished); each objective shows its
        2-3 KRs + linked KPIs.

    -   **KPI METER BASELINE BUG:** meter colors against target while
        annotation compares against plan → a KPI at 11 (plan 8, target
        14, \"higher is better\") shows \"+3 vs plan\" (outperformed)
        AND a RED meter simultaneously --- self-contradicting.
        **RESOLVED (user decision 26 Jul): show BOTH plan AND target per
        KPI per department --- NOT one baseline. The fix is to
        DISTINGUISH them, not pick one: \"ahead of plan (+3) but behind
        annual target (11 of 14)\" is a TRUE rich picture, not a
        contradiction. Meter must clearly label both references. PLUS:
        DRILL-DOWN explaining WHY each KPI is out/under-performing ---
        surfaced from CONNECTED data (linked initiatives + their status,
        variance trend, the objective/KR it serves), NOT AI-guessed
        narrative (traceable-or-silent). A KPI is a decision-surface
        node (linked initiatives + objective), not a bare value --- the
        \"why\" = show those connections. Critical for C-suite.** \*\*⚠
        SCHEMA GAP FOUND (b8646b2, 26 Jul): the KPI drill-down \"why\"
        CANNOT be built --- there is NO KPI→initiative link and NO
        KPI→objective link in the schema (KpiPlan carries department_id
        and nothing else relational; Initiative.department_id and
        GoalInitiativeLink exist, but nothing joins a KPI to either).
        Also NO KPI history endpoint (values per dataset version, no
        series). The meter fix SHIPPED correctly (two labeled chips ---
        actual vs plan AND actual vs target --- over one bar w/ both
        markers; resolves the \"green+red\" contradiction). But the
        drill-down honestly shows department initiatives/objectives as
        CONTEXT explicitly NOT claimed to address the KPI (rendering
        them as \"the reason\" would be
        fabricated-explanation-wearing-real-data --- traceable-or-silent
        forbids it). BLOCKER + DECISION: a kpi↔initiative link (+
        kpi↔objective, + KPI history) is a SCHEMA PREREQUISITE for (a)
        the real \"why\" drill-down AND (b) the seeding lane\'s \"each
        objective connected to multiple KPIs\" (Part A) --- CANNOT seed
        a link the model has no column for. So: SCHEMA CHANGE (new link
        table\[s\] + endpoints + template support so uploads express
        KPI↔objective/initiative + a KPI history mechanism) must come
        BEFORE both the drill-down and the seed. PENDING USER DECISION:
        do the KPI-linkage schema change (unblocks drill-down + seed +
        the \"KPI as decision surface\" vision), or defer and seed KPIs
        unlinked for now. **DECISION: DO IT (user chose the
        complete/connected vision). DESIGN APPROVED (26 Jul):** Two
        tables (NOT polymorphic --- objectives key by goal_key
        text-hash, initiatives by stable initiative_id; mirror
        GoalInitiativeLink): ax_kpi_objective_links (company_id,
        kpi_key, goal_key) + ax_kpi_initiative_links (company_id,
        kpi_key, initiative_id), both many-to-many (a KPI serves
        multiple objectives + is addressed by multiple initiatives, and
        vice versa), both UNIQUE, both carrying source
        (\'template\'\|\'in_app\') + flagged_absent (so re-upload
        doesn\'t silently delete in-app links --- the department-delete
        bug class). STABLE KEY: add kpi_key = uuid4().hex to KpiPlan
        (NOT a name-hash --- \"a hash is the name, rename orphans
        everything\" per the re-key lesson) + ax_kpi_aliases
        (name_norm→kpi_key) from day one. **KEYING DECISION (user, 26
        Jul): KPIs keyed on (company_id, DEPARTMENT, normalised name)
        --- a KPI name is DEPARTMENT-SCOPED** (IT\'s \"On-time delivery
        %\" ≠ Operations\' --- name-alone would merge two departments\'
        KPIs = the org-duplication bug again). TEMPLATE: two optional
        columns on the KPI sheet (G \"Serves Objective IDs\", H
        \"Addressed by Initiative refs\"), parser warn-never-block
        (unknown ref → warning + skip link, KPI row still ingests). KPI
        HISTORY: separate, nearly-free once kpi_key exists --- a query
        over dataset versions ordered by uploaded_at, just a read
        endpoint (no new storage; doing it before kpi_key would mean a
        throwaway second identity). RECONCILIATION: mirrors
        \_reconcile_okr_upload verbatim (template-match→update;
        template-absent-was-template→flag not delete; in-app→survives;
        disagree→conflict surfaced, in-app kept; unknown ref→warn+skip).
        MIGRATION SAFETY: link tables = create_all no risk; kpi_key
        backfill = THE dangerous part (same shape as the re-key crash)
        --- resolve identity from in-memory claimed dict NOT per-row
        query (autoflush=False broke that), begin_nested savepoint per
        assignment, oldest-dataset-first so earliest occurrence owns the
        key, DIRTY-DATA test battery (duplicates/blanks/cross-dept
        collisions --- clean tests missed the last crash), deploy
        watched, rollback graceful (column nullable+unused until link
        tables read). SEQUENCE: (1) kpi_key + aliases + backfill
        \[riskiest, alone+watched\] → (2) link tables + reconciliation
        → (3) template G/H + parser → (4) history endpoint → (5)
        frontend drill-down consumes real links (replaces today\'s
        honest \"department context\" note). \*\*STEP 1 DONE (93bbd97,
        suite 333/0): kpi_key + ax_kpi_aliases + backfill shipped.
        Dirty-data battery REPRODUCES the crash (naive per-row loop
        mints 2 keys, commit raises on uq_kpi_alias --- the exact prod
        failure) THEN survives on safe path --- \"a battery that only
        proves the fix works can\'t tell you the fix was needed.\" 10
        cases (cross-dept stays 2, out-of-order versions→1, blanks own
        key, archived keyed, case/whitespace unified,
        idempotent+resumable, companies never share). Dry-run on
        prod-shaped dirt: 6 scanned→3 distinct keys, dept-scoping
        verified. Deploy healthy, Meridian KPI surface byte-identical
        (kpi_key nullable+unread = safety). ⚠ PENDING VERIFICATION:
        backfill POPULATION on prod is UNCONFIRMED (kpi_key serialised
        nowhere in step 1, no read path, sandbox can\'t tail Railway
        logs). CONFIRM VIA: the Railway deploy log line \[kpi-key
        backfill\] {\...} (present w/ counts = ran; absent = didn\'t run
        / nothing to key) OR step 2\'s first resolving link proves keys
        exist. Rollback: nullable+unread, aborted backfill = system
        unchanged, next boot resumes (selects kpi_key IS NULL).
        Correction: battery first posited a NULL kpi_name row --- column
        is NOT NULL, that state can\'t exist --- narrowed to
        empty/whitespace (real spreadsheet dirt). \*\*STEP 1 CONFIRMED
        ON PROD + STEP 2 DONE (b0862a1 + counts endpoint fd15f84, suite
        340/0): prod key-population verified via a new admin counts
        endpoint (logs were unverifiable from sandbox) --- Meridian 24
        rows/24 keyed/0 unkeyed/8 distinct keys (= 8 KPIs × 3 dataset
        versions, proving \"oldest owns key, later inherit\" --- correct
        not just complete); Milliner 111/111/0/33; zero unkeyed
        anywhere. Link tables ax_kpi_objective_links +
        ax_kpi_initiative_links shipped (UNIQUE, many-to-many, source +
        flagged_absent load-bearing). Reconciliation mirrors OKR rule w/
        the critical 4th case test-pinned (in-app link SURVIVES a
        template that omits it --- else every upload silently deletes
        hand-drawn links). Endpoints: read a KPI\'s linked
        objectives+initiatives, create/delete in-app links. Verified
        live on Meridian (link created/resolved/deleted, flagship left
        clean). Details: link rows carry resolvable (goal_key stable but
        objective may be absent from active dataset --- says so vs.
        blank); \_kpi_key_for mints keys for post-backfill in-app KPIs
        (link never points at NULL). UNBLOCKS the real drill-down
        \"why\" --- once Step 3 populates links from template, the
        honest \"department context\" disclaimer comes out and the panel
        shows the actual objective/initiative addressing the KPI. NEXT:
        Step 3 (template columns G/H + parser) → Step 4 (history
        endpoint) → Step 5 (frontend drill-down consumes real links).
        **STEP 3 DONE (f555390, template v7.4, suite 348/0):** two
        optional KPI-sheet columns G \"Serves Objective IDs\" + H
        \"Addressed by Initiative refs\" (reuse existing workbook vocab;
        v7.0-7.3 still accepted). Parser warn-never-block (unknown ref →
        warning + skip that link, KPI row ingests fully, never an
        error). TWO SUBTLE CASES handled: (1) Objective IDs resolve
        against THIS upload\'s objectives not stored ones (else
        reordered objectives silently mislink); (2) SILENCE vs
        DECLARATION --- a v7.4 upload that CLEARS G/H declares \"no
        links\" → flags template links absent; a v7.3 workbook has NO
        G/H → silent → flags NOTHING (else an old-template upload wipes
        every template link in the company). \_template_declares_links
        draws the line, both test-pinned. split_refs module-level (test
        hits the real fn not a copy; accepts
        comma/semicolon/slash/whitespace, case-folds, de-dupes). Chain
        COMPLETE end-to-end: template→parser→reconciliation→link
        tables→read endpoint. Drill-down can drop its disclaimer + show
        real objective/initiative AS SOON AS links exist (workbook G/H
        or in-app). Nothing linked on Meridian yet = a SEEDING matter.
        NEXT: Step 4 (history endpoint) → Step 5 (frontend drill-down).
        **STEP 4 DONE (eb180e8, suite 354/0):** KPI history = a QUERY
        not a schema (KpiPlan always written per dataset version ---
        history was on disk, just had no identity to gather by; kpi_key
        supplies it, no new storage). GET
        /companies/{id}/kpis/{kpi_id}/history → {kpi_key, points,
        sufficient_for_trend, insufficient_reason, renamed_over_time,
        direction:null+note, series:\[per-version
        actual/plan/target/uploaded_at/...\]} oldest-first. Live
        Meridian: On-time delivery % → 3 points (flat, because the 3
        uploads carried identical figures --- honest reading not a bug).
        THREE RESTRAINT CALLS: (1) 1 version → 1 point,
        sufficient_for_trend:false + reason (one reading ≠
        trajectory); (2) direction DELIBERATELY not returned --- no
        polarity column + variance.status is direction-blind, so
        asserting direction would \"launder a guess into the API\"; raw
        series returned, consumer applies the visible/correctable
        on-screen assumption; (3) the GET does NOT mutate --- an in-app
        post-backfill row (no kpi_key, resolves via alias) is included
        explicitly but NOT written back (\"a read that quietly mutates
        is a read you can\'t reason about\"; next boot keys it).
        Robustness: dataset enrichment degrades rather than 500s (series
        stays correct from KpiPlan.uploaded_at if FinancialDataset read
        fails). Alias-resolved (renamed KPI history stays continuous).
        BACKEND CHAIN COMPLETE: template→parser→reconciliation→link
        tables→link reads→history. NEXT: Step 5 (frontend drill-down
        consumes links + history, drops the \"no link exists\"
        disclaimer) --- paired with SEED (Meridian has no links yet).
        **STEP 5 DONE --- KPI LINKAGE CHAIN COMPLETE (9e767db,
        Publish-pending):** drill-down now shows what\'s ACTUALLY
        connected or says plainly nothing is --- objectives the KPI
        measures + initiatives addressing it (each linking onward, each
        with status: a red KPI whose addressing initiative is stalled
        reads as exactly that = the real \"why\"). resolvable respected
        (objective absent from active dataset → \"not in current
        version\" not blank; in-app links marked manual). History as a
        line w/ target dashed reference. Verified live on prod, 3
        states: no-links → \"nothing here explains its
        performance\"+door; with-link → resolves w/ status; history 3pts
        → chart draws. Three honesty rules kept to the frontend:
        single-point draws nothing (states reading, trend at v2);
        direction from the printed card assumption NOT the API (a guess
        in the API is invisible; on the card it\'s contradictable);
        no-links state is NOT the old context-dump (nothing pretends to
        explain a KPI it isn\'t connected to --- the vindication of the
        whole 5-step effort). Perf: links+history fetched on EXPAND not
        page-load (8 KPIs would else fire 16 requests). **FULL CHAIN (5
        steps, each verified on prod before the next): template G/H →
        parser → reconciliation → link tables → link reads → history →
        drill-down.** TWO CARRIED-FORWARD (outside this lane): (1)
        Meridian has NO links populated --- drill-down correctly shows
        honest empty everywhere = the SEED lane (pairs w/ dept OKR/cycle
        seeding); (2) \_kpi_variance.status STILL direction-blind
        product-wide (\"favorable when actual\>=plan\", wrong for every
        lower-is-better KPI) --- dept page works around it (infer+print
        direction); the DURABLE fix = a direction/polarity column on
        KpiPlan captured in the template (§2 defect, pre-launch).

    -   **DEPARTMENT DASHBOARD naming + CXO OVERRIDE at department scope
        (locked 26 Jul):** the department page IS the department\'s
        \"Department Dashboard\" (spelled out --- parallels the
        enterprise Dashboard & Reports without a bare-\"Dashboard\"
        clash). The CXO OVERRIDE & SIGN-OFF (§4l --- CXO Dashboard
        Control & Sign-off, spec AXIOM_CXO_Signoff_Build_Spec.md)
        APPLIES AT THE DEPARTMENT LEVEL: each CXO can override/adjust
        THEIR OWN department\'s Dashboard (show/hide/add KPIs, adjust
        values, set RAG, sign off) --- the CHRO owns HR\'s Dashboard,
        the CTO owns IT\'s, etc. This is NOT a separate mechanism --- it
        is §4l applied at department scope. The §4l discipline carries
        in FULLY: immutable-computed-truth (computed value NEVER
        destroyed), override is an ATTRIBUTED layer shown BESIDE the
        computed value with visible \"adjusted by \[CXO\]\" authorship
        (so CEO/board can always tell computed from adjusted --- not
        number-laundering), reason-routing, re-sign-off on new data. So
        the Department Dashboard is both a VIEW and a CXO-controllable,
        signed-off surface.

    -   **DEPARTMENT SWOT → MATCH ENTERPRISE SWOT (locked 26 Jul):** the
        department SWOT is currently a flat 4-column text list (image);
        the ENTERPRISE SWOT is a proper 2×2 quadrant grid
        (Strengths/Opportunities top, Weaknesses/Threats bottom),
        axis-labeled (INTERNAL/EXTERNAL · HIGH/LOW SCORE), with context
        annotations, warning affordances, honest per-quadrant empty
        states (\"Nothing in this quadrant yet\"), AND
        clickable/ACTIONABLE items. Make the department SWOT match the
        enterprise SWOT\'s DESIGN and BEHAVIOR --- ideally REUSE the
        enterprise SWOT component scoped to the department (don\'t
        maintain two divergent SWOT renderers; the department one is the
        poor cousin). CRITICAL: department SWOT items must be
        CLICKABLE + ACTIONABLE exactly like enterprise (this is also the
        SWOT-drill-down-to-Projects/Initiatives item already noted --- a
        weakness → the initiative addressing it; no-dead-ends). Verify
        what \"actionable\" does on the enterprise SWOT
        (adopt→initiative? disposition? drill to linked initiative?) and
        carry the SAME behavior, department-scoped. **DONE (6c7e0c6,
        Publish-pending):** turned out to be a DELETION not a port ---
        LiveSwot (routes/swot.tsx) already took a department prop,
        fetched /assessment/swot?department=, handled suppression,
        rendered the 2×2. Department page was hand-rolling a flat list
        BESIDE it. Fix: exported LiveSwot, pointed dept tab at it,
        deleted the hand-rolled version + its duplicate fetch. One
        renderer, two call sites (enterprise + department) --- can\'t
        drift. Clicking a tile → EvidenceDrawer with drill-downs:
        item→stakeholder-engagement, contributing→readiness, LINKED
        INITIATIVES→/initiatives?open=\<ref\>, or when none linked
        \"Create initiative from this\"→/initiatives?create (= the
        SWOT→Projects drill-down, no-dead-ends, per department).
        Inherits seniority filter too (dept×seniority via
        intersection_slice). Non-change flagged: LiveSwot lives in a
        route file (not tidiest home) --- extracting would touch
        enterprise page for no behavioral gain, deferred to whenever
        that file is opened anyway.

    -   **CEI DISPLAY AT ORG LEVEL (locked 26 Jul):** show CEI scores
        where the org is seen --- (1) the ENTERPRISE page shows overall
        enterprise CEI + each department\'s CEI; (2) ORG STRUCTURE
        department CARDS show each department\'s CEI score (org chart
        becomes a CEI heat/sentiment map). NOTE: org-chart already has a
        sentiment-map + RAG-band wiring (the alias fix touched it) ---
        verify what exists vs. surfacing the CEI NUMBER on cards.
        DEPENDENCY: only fully populated once the seed (below) gives
        EVERY department a real CEI (today only
        Finance/IT/Operations/Sales have one; HR k-suppressed, Supply
        Chain empty) --- SEED before DISPLAY or the org chart shows
        blanks.

    -   **FULL MERIDIAN SEED (locked 26 Jul, flagship rule ---
        supersedes the simpler \"seed cycles\" item):** TWO LANES. LANE
        1 (backend prerequisite): per-department CEI TREND + READINESS
        are enterprise-only by construction (trend reads
        snapshot\[\"cei\"\]; \_show_slice strips departments; readiness
        assessment_summary(department=None) hardcoded accounts.py:8336)
        --- build them sliceable-by-department from cycle history w/
        k-floor. **LANE 1 DONE (0ba3095):** history is RECOVERABLE not
        forward-only (my \"\_show_slice strips departments\" flag was
        wrong in our favour --- it strips only a nested slice at
        serialization; stored snapshots retain full per-dept breakdown
        snapshot\[\"departments\"\]\[name\]{cei,n,subscores,radar}; AND
        AssessmentResponse rows retained per cycle tagged by dept =
        recomputable anyway --- two routes). Trend takes ?department=,
        reads stored breakdown alias-resolved, skips cycles w/o the
        dept, tags scope enterprise\|department. Readiness slices by
        dept w/ the HONEST fix (axis means AND cei from
        department_slice, not enterprise top-level --- else a dept\'s
        readiness computes from enterprise numbers and looks plausible =
        the silent-wrong trap). K-floor per department-CYCLE point (on
        the slice\'s own n, never the cycle total --- a 30-cycle w/ a
        2-person dept must not publish the pair; test-pinned; HR
        n=0→None live). **⚠⚠ PIVOTAL SEED-DESIGN CORRECTION (measured on
        Meridian): department CEIs DO NOT and CANNOT aggregate to the
        enterprise CEI. Measured: visible-slice weighted mean 6.3411 vs
        enterprise 6.3716 (Δ0.0305). TWO structural reasons: (1)
        k-floored slices (HR+Supply Chain\'s 5 respondents) are IN the
        enterprise number but IN NO visible slice --- averaging visible
        slices averages 25 of 30 people; (2) CEI is a weighted mean of
        AXIS means (pooled over who answered each item), not a mean of
        respondent scores --- with uneven per-dept item coverage +
        abstentions, enterprise axis mean ≠ mean of dept means. So the
        ORIGINAL seed constraint (\"dept trajectories that aggregate to
        6.3716\") is MATHEMATICALLY UNSATISFIABLE; forcing it =
        fabricating the enterprise number. CORRECT SEED APPROACH:
        generate per-RESPONDENT responses per cycle tagged by
        department, let compute_cei DERIVE both enterprise + dept
        figures. Shape the INPUTS to give each dept the trajectory
        (rising/flat/declining); the enterprise series falls out as
        whatever those inputs imply --- consistent BY CONSTRUCTION
        because computed like real data. Writing snapshots directly =
        faster but \"reconstructed-and-wrong\" (history that doesn\'t
        reconcile with its own inputs). Resolves the \"latest cycle
        stays current\" constraint: leave cycle 37 + its responses
        UNTOUCHED, seed only EARLIER cycles --- current enterprise CEI
        stays 6.3716 (same responses), every dept slice unchanged,
        history added BEHIND the present.** LANE 2 (seed, after Lane 1
        --- NOW via responses not snapshots): **STEP A STAGING DONE
        (af6573e + da17c47, suite 363/0) --- caught a real defect (why
        staging existed):** first dry run derived 5.869 vs target 6.30
        (0.43 miss) --- NOT transform bias, SAMPLING: zero-mean offsets
        don\'t CANCEL at n=5 (harshness SE \~0.16; item offsets are
        SHARED across the dept so never average out over respondents ---
        a fixed displacement of the whole profile). A 0.43 miss turns
        \"flat\" into visible \"decline\" --- plausible-but-false, the
        exact failure mode. FIX: centre both offset sets on their
        REALISED mean (dept average lands on target, respondents/items
        stay as varied --- \"variation makes it look real, the mean
        makes it true\"). After: mean delta +0.002, worst +0.049 (40
        seeds, n=5). The unit test asserted mean-hits-target over 200
        respondents (passed) --- error only appears at the n=5 the seed
        actually uses (same lesson as clean-tests-missed-the-crash: test
        at production scale). Verified: Operations derived 6.3355 vs
        target 6.30; cycle 37 UNPERTURBED (6.3716, n=30, all slices
        identical, only cycle_count 1→2); showcase gate 403s real
        tenants + fail-closed; idempotent (re-run wrote 0). STEP B
        ADJUSTMENTS (from review): (1) build UNSEED path FIRST before
        the full write (a 7,800-row write with no reverse is worse than
        390 standing); (2) \~4-5 respondents PER DEPT per cycle
        (\~30/cycle, matching cycle 37\'s scale so participation reads
        STABLE not \"grew 6×\"; margin above k-floor for HR/Supply Chain
        to appear). Trajectories: Finance rising, Operations flat, IT
        declining (tech-transition), Sales rising, HR
        rising-from-suppressed, Supply Chain flat-from-suppressed, Exec
        flat; enterprise series FALLS OUT (never targeted). OKRs/KPIs =
        direct in-app inserts (not template re-upload --- would replace
        active dataset); links via endpoint (source in_app, survive
        re-uploads). \*\*UNSEED DONE (14eb8b4): \"names select,
        structure decides\" --- a cycle deletes only once EVERY response
        confirms the synthetic seed: prefix (refused cycle 37 by
        structure: 2340/2340 NOT synthetic; can\'t be removed even when
        named). Round-trip clean on prod (staged cycle removed,
        6.3716→6.3716, slices identical). Bug caught: .first() on name →
        half-unseed looks clean; now handles all matches. include_okrs
        extends the created_by_name marker. B1 RESPONSES DONE (f4db9b5,
        12,090 rows / 5 cycles): all 7 trajectories landed as specified
        (worst \|derived−target\| = 0.083 across 35 dept-cycles ---
        centred fix holds at scale); enterprise series FELL OUT
        (6.147→\...→6.372 real, coherent improving story, not targeted);
        31/cycle vs 30 real = stable participation; cycle 37 UNPERTURBED
        (slices unchanged, cycle_count 1→6); reversible. **⚠ K-ANONYMITY
        DEFECT EXPOSED BY SEEDING + FIXED (a real privacy leak, was LIVE
        in prod, introduced in Lane 1):** department slices are an EXACT
        PARTITION of respondents --- if only ONE is hidden, its value is
        derivable by subtracting shown slices from the enterprise total.
        The scorecard\'s \_partition_status already suppresses the
        smallest shown slice until 2+ are hidden; but the Lane-1 TREND
        applied only the primary n\<KFLOOR floor → published a value the
        summary withholds. Meridian cycle 37 is exactly that shape
        (Supply Chain n=2 below floor forces HR n=3 hidden too) ---
        trend showed HR 6.72 while scorecard correctly showed None.
        FIXED, fails closed, verified (HR now suppressed). FOUND BY
        SEEDING NOT REVIEW --- 5 synthetic cycles put a dept exactly at
        the floor beside one below it, two surfaces disagreed; the kind
        of defect invisible until real data takes that shape. LESSON:
        seeding the flagship doubles as a fuzzing pass that surfaces
        latent edge-case bugs (esp. k-anonymity partition leaks) before
        real customer data hits them. \*\*B2 DRY-RUN caught another
        defect (why dry-runs exist) → DIRECTION COLUMN DECISION (26
        Jul): the plan (objectives top-up to 3/dept, 42 KPIs
        GREEN11/AMBER18/RED13, 12 lower-is-better above target = red) is
        good, BUT testing the planned realistic CFO KPI NAMES against
        the frontend\'s keyword direction-heuristic → 4 of 8
        MISCLASSIFIED (\"Audit findings open: 5 vs target 2 → GREEN\" =
        confidently-wrong, worse than nothing; keyword list has no entry
        for variance/findings/failure-rate/payback and no principled
        list could --- KPI name space is open). DECISION: option (a) ---
        ADD THE DIRECTION COLUMN FIRST, then seed with STATED
        directions. One direction column on KpiPlan, honored by
        \_kpi_variance (FIXES the product-wide backwards-variance defect
        §2 at the source), set explicitly by the seed AND by the upload
        template (new column I). Removes the guess entirely --- the
        infer-from-name heuristic goes away. ONE column resolves FOUR
        things: the seed\'s correct colors + the product-wide
        \_kpi_variance bug + the dept-meter\'s inference + real
        customers stating direction. (Options b/c rejected --- both
        design around the bug.) Also: Operations/HR/Exec have no
        initiatives → recommend seeding 1-2 initiatives per dept
        (flagship full-glory; linking company-level A4/A5 dept=None
        would be mildly dishonest). SEQUENCE NOW: direction-column lane
        (column + \_kpi_variance fix + template col I) → then commit B2
        seed with directions stated → then B2 verify. \*\*DIRECTION
        COLUMN SHIPPED (e496444 backend + db23ded frontend, suite
        379/0): product-wide \_kpi_variance defect FIXED AT SOURCE
        (Unplanned downtime 101 vs plan 95: FAVORABLE→unfavorable; fixed
        on dashboard/reports/dept page alike; abs+pct stay signed ---
        magnitude is direction-independent, only the verdict flips).
        KpiPlan.direction (higher_better\|lower_better) DEFAULTED not
        nullable (higher_better = how rows were already treated → no
        backfill, none of the identity-crash shape). Template v7.5 col I
        optional (blank=higher; normaliser accepts
        lower/minimise/down/min...; unrecognised warns+falls back not
        fails; blank = silent per pre-v7.5; 7.0-7.4 parse); wired
        through create/update_kpi too. FRONTEND got the key distinction:
        keyword heuristic SURVIVES ONLY as fallback for pre-v7.5 rows
        (dropping it = silently calling every old KPI higher-better =
        same bug in a new coat); and the basis DISTINGUISHES fact from
        guess --- stated shows \"lower is better\", inferred shows
        \"lower is better (inferred)\" (\"a fact from the upload and a
        guess from a keyword shouldn\'t look identical to the person
        deciding whether the red bar is real\" = traceable-or-silent at
        its finest). ⚠ PROCESS LESSON: pytest \| tail -2 && git commit
        MASKS pytest\'s exit code → a red test committed anyway
        (0b75f9b, benign stale TEMPLATE_VERSION assertion, fixed).
        DON\'T pipe pytest before a conditional commit --- the pipe
        swallows the failure. B2 SEED READY: same plan (42 KPIs, RAG
        targets, links) with polarity now DECLARED not guessed; re-run
        dry-run showing corrected bands for approval, then commit. **⚠
        KNOWN BUG (diagnosed-not-fixed, for next session --- the \"two
        surfaces, one concept, divergent computation\" class again):**
        the ORG CHART objective-status BORDER color and the DEPARTMENT
        PAGE average-attainment RING color DISAGREE for the same
        department. Measured: Finance & Accounting = org-chart border
        YELLOW (Mixed) vs dept-page 40% RED; Human Resources = org-chart
        border GREEN (On track) vs dept-page 46% YELLOW. Likely cause:
        the org chart classifies by DISTRIBUTION (On track / Mixed / At
        risk / No objectives = the spread of objective statuses) while
        the dept page rings by AVERAGE ATTAINMENT % → RAG bands. Both
        legitimate but they answer different questions, so they disagree
        (a dept with one strong + one weak objective is \"Mixed\" by
        distribution but \"Red\" by average). DECISION NEEDED before
        fix: what should objective-status COLOR mean --- average
        attainment (advisor\'s lean: more honest at-a-glance --- a dept
        averaging 40% IS at risk, \"Mixed\" undersells it) or
        distribution? Then make BOTH surfaces use the ONE rule.
        NEXT-SESSION FIRST ITEM. \*\*RESOLVED + DONE (798e0b1 backend +
        0cdfa68 frontend, user chose AVERAGE ATTAINMENT): the two
        surfaces differed by MEANING not thresholds --- org chart read
        counts.rag (distribution of hand-entered Objective.status
        labels), dept page read mean of measured KR attainment. Fixed at
        SOURCE not display: /departments now computes counts.attainment
        through the SAME \_objective_rows+\_kr_progress path the ring
        uses (a shared frontend helper over the two old inputs would\'ve
        looked unified + still disagreed). Canonical
        objective_status_band: green ≥0.70 / amber ≥0.40 / red \<0.40.
        FOUR states: none→grey, unscored→grey-separately-labelled
        (unmeasured ≠ failing; but measured 0% stays red so unscored
        isn\'t a hiding place), green/amber/red. Verified all 7 Meridian
        depts: border color == ring color, ZERO mismatches (dept column
        recomputed independently). Finance 0.3988 correctly red;
        percentages now FLOOR not round (Math.round showed \"40%\"
        contradicting its red band --- flooring can\'t overstate
        attainment). DEFINITION SHOWN: legend now names the measure +
        bands (was just \"objective status\" --- that\'s how two
        surfaces counted different things unnoticed); + a follow-up
        shows it on the dept page near the ring too. Incidental fixes:
        ragBand() was dead code (never called, drawer never showed a
        band); \_dept_counts ran its own db.query(Objective) missing
        archived-drop + legacy-OrgGoal fallback (chart counts described
        a different row set than the page). Backend live; frontend
        Publish-pending. **CAPTION DONE (f5bada3): definition + bands
        under the ring, band named beside figure (\"41%\"→\"Mixed ·
        across 1 of 3 objectives\"); two greys named apart with NO arc
        drawn (zero-length arc reads as 0% which unknown isn\'t entitled
        to); word-for-word match ENFORCED (ATTAINMENT_DEFINITION/BANDS
        exported, one string both surfaces). f5bada3+0cdfa68 sequential
        = one Publish carries both. #1 COMPLETE pending Publish.**
        \*\*B2 SEED COMMITTED + VERIFIED (flagship fully populated): per
        dept 3 obj / 6 KR / 6-8 KPIs / 1-2 initiatives / mixed RAG
        (Finance 1/2/4, Ops 4/2/2, IT 1/2/4 \[tech-strain story\], Sales
        1/4/2, HR 2/4/1, SupplyChain 2/3/2, Exec 1/3/2). RAG via STATED
        direction (lower-better inverts --- latency/P1 red on
        overshoot). Named drill-down passes end-to-end: P1 incidents →
        \"Launch platform v2\" objective + initiative A3; Mean latency →
        same obj + A7 (the KPI-as-decision-surface vision realized with
        coherent data --- IT\'s story consistent across
        trend/KPIs/objectives). Cycle 37 unperturbed. Fully reversible
        (unseed = exactly B1+B2: 5 cycles/12,090 responses/11 obj/41
        KPIs/82 links; refuses cycle 37; showcase-gated 403 on
        Milliner). BUG CAUGHT + FIXED (083deec):
        department.\$deptId.tsx (1) dropped null gap points via .filter
        → drew a continuous line across k-suppressed gaps (\"a story
        that never happened\") and (2) labelled a genuinely
        department-scoped series \"enterprise-wide\" (series became
        dept-scoped in b37a4d9; page never learned). Fixed: line breaks
        at nulls, gaps named w/ backend\'s sentence, caption read from
        payload scope. ⚠ 083deec + department page + Ask AXIOM + KPI
        meters are PUSHED NOT LIVE --- need a Lovable Publish. Crawler
        on live bundle: anon 16/17, operator 45/52 (pre-existing
        failures are separate lanes). THE DEPARTMENT-PAGE ARC IS
        ESSENTIALLY COMPLETE --- flagship demo-ready pending Publish +
        the org-chart-color decision (next-session first item). each
        Meridian department gets MULTIPLE objectives (2-3), each
        objective 2-3 KEY RESULTS + linked to MULTIPLE KPIs, 6-8 KPIs
        per department in aggregate spanning green/amber/red (respecting
        direction), AND a multi-cycle (4-6) CEI history with
        DELIBERATELY VARIED trajectories across departments (some
        increasing, some flat, some decreasing --- believable, gentle,
        not straight/random). CONSISTENCY NON-NEGOTIABLE: department
        slices must AGGREGATE to enterprise CEI each cycle; latest cycle
        stays Meridian\'s real current state (enterprise 6.3716); no
        implied respondents/departments that don\'t exist. An
        internally-inconsistent seed is WORSE than empty (sharp buyers
        spot it).


---

## 5. INCIDENT LOG (seam-bug era, CLOSED 21 Jul)

**5. INCIDENT LOG (the seam-bug era --- CLOSED 21 Jul)**

**Theme: every launch-blocking bug lived at the accounts-world ↔
legacy-identity seam, and none was reachable by anonymous
verification.** Email is the ONLY reliable cross-world join key (the two
/me endpoints return different ids for the same human). Unified identity
resolver = post-launch refactor candidate.

1.  **Masquerading-500 / CORS (commit 99e0604 + Railway var).**
    Unhandled 500 (account.id on None, FP-1 regression 2d2ef0f) escaped
    Starlette outside CORS middleware → browser showed CORS block.
    Fixed: None guard + catch-all handler re-attaching ACAO on 5xx +
    AXIOM_ALLOWED_ORIGINS lockdown (hardening item DONE).

2.  **read_tenant showcase carve-out (Option A, cf3088a).** Signed-in
    sessions landed in empty private tenants; showcase only reachable
    anonymously. Fix: only the SHOWCASE alias honored from header when
    authed; demo stays anonymous-only. Claude Code\'s frontend
    investigation prevented the original approved fix from silently
    breaking future own-company reads (frontend hardcodes
    X-AXIOM-Tenant: demo everywhere). Frontend: currentTenant() sends
    showcase only for token+showcase-company contexts.

3.  **platform_role reader gap + /me shape (05a6f1e + Lovable
    normalize).** Setter existed, no reader; then flat-vs-{user:}
    envelope mismatch kept isSuper false. Fixed both ends. \"Operator
    admin\" link existed in AuthMenu all along, strangled by the gate.

4.  **enterprise_state auth-blind tenant (6298f1a) + ROUTER AUDIT.**
    enterprise_state/learning/risk/optimization/simulation used
    auth-blind tenant_from_header → signed-in operator saw demo
    tenant\'s companies, Milliner invisible → Data-Input crash +
    report-gen \"failure\" (downstream). All 5 swapped to read_tenant;
    dead imports stripped from the rest so the anti-pattern can\'t
    rewire. Anonymous /api/v1/enterprises now returns showcase (was ABC)
    --- accepted consistency change. Milliner PDF/PPT generate fine
    post-fix.

5.  **Admin first-light crash.** f.map on {pilots:\[\...\]} wrapper when
    the gate opened for the first time ever. Fixed + GLOBAL asArray
    normalization across 12 route files (third instance of the class →
    app-wide policy).

6.  **http:// redirect mixed-content (infra, pre-existing).**
    Trailing-slash 307s carried http:// Locations (uvicorn didn\'t trust
    Railway\'s TLS edge) → \"Failed to fetch\" for any slash-normalizing
    client. Fixed via Railway env var FORWARDED_ALLOW_IPS=\* --- **the
    Procfile is NOT authoritative on this service (Start Command
    overrides it); env vars are the lever for start flags.**
    User-visible education errors were the transient deploy-restart
    window.

7.  **Phantom GET /companies/{id}.** The data-input default tab called
    an endpoint that never existed (silently swallowed 404 since day
    one; crawler was the first observer). Fix approved: real endpoint
    gated by require_company_member (viewers included --- read-only
    summary). \[verify on Claude Code\'s report\]

8.  **Claude Code over-broad cleanup disclosure:** a test-report cleanup
    deleted Milliner\'s 2 pre-existing report issues + blobs
    (unrecoverable); regenerated functionally-equivalent set. → New
    discipline: cleanup deletes scoped to exact created ids only.

**Minor fixed en route:** pilot status snake_case/label mismatch
(backend accepts both) · roles form sends email→id lookup (never raw
strings in URLs) · logout 404→correct route + clearSession guarantee ·
/billing/success anon guard · scenario-analysis 404 silenced · login
console debug stripped · Railway hostname removed from sidebar.

**THE CRAWLER (standing verification):** scripts/auth-regression.py ---
enumerates all routes (92), modes anonymous/operator/(member when
account exists), primes localStorage\[\'axiom.auth.token\'\], HARD
sanity gate (asserts Authorization actually sent + /me 200 or aborts),
per-failure inline console messages + non-2xx URLs, sidebar-presence
assertions per mode. Baseline: 91/92 green on bundle index-CcEtBthz.js
(the 1 = phantom endpoint, fix in flight). **Replaces hand-clicking
after every build. Runs after every deploy. Member mode switches on when
the f4 test account is created. Rotate the operator token after each
run.**
