# AXIOM — ONBOARDING FOR A FRESH ADVISOR

**Written 1 Aug 2026. Assumes no conversation history, no memory, no context.**

`AXIOM_LEDGER_CORE.md` records **what was ruled**. This file records **how the
work is done**. Read this one first; it is shorter, and it tells you how to read
the other.

> ⭐⭐ **THIS DOCUMENT IS A RECOVERY DOCUMENT, AND A RECOVERY DOCUMENT THAT GOES
> STALE IS WORSE THAN NONE — because it will be trusted.** If you change a
> practice, change it here in the same lane. See *Keeping this current*, last
> section.

---

# 1 · WHAT AXIOM IS

**A financial and strategic analysis platform for mid-market companies.** It
takes a company's own financial statements, organisational structure, planning
documents and employee assessment responses, and produces a defensible account
of **what created enterprise value, what is at risk, and what to do next** —
delivered as a **board-grade pack**.

## The leading question

> *"You know what created value last year. **Can you rank it?**"*

⭐ And the question a CFO asks the moment they take it seriously:

> *"**How would you know?**"*

⭐⭐ **THAT SECOND QUESTION IS WHERE THE MATHEMATICS EARNS ITS PLACE.** A ranked
value decomposition is worth having **only if the ranking is defensible.**

⭐ **THE RIGOUR IS THE WARRANT FOR THE CLAIM, NEVER THE CLAIM ITSELF.** Do not
write copy that sells the method. Sell the answer; let the method be
inspectable. *"No other software gives you that"* was ruled **inadmissible**
because it is unverifiable.

## The target market — ruled

> ⭐⭐ **ONE THOUSAND MID-MARKET FIRMS USING AXIOM CONSISTENTLY AND SATISFIED.**
> **Not 100,000. Not the Fortune 500.**

This is a **commercial goal that binds engineering**, and it settles arguments
that would otherwise recur:

| ruled out | because |
|---|---|
| enterprise procurement motion | a thousand firms is not reached through 18-month procurement cycles |
| self-serve long tail | that is the 100,000 number, and it is not the goal |
| per-seat land-and-expand | **the buyer is the company, not a department budget** |

⭐ It binds engineering too: at a thousand firms the **unattended monthly sweep
is itself an untested load**, which is why load testing is a launch gate.

## The two tiers

| | monthly | annual |
|---|---|---|
| **AXIOM Business** | **$4,995 / company** | $59,940 |
| **AXIOM Prescience** | **$11,995 / company** | $143,940 |

⭐⭐ **FLAT PRICE PER COMPANY, UNLIMITED USERS, ONE COMPANY PER WORKSPACE.**
Never "per seat." Annualised, AXIOM sits **mid-band on price** against the ten
FP&A platforms in the comparison matrix — ⭐ **unlimited users is the
difference, not cost**, which is why the Users row sits *above* price in the
matrix. Leading with price would make the one claim the numbers do not support.

**Gating:** Business includes all core product plus **Ask AXIOM only** from the
Prescience layer. **Prescience-only:** Multiverse, Resilience Field, Causal Map,
Radar/Sentinel, Prescience Brief. ⭐ Of those five, **only Radar/Sentinel is
built** (measured against the served route table, not a status column).

## The customer journey — twelve steps (§4z)

| # | step |
|---|---|
| 0 | Arrive — leading question, brochure, comparison matrix, referral |
| 1 | View the live demo — **public and unauthenticated** |
| 2 | Receive two templates — financial and organisational, participants at 3–5 per department |
| 3 | Submit templates and business planning documents |
| 4 | ⭐⭐ **The assessment runs** — participants respond, the cycle closes |
| 5 | Scheduled call — view results |
| 6 | Submit the viewer list |
| 7 | Invited viewers explore their own data — 30 days, read-only, opens logged per person |
| 8 | Discuss internally, decide |
| 9 | Register and purchase |
| 10 | Activation with support — pilot data transfers |
| 11 | Walkthrough of ongoing use |
| 12 | ⭐⭐ **The first pack publishes on the 5th** — the CEO releases it to the board and the lender |

⭐⭐ **STEP 4 AND STEP 12 WERE BOTH MISSING FROM AN EARLIER DRAFT AND BOTH ARE
LOAD-BEARING.**

- **Step 4's elapsed time belongs to the CLIENT**, and their obligation is
  getting people to respond. Omitting it makes the journey look faster than it
  is and ⭐ **hides the dependency** — a journey that conceals whose step it is
  sets up the failure to read as ours.
- **Step 12 is where AXIOM becomes difficult to cancel** — not through
  cleverness, but because **someone outside the company now expects the pack.**
  ⭐ A journey that stops at step 9 describes a sale, not a customer.

**The pilot runs on Prescience.** A client buying Business loses forward-engine
surfaces they were shown for 30 days. ⭐⭐ **STATED UP FRONT THIS IS AN UPSELL;
DISCOVERED AT CHECKOUT IT IS A BAIT** — the same fact, and only the timing
decides which. Required in three places: the results call, the viewer
experience, the pricing page. **Only the viewer experience is built.**

---

# 2 · THE TWO-LANE CUSTODY MODEL

Three parties. **Mixing them makes two of them fight over one file.**

| party | owns | does not |
|---|---|---|
| **this chat (advisor)** | advises, rules, routes, writes dispatches | never edits code |
| **Claude Code** | ⭐ **backend, data, tests, guards, all verification, and the ledger** | does not do visual/copy design |
| **Lovable** | ⭐ **frontend presentation — layout, visual design, copy rendering** | ⭐ **does not audit, and does not verify** |

## Why the audit owner is Claude Code, never Lovable

Recorded because **routing corrections become policy**. Three reasons, each
grounded in an actual failure:

1. ⭐⭐ **LOVABLE IS A GENERATIVE ENVIRONMENT — ASKED TO CHECK, IT EDITS.** An
   audit must produce a truthful list, not begin remediating. **A tool that
   repairs what it finds cannot tell you what it found.**
2. ⭐ **LOVABLE REPORTS ON SOURCE, NOT THE SERVED BUNDLE.** A publish stall
   proved source-correct and served-wrong coexist happily while every ordinary
   check passes. ⭐⭐ **ONLY THE SERVED BUNDLE IS TRUTH.**
3. ⭐⭐ **IT WOULD BE ASSESSING CODE IT WROTE, IN THE ENVIRONMENT THAT WROTE
   IT.** Every measurement error of one bad day came from **an instrument
   reporting on itself.**

**Lovable's role is remediation, after.** Visual and copy defects found by an
audit route to Lovable as a **separate lane**.

## The practical consequence you will hit

⭐⭐ **LOVABLE PUSHES DIRECTLY TO `optimization-anchor/main` ON ITS OWN
SCHEDULE.** A recent session found the local checkout **38 commits behind**,
including a 414-line rewrite of a component a Claude Code lane had built.

**What to do:**

- **Always shadow-check before a lane** (see §3). Measure `ahead` and `behind`
  separately.
- ⭐ **`behind: N, ahead: 0` IS NOT A COLLISION** — it is a stale local, and a
  fast-forward is not a resolution. Verify with
  `git merge-base --is-ancestor HEAD origin/main`.
- ⭐ **`ahead > 0` AND `behind > 0` IS A COLLISION. Surface it. Never
  auto-resolve.**
- ⭐ **Expect the frontend gates to be RED ON ARRIVAL** after Lovable pushes.
  Formatting normalisation is mechanical and fine; **content reconciliation is
  the user's call.**
- ⭐ Do not write frontend *presentation* in a Claude Code lane unless the lane
  says so. Wiring, route registration, data shape and assertions are Claude
  Code's; **visual design is not.**

---

# 3 · HOW A LANE RUNS

## The invariant shape

1. **Read `AXIOM_LEDGER_CORE.md` first.** Every session, no exceptions.
2. **Shadow check** — both repos: last commit, `git status`, `ahead`/`behind`,
   `git stash list`.
3. **One lane at a time.** The dispatch names it.
4. **Every session ends with a pushed `origin/main` and a reported commit hash.**
5. **Record in CORE as part of the lane**, not afterwards.

```bash
# shadow check
cd /Users/samirasaf/dev/axiom && git log --oneline -1 && git status --porcelain \
  && git fetch -q origin && git rev-list --count HEAD..origin/main
cd /Users/samirasaf/dev/optimization-anchor && git log --oneline -1 \
  && git fetch -q origin \
  && echo "ahead $(git rev-list --count origin/main..HEAD) behind $(git rev-list --count HEAD..origin/main)"
```

`scripts/lane-env.sh` fetches environment for a lane — **one fetch per lane, and
the URL is never printed.**

## Verification commands

```bash
python3 -m pytest tests/ -q                       # full suite, ~3m20s
for f in scripts/check-*.py; do python3 "$f" || echo "FAIL $f"; done   # 29 gates (5 Aug)
```

⭐ **Run the gate loop in the background.** A foreground 10-minute timeout has
killed it mid-run four times.

### ⛔⭐⭐ A BROWSER PROOF MUST NAME ITS ORIGIN, OR IT PROVES NOTHING ABOUT THE PRODUCT

**Every browser proof reports the ORIGIN it ran against, beside its result.**
Not the path — the **host**.

⛔ **"On the URL a reader takes" does not specify a host, and is satisfied by
`localhost`.** That phrasing has stood in dispatches all week and a localhost
proof satisfies it completely — which is the defect. **A localhost proof is a
statement about the TREE. Only a proof against the served host is a statement
about the DEPLOY.**

| what ran it | default origin | what it can prove |
|---|---|---|
| **`browser-verify.py`** — the CI browser gate | **`localhost:3000`**, and `APP_URL` is **never set** anywhere | **the tree only**, on the **nitro** build |
| `auth-regression.py` (both copies) | **the served host** | the deploy |
| `proxy-sweep.py` | the served host | the deploy |
| `crawler-login.py` | `localhost:4175` | the tree |

⭐⭐ **AND THE TWO BUILDS ARE NOT THE SAME ARTEFACT.** `build:preview` produces
the **nitro** target (`/_build/assets/*`); the deployed product is a **Vite SPA**
(`/assets/*`) with different chunking. Two targets from one tree. On 7 Aug they
agreed — **by luck, not by construction**, and a lane cited a localhost proof as
evidence about the deploy.

⛔ **So report it like this:** *"browser proof, incognito, origin
`localhost:3000` (nitro `build:preview`)"* — or name the served host. A result
with no origin is not a proof, and **the reader cannot supply the missing half.**

Frontend (`export PATH="$HOME/.bun/bin:$PATH"` first — `bun` is installed but
not on the default PATH; a lane once concluded "no JS runtime" and queued unneeded
work on that false measurement):

```bash
bunx tsc --noEmit && bun run lint && bun run build
bun scripts/check-routetree.mjs      # the committed route tree must stay LOOSE
```

⭐ **`vite build` REWRITES `src/routeTree.gen.ts` into a STRICT variant that
breaks typecheck in ~80 untouched files.** Copy the loose tree aside before
building and restore it after. `check-routetree.mjs` exists to catch a
regenerated tree being committed.

---

# 4 · HOW A DISPATCH IS WRITTEN

These are **instructions**, not history. Each exists because its absence cost
something.

## Measure before building

⭐⭐ **NEVER BUILD FROM A LEDGER LINE ALONE.** CORE has been found wrong **twelve
times** — twice false when written, and the rest where the record trailed the
code. Four of those invited **rebuilding working software**.

> ⭐⭐ **A STALE LEDGER LINE DOES NOT MERELY MISINFORM. IT ISSUES INSTRUCTIONS.**

**In a dispatch:** say *what to measure* before saying what to build. If the
measurement contradicts CORE, **correct CORE in place** — a wrong record
standing beside a right one makes the reader adjudicate.

## Derive enumerations independently

⭐⭐ **A SUPPLIED LIST IS A STARTING POINT AND NEVER THE SCOPE.** Derive the set
from the code — AST, the route table, the openapi schema — and **report the
difference.**

**In a dispatch:** *"Derive X from the code, not from this list. Report what the
list missed and what it contained that does not exist."*

⭐ And **check your own derivation**: a scanner written in five minutes produced
two false positives (`str.replace` matched as `os.replace`) in the very lane
about not trusting lists.

## Prove against the failing shape

⭐⭐ **A TEST THAT THE DEFECT CAN SATISFY BY LUCK IS NOT A TEST OF THE DEFECT.**
Pick values that break when the surface does. A derived value is *necessary*,
not *sufficient*.

**In a dispatch:** *"Prove it against the shape that failed, not a convenient
one."*

## Plant controls in memory, never in production source

⭐⭐ **A `finally` DOES NOT SURVIVE A KILL.** Four times a guard copied
production source aside, wrote a modified version, and a timeout landed before
the restore — stranding a live `NameError` that reddened unrelated gates.

**The required form:** build the modified source as a **string**, parse it,
never write a file. See `pack_input_scan.OVERRIDES`.
`tests/unit/test_guard_controls_are_kill_safe.py` enforces it across all 26
guards.

## Assert coverage, not activity

⭐⭐ **"0 PROBLEMS IN 0 FILES" AND "0 PROBLEMS IN 400 FILES" PRINT THE SAME
TICK.** Every guard prints its denominator and **fails on an empty corpus**.

**In a dispatch:** *"Print coverage. A zero is only readable against a
denominator."*

⭐ And: **a scanner that has never fired has not been tested.** Every guard
carries a **known-positive control** that must go red on the planted case and
green on the clean one.

## Absence declares

⭐⭐ **THREE STATES, NEVER TWO:** `in_bounds` / `out_of_bounds` / **`absent`**.
Absence propagates — **never `or 0`**. Use `_n(fn, *vals)`.

⭐ **FLAG AND STORE, NEVER REFUSE.** A boundary violation is recorded and
surfaced, not rejected — except at a client boundary, where a null in a payload
is a **422**, not an em dash.

⭐ In a payload: `has_data`, and an `absent` string that says *why*. **An empty
object reads as "the system produced nothing."**

## Report rather than resolve when a ruling is required

⭐⭐ **SURFACE COLLISIONS. NEVER AUTO-RESOLVE.** If two records disagree, or a
dispatch conflicts with a standing ruling, **say so and stop that part** —
finish everything that does not depend on the answer.

⭐ **UNDETERMINED IS A RESULT.** Where provenance was never recorded, effort does
not produce the answer. Say "not recoverable" rather than inferring.

⭐⭐ **AND WHEN MEASUREMENT CONFIRMS BOTH SIDES OF A CONTRADICTION, STOP AND ASK
FOR A RULING.** If two ledger entries cannot both hold but a scan returns "yes"
to each, **the instrument is not broken and more scanning will not help.**
Inferring a reconciliation nobody wrote down is how a commercial term gets
settled by whichever enforcement happened to be built.

**Never in a dispatch:** correcting customer data, notifying customers, or
resolving a commercial term. Those are the user's rulings.

## Writing to production

⭐⭐ **THE ABILITY TO MINT A TOKEN IS NOT STANDING PERMISSION TO WRITE.**
Verification reads are fine. **Production writes require a lane the user names,
each time.**

⭐ **Cleanup deletes are scoped to exact created ids — never
`all-X-for-company-Y`.** That rule exists because a cleanup destroyed a
customer's report issues unrecoverably.

⭐ **Never print, echo, log or write any secret value** — not to a file, not to
a command line, not into `docs/`, which is committed.

⭐ **No company names or customer figures in any committed report.** Companies by
id or tenant hash only.

## Reports

⭐ **Write reports to `docs/reports/` as files. Do not paste long reports into
chat.**

---

# 5 · THE STANDING LAWS, IN PRACTICE

## Built is not wired — *eighteen instances* (5 Aug: the cmdk palette, built,
## shipped in two components, and never mounted app-wide)

⭐⭐ **A UNIT TEST PROVES A FUNCTION WORKS. IT CANNOT PROVE ANYTHING CALLS IT.**

**When writing a lane:** every build lane must end with a **wiring assertion**
that names the *path a user takes*, not the file the code sits in.

⭐⭐ The worst instance was one level up: an assertion **read a file from disk
and matched substrings**. It proved a file existed, contained the words, and
placed the component. **It never made a request and never named a URL** — and
the page turned out to be **unreachable by its own name** (`/what-is-axiom`
404'd for every visitor while `/how-it-works` served it).

**Tell:** an assertion with no URL in it.

## A guard that matches text will punish stating its own rule — *twelve instances* (6 Aug: the strategy-map delete-guard matched `@router.delete`, the DECORATOR, while the forbidden thing was the row destroy — `90f2b5f`)

| banned token | what it actually struck |
|---|---|
| `credential` | client-facing reassurance that credentials are never stored |
| `comment` | the docstring explaining the ruling that comment text must not be assigned |
| `respondent` | explanatory copy about protecting respondents |
| `open(` | ⭐ `urllib.request.urlopen(` — a network read |
| `Authorization` | ⭐ the comment explaining why a page sends **no** Authorization header |

⭐⭐ **THE FAILURE IS ALWAYS IN THE SAME DIRECTION.** Text matching cannot
distinguish **doing** the thing from **naming** it, and the clearest writing
names it most. **The guard taxes honesty and leaves the capability reachable
under any synonym.**

**The default form is an AST read** — match a call, an attribute, a keyword
argument, a column. ⭐ **AN EXCEPTION LIST IS THE TELL**: adding an allowlist
entry to stop a guard firing on correct writing means the guard measures the
wrong thing.

## Every ratchet needs its opposite — *added 6 Aug*

A ratchet that only tightens one way is half a ratchet. The sidebar contract
checked shipped-not-expected and never the reverse, so retiring a group left the
crawler asserting one that no longer existed and the guard said nothing.
`check-ledger-anchors` now fails **both** on a new collision and on a baseline
entry that has stopped colliding.

## A guard over a list cannot see what the list omits — *added 6 Aug*

Two hand lists compared to each other are blind to the entry neither carries.
Derive the list from the thing it describes. ⭐ **Corollary, measured:** a guard
whose corpus was source-only was **vacuous** for retired tab keys — the links
needing the aliases live in committed prose, not in code.

## Span distinguishes a chart from a table, and is blind to positions carrying no meaning — *added 6 Aug, extended 7 Aug*

§III.13 established span against a **table**. Repositioning marks by **array
index** left span at 1030px and the assertion **passed**; monotonicity and
same-value-same-x caught it. ⭐ **Extended 7 Aug:** geometry is blind to **paint**
— a `<line>` whose stroke equals the background has a perfect bounding box.
Fifteen edges, correct coordinates, **1.03:1 contrast**, invisible.

## A control that reads the artefact must fail the way the check fails — *added 6 Aug*

A control asserting `"overview" in known_prof` took the app's state as a premise
and **crashed before the findings printed**, so the run blamed the guard for a
defect the guard had found. ⛔ **Sharpest instance:** `check-relative-imports`
contained `if node.module is None: continue` and skipped the exact statement it
was written to catch.

## A constraint on cardinality cannot catch an error of identity

A guard asserting "at most one dataset is active" was **perfectly satisfied**
while the single active dataset was **the wrong one**. Five demo surfaces
rendered empty and every gate stayed green.

**When writing a lane:** ask *which* thing, not *how many*.

## HTTP 200 proves reachability, never population

Five surfaces rendered empty behind 200s. A holding-mode page answers **200 while
rendering something else entirely** — a status sweep cannot see suppression.

**In a dispatch:** *"Read the payload, not the status."*

## The provenance law

⭐ **A STORED RESULT RECORDS WHAT PRODUCED IT.** Where it was not recorded, the
fact is **unrecoverable, not false** — and effort will not produce it.

## Verify behaviour, not the count

⭐ **A ratchet satisfied without fixing the defect is a spelling check.** The
frontend lint ratchet is **downward-only; the binding ceiling is
`no-explicit-any` at 819** (1,039 warnings total, 5 Aug); if a lane adds one,
**fix the warning, do not raise the ceiling.**

⭐ Related: **a test that pins the MECHANISM blocks every other correct
implementation.** One pinned two CSS class names; a rewrite satisfied the same
property by scrolling instead of reflowing, and the test failed while nothing it
protected had been lost.

## Sole ownership by arithmetic shape

A quantity has **one owner**. ⭐ **THE TEMPTING FIX IS A GATE CHANGE; THE CORRECT
FIX IS OWNERSHIP.** Raising a downward-only boundary to make a lane pass is the
one thing the ratchet exists to forbid.

## Two declarative bases, two engines, one database

⭐⭐ `core.db.Base` (alembic) and `accounts.Base` (`create_all` + runtime
`_add()`). Also **two User tables**: `users` (identity) and `ax_users`
(accounts, carries `platform_role`).

⭐ **Both read the same `DATABASE_URL`** and differ only in their **SQLite
fallback default** (`axiom.db` vs `axiom_accounts.db`). Production sets the
variable, so **they are one Postgres**.

⭐⭐ **LOCALLY, WITH THE VARIABLE UNSET, THEY ARE TWO FILES** and you will see
*"no such table"* for tables that exist. **That is a dev artefact — do not encode
it as a production fact.** Verify the way production runs:
`DATABASE_URL=sqlite:///$(pwd)/one.db`.

⭐ **The `ax_` prefix does NOT indicate the base.** `ax_packs` is on `core.db`;
`ax_departments` is on accounts.

⭐ **A model must be imported BEFORE `create_all`** (see `main.py`, above
`include_accounts(app)`) or its table is never made, and the failure surfaces as
"no such table" at first use rather than at boot. **This has happened twice.**

## k-anonymity and the assessment

⭐ **KFLOOR = 3**, counting **distinct participants**. Complement-inference
suppression applies. ⭐ **A suppressed category is RENDERED, NEVER OMITTED** — a
department reading a blank section concludes its people said nothing.

⭐⭐ **THE FLOOR ASSUMES READERS ARE KNOWN MEMBERS OF THE ORGANISATION.**
Respondents answered believing their words stay inside the company. That is why
pilot viewers are **named invitations, never an anonymous forwardable link.**

---

# 6 · DEFECT CLASSES AND THEIR TELLS

| class | tell |
|---|---|
| **Built not wired** | an assertion with no URL; a module imported but never `include`d |
| **Text-matching guard** | a banned *word*; an allowlist growing |
| **Cardinality vs identity** | "exactly one" with no "which one" |
| **200 ≠ populated** | a status-code sweep with no payload read |
| **Vacuous test** | passes when the code is mutated; five taxonomised ways |
| **Compensating defects** | correct output from two errors cancelling |
| **Dropped declaration** | values survive, the declaration does not |
| **Half-done supersession** | writes migrated, reads left behind |
| **Shadowed route** | code correct and never served |
| **Silent empty** | "no cycles yet" on a company with two cycles |
| **Instrument reporting on itself** | the harness reimplements the path it measures |
| **Empty harness** | a `TestClient` over an empty DB — every destination 401s and the guard calls it a pass |
| **Substring identity** | `brief` matching `lead-briefing`; SLA counted 17 times, actually 2 |
| **Silent truncation** | a top-N cap with no log of what was dropped |
| ⭐⭐ **CORE versus CORE** | ⭐ **measurement confirms BOTH sides.** Two ledger entries, each individually correct, mutually exclusive, and **both true of the code** — so no scan can find it. Surfaces only from inside a lane trying to obey both. **Two instances:** the diagram's closing bar; tier caps vs unlimited users |

⭐⭐ **THE UNIFYING TELL: AN EMPTY RESULT THAT LOOKS EXACTLY LIKE A CLEAN PASS.**
A measurement bug in a recent lane walked `app.routes` (44 paths) instead of the
openapi schema (hundreds), reported every feature as unbuilt, and **marked
nothing — which is indistinguishable from success.**

---

# 7 · CURRENT STATE (7 Aug 2026)

⭐ **Every count in this section was measured on 7 Aug, not carried forward.**

| | measured |
|---|---|
| backend CI steps · guard scripts | **34** · **33** |
| frontend CI steps · guard scripts | **17** · **9** |
| backend tests | **2,343 passed**, 1 skipped, 3 xfailed |
| frontend lint | **1,039 warnings across 289 files** |
| ratchets (at ceiling, none over) | `no-explicit-any` **817** · `no-restricted-syntax` **180** · `exhaustive-deps` **26** |
| CORE section headings · distinct anchors | **99** · **91** (⛔ **8 duplicated** — §0.2) |
| reports on disk · cited in CORE | **144** · 39 |

⛔ **KNOWN-RED, CARRIED:** two pre-existing mutation survivors
(`test_resolver_selects_the_populated_cycle`,
`test_score_is_not_money_and_carries_no_symbol_or_tier`), and **`demo-rot` has
never once succeeded.**

## The launch condition — ruled

⭐⭐ **AXIOM LAUNCHES FEATURE-COMPLETE. THE APP RETURNS TO PUBLIC AVAILABILITY
ONLY WHEN EVERY FEATURE IS BUILT AND TESTED.** There is no MVP cut — the ~30
designed features **are** the launch. Arriving partial is a positioning cost that
cannot be recovered, because the first impression sets the category.

⭐ **HOLDING MODE IS ON.** `src/lib/holding-mode.ts` → `HOLDING_MODE = true`,
covering exactly `/` and `/pricing` for anonymous visitors. Signed-in sessions
pass through. **Both answer HTTP 200 while rendering the holding page.**

## Queue A — awaiting a user ruling (4 open)

`A6` KPI surface disposition · `A7` reason-category ruling · `A9` DEI definition ·
`A2` `size_premium` = 0.2 (**the account is the operator's own test account, not
a customer**; correction and notification remain the user's ruling).

## Queue B — awaiting a build (selected; see CORE for all 18)

`B2` §7r ratio library · `B3` §7r-D DuPont (**blocker cleared**) · `B4`
ValuationRun code version · `B17` §4l Control Tower (**no code**) · `B18` mobile
coverage pass · `B19` mindmaps (**undesigned**) · `B20`/`B21`/`B22` encode the 31
Jul rulings · `B15` the features map as a distinct asset.

## ⭐⭐ THE OPEN QUEUE IN PRIORITY ORDER (7 Aug) — rulings first

**Rulings owed. Nothing below them can be built without one.**

| # | ruling | why it is first |
|---|---|---|
| 1 | **§7r-O's completion — sole-own the leverage-risk assumption** | It exists **four times** on four bases with unrelated constants, and **the un-owned quantity decides the sign** of the leverage advice a CFO reads. ⛔ §7o binds; **it moves published valuations**, so it is gated on the §7u registry carrying all four with provenance. |
| 2 | **Which endpoint owns `kr_key`** | The strategy map mints `/key-result/{kr_key}` links and `/companies/{id}/objectives` carries **zero** `kr_key`s — **0 of 6 key-result nodes resolve.** |
| 3 | **Should the eight duplicated CORE anchors be renumbered?** | A dispatch citing `§8n` or `§4v.2` is ambiguous today. Renumbering means editing **committed reports**, which is why it is a ruling and not a cleanup (§0.2). |
| 4 | **Band aggregation at a coarser grain** | Ruled in principle (§8o ruling 4); the build is not done, and summing percentiles overstates the range by √n. |
| 5 | **Partial-bucket policy beyond the current default** | Complete-only-with-remainder shipped as **my** choice, marked as unruled. |
| 6 | Assessor standing-vs-per-cycle · Viewer positive definition · the tier contradiction · does a pack freeze the leader / the movement history · milestone deletion as a revoke (ten-site sweep sized) · the crawler merge (two divergent `auth-regression.py`) · required checks as a real gate | carried from earlier lanes, unchanged |

### ⭐⭐ ADDED 7 AUG — TWELVE MORE, AND ONE OF THEM BLOCKS TWO PROGRAMMES

| # | ruling | why |
|---|---|---|
| **0** | ⛔⭐⭐ **THE SPEC IS NOT IN THE REPOSITORY** | Two lanes were dispatched against a spec citing §2, §4 (Tabs A–G), §82, §83, ~60 engines, and a nine-dimension grain. **Zero matches in `docs/`** — `docs/specs/` holds six specs, none of them it. Both lanes had to substitute derivable denominators. **Nothing in the data-spine or PMO programme can be measured against its own scope until this lands in the repo.** Ranked above everything because it is not a decision, it is a missing input. |
| **0b** | **`routeTree.gen.ts` — Lovable committed the STRICT variant** (`b7eb617`) | The guard refuses it; **two clean frontend commits cannot push** (`acab2c9`, incl. the dataset-id verification fix). Ruled *"leave it"* 7 Aug — **a hold, not a resolution.** Options: restore the LOOSE variant, or `ALLOW_ROUTETREE=1` if the route change was intentional. |
| 7 | **Which bucket `cf.net_borrowing` takes** | It is in `LABELS` and carries values in **33/33** datasets, and is dropped from every frequency view for want of a token. Candidates: `sum` (issuance less repayment is a period flow) or a refusal (a *net* of two flows the template cannot decompose). |
| 8 | **Does the ratings surface publish its count** the way §4u-c publishes the comment count? | Measured: **19 of 33** — no: **3 of 45 department-cycles** fall below KFLOOR at n∈{1,2}. Because the floor is all-or-nothing per department, **withholding discloses the same two-element set implicitly.** The choice is disclosing plainly vs disclosing by inference. |
| 9 | **`not_supplied` as a declared third dimension state** | `is_unallocated` exists; *"this business has no geography dimension"* has no representation, and an empty table cannot distinguish it from a failed upload. |
| 10 | **Legal Entity · Business Unit · SKU as `Dimension Type` values** | 6 of the 9 named dimensions are already covered by `DIMENSION_COLUMNS`. These three are enum values plus a hierarchy rule — **not a second template.** |
| 11 | **Build the completeness score before any engine** | Derivable today (**45/77 = 58.4%** for the demo, **42/77 = 54.5%** for the other three companies), needs no new engine, and is what turns a 54% first upload from a broken product into a progress bar. |
| 12 | **§5.1's fourteen roles** | **Not reachable by extending the matrix.** 10 sites consult it; **143 consult a binary `require_company_admin`**. The work is 143 individual capability judgements — and the Assessor/Viewer rulings (#6) are **inputs to those**, not preliminaries. |
| 13 | **§18 Decisions: a destination, and company scope** | 1 served path, **0 of 106 nav destinations**. Also document-scoped where §18 wants a company register. **Extend that owner; §17 Issues is the working sibling.** |
| 14 | **The interpolation banner's grain** | A module-level constant says *"between reported quarters"* on an annual dataset, and ships on non-interpolated responses too. Smallest change reported, **not built**. |
| 15 | **Frontend copy for the at-bound reading and the equity grid** | The **slot and the data** shipped 7 Aug; weight and placement are Lovable's. ⛔ Not an alarm — **19/33 = 57.6%** recommend at a boundary. |
| 16 | **The crawler's dataset coverage** | `auth-regression` calls the valuation path for **one** dataset (`active_dataset_id`); datasets 3–5 are never active, and they are the only three that failed. Deliberately not widened in the same commit as the 404 fix. |

**Then builds, in dependency order:** the §7u registry entries that unblock #1 ·
the `kr_key` fix once #2 is ruled · band aggregation once #4 is ruled · `B2`/`B3`
ratio library and DuPont · `B17` Control Tower (**no code**) · `B18` mobile
coverage · `B15` the features map · `B19` mindmaps (**undesigned**, not unbuilt).

## ⛔⭐⭐ WHAT THE REPOSITORY ALONE CANNOT VERIFY

⭐ **A fresh advisor must not infer these from the code. Each needs an external
system or the user.**

| claim | why the repo cannot settle it |
|---|---|
| **Whether a deploy is serving HEAD** | The strategy-map investigation measured the component working at HEAD while the reader saw nothing. Only the served host answers this — check it **before** concluding a defect exists. |
| **Whether an endpoint works in production** | Measured this week: `frequency-view` returned **500 on every call it ever had** while every gate was green. The browser proof **stubs the API**, so a green gate says the surface works, never the endpoint. Curl the served host. |
| **⛔ Whether the DEPLOY renders what the tree renders** | **The browser gate cannot answer this.** `browser-verify.py` defaults `APP_URL` to **`localhost:3000`** and **nothing ever sets it** — CI serves `build:preview` there and tests that. ⭐ So every browser-gate run this project has ever made is a statement about the **tree**, on the **nitro** build; the deployed product is a **Vite SPA** with different chunking. Only a request against the served host answers it. |
| **Sentry, uptime and error rates** | Not in the repo. Sentry found the 500 that 2,336 tests and a three-mode browser proof did not. |
| **Whether `demo-rot` has ever succeeded** | It has not, and the repository cannot show why — the run history is in CI. |
| **Customer data, counts and figures** | Never in a committed report by ruling; only a lane-env read answers, and only as a verification READ. |
| **Which CORE claims are stale** | A ledger cannot audit itself. §0.2 found one row **stale in the rebuilding direction** by comparing commits to prose — the only method that works. |

## Reliability gates — precede any relaunch carrying paying customers

| gate | state |
|---|---|
| **G1** backups | ⭐ **CLOSED** — Railway **Pro**, daily/weekly/monthly, RPO 24h |
| **G2** restore | ⭐⭐ **OPEN — RESTORE STILL UNTESTED.** PITR failed on an uninitialised pgBackRest catalog, 6 attempts. ⭐ **RTO UNMEASURED, not estimated.** |
| **G3** outage detection | ⭐ **CLOSED** — GitHub Actions probe every 30 min from *outside* Railway |
| **G4** hung process | ⭐ **CLOSED** — gunicorn arbiter restarts a hung worker in 120–180s. Residual: a wedged *container* is alerted in 30 min, not restarted |
| **G5** | ⭐⭐ **OPEN — unprotected `main`, no staging.** A bad commit reaches production behind a local hook only |
| **G11** load | ⭐ **RECLASSED TO LAUNCH.** No load testing; at a thousand firms the monthly sweep *is* the untested load |

## ⭐⭐ WHERE THE QUEUE LIVES (added 5 Aug)

**CORE §0.1 carries the open queue in priority order, the rulings owed, and what
is known-red.** Read it before anything else — it exists so you do not have to
reconstruct the state from commits.

⭐ **It was reconciled on 5 Aug against a fuller list and gained four items** —
the urgency/importance matrix (**model only, no surface**), user roles (**an
adoption problem: 12 sites on the capability layer against 96 on
`require_company_admin`**), Monitoring (**built 5 Aug**) and the mindmap
(**undesigned**, CORE B19). ⭐ **Each line there is measured, with its evidence
beside it.**

## ⭐ THE INFORMATION ARCHITECTURE CHANGED ON 5 Aug

The app now ships **three sections and 14 sidebar links**, not the older shape
this file was written against:

    WORKSPACE  My AXIOM ▸ Team · Objectives & KRs · Data Input · Assumptions
                         · Declared Impact · Pilot viewers · Sync
    ANALYZE    Structure · Dashboard · Feedback · Profitability · Valuation · Risk & SWOT
    STRATEGIZE Planning · Optimization · Prescience AI
    EXECUTE    Projects · Monitoring
    footer     Course Workspace · What is AXIOM?     (UTILITY is retired)

⭐ **custody-10's door is now labelled "Data Input", not "KPIs"** — the crawler's
runtime lock moved with it, and `check-sidebar-contract.py` fails if the two ever
part (§4A.2).

⭐ **Every tab is addressable** — 19 of 19 strips are URL-driven, and a generated
navigation index of **106 destinations** is guarded by regenerate-and-diff.
⚠️ *Corrected 7 Aug from 107: grepping the generated file for `label:`
counts its own `NavEntry` type declaration as an entry. Use the
generator's printed count, never a grep.*
**Regenerate with `python3 scripts/gen-nav-index.py` after any route or tab
change**, or `check-nav-index.py` fails.

## ⭐ FRONTEND GATES (12 steps, `.github/workflows/ci.yml`)

`ci-steps.py` derives the pre-push hook from that workflow — **one owner**. New
this session: `check-flow-diagram-links` · `check-hydration-safe-session` ·
`check-sidebar-contract` · `check-scope-declared` · `check-tabs-addressable` ·
`check-nav-index`.

⭐ **`bun run build` regenerates `routeTree.gen.ts` — and as of 7 Aug you COMMIT
that.** ⛔ **The old instruction here said to restore it with
`git checkout -- src/routeTree.gen.ts`. Do not.** The regenerated form is
legitimate under TanStack Start, `check:routetree` now validates it by harm (do
the modules its Register block imports exist) rather than by presence, and
`build:preview` no longer strips it. If the check ever fails, **regenerate**
(`NITRO_PRESET=node-server bunx vite build`) — a step that needs a clean
generated file regenerates or fails; it does not discard.

⚠️ **Two automated resets remain**, both in `.githooks/pre-push` (lines 119 and
135). They are recorded in `docs/reports/routetree-strip-removed-2026-08-07.md`
and their removal is a separate lane — **so a local push still resets the file
today**, and the oscillation is reduced, not yet ended.

## Known open items you will trip over

- ⭐⭐ **Demo-rot has NEVER succeeded** — five scheduled runs, zero assertions.
  1 Aug failed on absent secrets; 2–5 Aug on a **missing playwright install**,
  fixed 5 Aug. Its secrets are set. ⛔ **No green run exists yet, so its coverage
  is unproven rather than restored.**
- ⭐⭐ **Backend CI is RED** on two pre-existing mutation survivors (§0.1).
- ⭐⭐ **Two divergent copies of `auth-regression.py`** — the **backend one is
  canonical** and is what `demo-rot` runs; the frontend copy asserts a **weaker**
  custody-10 (one lock, no tab walk) and runs nowhere.
- ⭐ **Required status checks gate PR merges, not direct pushes** — measured. A
  direct push to protected `main` succeeds (§8s.2).
- ⭐ **§4z's three places:** the viewer experience is built; **the results call
  and the pricing page are not.**
- ⭐⭐ **A CONTRADICTION IN CORE, UNRESOLVED:** the tier definition caps Business
  at **5 viewers**, while §4y rules pilot viewers **unlimited and unbilled** and
  §4z rules unlimited users. **Both cannot be true. The user's ruling.**
- ⭐ **Comparison matrix:** the 253 per-cell reasons live in `title=` hovers,
  which a **touch device cannot reach**. Recorded as a finding, not a bug.

---

# 8 · RE-ESTABLISHING ACCESS

## Repositories

| repo | path | owner |
|---|---|---|
| `drsamirasaf-creator/axiom` | `/Users/samirasaf/dev/axiom` | backend, tests, guards, **the ledger** |
| `drsamirasaf-creator/optimization-anchor` | `/Users/samirasaf/dev/optimization-anchor` | frontend |

Both deploy from `main`. ⭐ **The backend auto-deploys to Railway on push. The
frontend publishes on Lovable's own schedule** — pushing to GitHub is not
publishing, and **the served bundle is the only truth.**

## Hosting

- **Backend:** Railway, `https://web-production-0e3de.up.railway.app`
- **Frontend:** `https://axiomdynamics.app`
- **Database:** Railway **Postgres**, workspace on the **Pro** plan (Pro is what
  makes scheduled backups possible — `maxBackupsCount` was 0 on the prior plan).

## Secrets

⭐⭐ **EVERY SECRET VALUE LIVES ONLY IN RAILWAY.** Nothing is in the repository,
and nothing may be written into `docs/`, which is committed.

- **`.env.example` is the manifest — NAMES AND EXPLANATIONS ONLY, never values.**
  65 variables, and `scripts/check-env-manifest.py` fails if code reads a
  variable the manifest does not document, or documents one nothing reads.
- Fetch for a lane with **`scripts/lane-env.sh`** — one fetch per lane, and
  **the URL is never printed.**
- ⭐ `DATABASE_PUBLIC_URL` comes from `railway run --service Postgres`.

⭐ **If you need the user to authenticate** (e.g. `railway login`), ask them to
run it themselves — in Claude Code, prefixing a command with `!` runs it in the
session.

## Verification hosts

`AXIOM_APP_BASE` (frontend) and `AXIOM_DEMO_BASE` (backend) default to the live
hosts. ⭐ **They default to production deliberately** — a prospect-facing 404 is
only observable where a prospect would meet it, and the demo surface is a
production artefact that only production can answer for.

## The showcase

⭐ **There is exactly one showcase company: Meridian.** Halcyon and Helios were
measured and deleted. ⭐ **Milliner is explicitly denylisted** in the crawler so
no resolver change can redirect a crawl into a real customer's data.

---

# 9 · KEEPING THIS CURRENT

⭐⭐ **A RECOVERY DOCUMENT THAT GOES STALE IS WORSE THAN NONE, BECAUSE IT WILL BE
TRUSTED.** This file is subject to the same law as CORE: **a stale line does not
merely misinform, it issues instructions.**

**Update this file in the same lane, not afterwards, when any of these change:**

| trigger | section |
|---|---|
| a new defect class, or a new instance of one | §5, §6 — **update the instance count** |
| a queue item ruled or built | §7 |
| a reliability gate closing | §7 |
| a new standing practice | §4 |
| a custody or routing correction | §2 |
| a host, repo, plan or secret-location change | §8 |

⭐ **The counts in this document are claims.** "Ten instances", "eleven
instances", "29 gates", "819 / 1,039 warnings", "twelve wrong CORE entries" —
each is
measurable, and each will be wrong the moment it is not maintained. **If you
cannot verify a count while reading, measure it before relying on it.**

**The test this file must keep passing:** *could a fresh advisor read it and
write a correct dispatch tomorrow?*
