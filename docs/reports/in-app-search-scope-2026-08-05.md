# In-app search — scoped

**Report only. No build.** 5 Aug, from `adbfc1f` / `d013c3f`, both clean and in
sync.

---

## 4 · What already exists — ⭐⭐ and the palette is one of them

Searched: `search · index · command · palette · omnibox · spotlight · quickfind ·
lookup · finder`.

| thing | state |
|---|---|
| ⭐⭐ **`src/components/ui/command.tsx`** | **A FULL `cmdk` COMMAND-PALETTE PRIMITIVE** — `Command`, `CommandDialog`, `CommandInput`, `CommandList`, `CommandEmpty`, `CommandGroup`, `CommandItem`, `CommandShortcut`. ⭐ **Already used in production** by `CurrencySelector` and `/my-axiom`. ⛔ **Never mounted app-wide.** |
| **Ask AXIOM** | ⭐ shipped, in the header on **every** page (`AskAxiomLauncher`). Answers questions **over the data** — it is the data-search surface, in prose form |
| **GLOSSARY** (~400 lines) + `glossary-remote` | term → definition, consumed by `InfoTip`. ⛔ **`lookupRemote` is a point lookup — there is no search over it** |
| **`PageScope` + `docs/department-scope-audit.md`** | the leaf-level scopability inventory — ⭐ **a ready-made source of per-leaf metadata** |
| **`GET /companies/{id}/my-capabilities`** | ⭐ shipped, already read by `useCapabilities` |
| ⛔ **a backend `/search` endpoint** | **does not exist** — no route matches `@router.get(".../search")` |

⭐⭐ **EIGHTEENTH UNSEARCHED NAME, AND A DIFFERENT SHAPE THIS TIME.** The previous
seventeen found a *capability* already built. This one finds the **widget** built
and proven, with the *feature* genuinely absent. **That distinction matters for
the estimate: the UI layer is not the cost.**

---

## 1 · The navigable surface, derived

    routeTree fullPaths                    64
      parameterised (need a real id)        8   /department/$deptId /initiative/$iid
                                                /kpi/$kpiId /objective/$objKey
                                                /key-result/$krKey /sentiment/$axisCode
                                                /c/$cid /pilot-view/$token
      redirect-only route FILES             4   benchmarking · discussion
                                                my-companies · reports
    tab objects found                     111
      reachable                            96
      ⛔ DEAD — below a redirect            15   all in benchmarking.tsx
    unique reachable tab keys              88   (after de-duplicating cei's two
                                                 tab levels and my-axiom's three
                                                 render sites)

### ⭐⭐ The derivation must see past early returns, and here is the proof

`benchmarking.tsx` declares **fifteen tab objects that sit below
`return <Navigate to="/risk-analysis" …/>` and never render.** The IA audit
counted them as a surface and I repeated it in a pushed report; the IA lane
corrected it.

⛔ **AN INDEX BUILT BY THE SAME NAÏVE SCAN WOULD SHIP FIFTEEN RESULTS THAT LAND
NOWHERE** — the exact dead end §4v forbids, generated automatically and at scale.

⭐ Four route files are redirect-only. **A correct index must resolve a redirect to
its destination, not index the alias as a destination** — otherwise "Benchmarking"
appears twice, once real and once as a stop on the way.

### The honest headline

**~88 tab destinations + ~40 non-parameterised page destinations**, minus
auth/onboarding routes that are not destinations for a signed-in user. ⛔ **I am
not reducing this to one number**, because the count depends on a ruling nobody
has made: **does a tab inside a filtered page count as one destination or several?**
`/cei` alone is 1 route, 5 tabs and 9 sub-tabs — **1, 5, 14 or 15 depending on the
answer.**

---

## 2 · The navigation index, and the guard that keeps it honest

### What it needs

1. ⭐⭐ **Derivation from `routeTree.gen.ts` and the tab configs at BUILD time** —
   never a hand list. Seven hand lists have been incomplete; the sidebar contract
   drifted nine labels.
2. ⭐ **Redirect resolution** — index the destination, not the alias.
3. ⭐ **Early-return awareness** — the fifteen dead tabs above.
4. **Per-entry metadata**: section (ANALYZE / STRATEGIZE / EXECUTE / WORKSPACE),
   the route, the tab key, the scope bucket, and the capability or tier required.
5. **Synonyms**, declared not inferred — a user types "SWOT", "benchmark",
   "actuals", "Gantt". ⛔ **Inference-by-name is the one mechanism this codebase
   has measured to zero** (`KeyResult.kpi_key`, null on all 82 rows). **Synonyms
   must be a declared list with an owner.**

### The guard, and where it lives

⭐⭐ **IN THE FRONTEND REPO**, on every push. The precedent is explicit: the
sidebar contract had to move there *"because that is where nav changes happen"*,
and the crawler that lived only in the backend drifted nine labels while a nightly
job that never once succeeded watched it.

**The guard must assert, both directions:**

- every reachable destination appears in the index — ⛔ *an index missing a page
  is a page a user cannot find, which is the same as unshipped*
- every index entry resolves to a **live** destination — ⛔ *catches the fifteen
  dead tabs*
- **printed denominators and a floor** (§III.4), so a recogniser that stops
  matching cannot pass
- **an AST/structural read, not a text scan** — §III.9 has fired **eleven** times,
  twice inside guards written in this same programme

⭐ **And a known-positive drawn from the route table, never invented** — §4z.3's
ninth instance was a control asserting a regex matched a string the guard had
written itself.

---

## 3 · Data search — a separate cost, and a much larger one

**Objects a user would expect to find:** initiatives, objectives, key results,
KPIs, departments, issues, ideas/proposals, documents, assessment cycles, people,
report packs.

### The permission model — every layer already exists, and none of it is optional

| layer | mechanism today | what search must do |
|---|---|---|
| **tenant** | `_participant_role_set`, `require_company_member` | ⛔ never return a row outside the active company |
| **role / capability** | `permissions.py` (`view` · `take_instrument` · `submit_idea` · `dispose_recommendations` · `admin`), `require_capability` at 12 sites, `GET /my-capabilities` | filter results by capability **server-side** |
| **magic-link scope** | `_token_scope`, refused on writes | a view-only link must not surface write targets |
| **department** | `PageScope` bucket A + `?department=` | scope results to the lens |
| ⭐⭐ **the k-floor** | `suppression_block` → `{suppressed, n, reason, note}`, three distinct reasons | **see below** |
| **tier** | 402 on paused/inactive subscriptions; `pro: true` on Prescience | answer truthfully **before** the click |
| **showcase** | `_summary_access` allows anonymous reads for showcase companies | search must inherit **exactly** this, not a looser rule |

### ⭐⭐ The floor is where data search is most dangerous

A department slice below `KFLOOR` is withheld — and the engine distinguishes
**three** reasons because merging them *"tells a manager their team ignored the
survey when in fact it answered and was protected."*

⛔ **A SEARCH RESULT THAT NAMES A SUPPRESSED SLICE DEFEATS THE FLOOR ENTIRELY.**
Worse than a leak: the floor's whole design assumes the *count* may be published
while the *value* is withheld. A result reading **"Quality — CEI 41"** in a
dropdown discloses precisely what `suppression_block` refused three layers down.

⭐ **And free-text search over verbatim comments is a re-identification vector by
construction.** The scope audit already rules this: Assessor Comments is
**N-A / privacy-gated** — *"a narrow department slice over verbatim text is a
re-identification vector; the k-floor protects aggregates, not quotes."*
**Search must not index verbatim text. That is a ruling to confirm, not my call.**

### Do they share machinery?

⭐ **The index is shared; the resolver is not.**

- **Navigation search** is a **static, build-time** index of ~128 destinations.
  No backend. No per-user filtering beyond hiding what the user cannot reach.
  **Cheap.**
- **Data search** needs a **new authenticated endpoint** applying tenant,
  capability, scope, department and floor rules to every object type — and
  `_summary_access`'s showcase exemption exactly. **It is a backend lane of its
  own**, and the floor makes it the most privacy-sensitive surface in the product.

⛔ **THEY SHOULD SHIP SEPARATELY.** Navigation search is a week of careful
derivation and a guard. Data search is a permission surface. ⭐ **Shipping
navigation first also answers "where is X" — which is what a 14-link, 88-tab app
actually makes hard.**

---

## 5 · Dead ends, and the tab-inside-a-page-inside-a-filter problem

⭐ **A result must land on the thing, not near it.** The app already supports this:
`/twin?tab=sync`, `/risk-analysis?section=benchmarking`, `/initiatives?open=A7`,
`/target-state?tab=initiatives`. **Every tab group with an `activeWhen` reads a
search param**, so a deep link can select a tab.

⛔ **BUT NOT UNIFORMLY, AND THAT IS THE GAP.** Some tabs are `to:` + `matches:`
(a real route). Others are `search:` + `activeWhen` (a param). **Others are local
`useState` with no URL at all** — `/valuation`'s 8, `/profitability`'s 6,
`/risk-analysis`'s 7. ⭐⭐ **A destination with no addressable URL cannot be a
search result.** Landing on the page and leaving the user to hunt is exactly the
failure this feature exists to fix.

**So navigation search has a prerequisite:** every indexed tab must be
URL-addressable. ⛔ **That is a real build across several pages, and it is the
honest bulk of the cost** — not the palette, which already exists.

**And the filter:** if a result is department-scoped, the link must carry the
department **and** the page must declare bucket A. ⭐ `check-scope-declared.py`
already guarantees every analytical page declares its bucket, so **the index can
derive scopability rather than guess it.**

---

## 6 · Tier and role — truthful before the click

⭐⭐ **THREE HONEST ANSWERS, AND SILENCE IS NOT ONE OF THEM.**

| case | correct behaviour |
|---|---|
| **Business user types "Multiverse"** | ⭐ **show it, marked PRO, linking to pricing.** The sidebar already does exactly this — `caption: "PRO", pro: true`. ⛔ Not silence (the feature exists and they should know), ⛔ not a 402 after the click |
| **Viewer types "Invite assessors"** | ⭐ **show it, marked as requiring an administrator.** Hiding it teaches the app is smaller than it is; a 403 after the click teaches it is broken |
| **Viewer types "Data Input"** | same — and custody-10 makes this door's discoverability a standing rule |
| **A result the user cannot see the DATA for** | ⛔ **omit entirely.** A capability the user lacks is a feature; **a data row they cannot open is a leak with extra steps** |

⭐ **THE DISTINCTION IS THE RULING:** *gated capability → show, labelled;
inaccessible data → omit.* **Navigation results are a menu; data results are
disclosure.**

⛔ **AND THE MARKING MUST NOT COME FROM THE CLIENT'S OWN GUESS.**
`use-capabilities.ts` says it plainly: *"COURTESY ONLY: the API is the security
wall."* The label may be client-side; **the filtering may not.**

---

## Rulings owed before a build lane

1. ⭐⭐ **Does a tab count as a destination?** It decides whether the index holds
   ~40 entries or ~128, and whether the URL-addressability work above is in scope.
2. ⭐⭐ **Is verbatim text indexed?** My reading is **no** — the scope audit already
   rules it a re-identification vector — but that is a confirmation, not my call.
3. ⭐ **Navigation first, data second?** My recommendation, and the two are
   separable.
4. ⭐ **Who owns the synonym list?** Declared, never inferred.

## What I did not do

No build, no index, no guard, no endpoint. **One commit: this report.**
