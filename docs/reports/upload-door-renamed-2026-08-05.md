# custody-10 — the upload door renamed, and its lock moved with it

5 Aug, from `c4d349a` / `5fdc0b3`. Frontend **`7f9a55a`** · backend this commit.

---

## 1 · The label: **"Data Input"**

**Why that word:**

- ⭐ **It is the page's own title** — `<InfoTip term="Data Input">Data Input</InfoTip>`
  and `pageKey="data-input"`. The tab and the page it opens now agree, which is
  the recorded principle: *"a sidebar that says one thing and a page that says
  another makes a reader check they clicked the right link."*
- ⭐ **It names the act** — where a client **supplies** data. `/dashboard?tab=kpis`
  is where they **read** it.
- ⛔ **It does not collide inside My AXIOM.** Its siblings are Team, Objectives &
  KRs, Assumptions, Declared Impact, Pilot viewers, Sync; the page's *own* inner
  tabs are "Financial & Organizational Data", "Additional Documents", "Participant
  List" — one level down and differently worded.

⛔ **THE OLD LABEL NAMED THE WRONG CONCEPT.** "KPIs" appeared twice in the app
meaning two different things, and the duplication a reader perceived was **the
word**, not the surface.

---

## 2 · Lock (b) moved in the same commit

    - tab = get_by_role("link", name="KPIs", exact=True)
    + tab = get_by_role("link", name="Data Input", exact=True)

in the **canonical backend crawler**, with the reason recorded beside it.

### ⭐⭐ And the tie is now guarded, not merely done once

`check-sidebar-contract.py` reads the label `MY_AXIOM_TABS` **actually ships** for
`/data-input` and requires the crawler's door-walk to use exactly that label.

⭐ **A lock pinned to a label must move when the label does** — otherwise a
crawler walking the old name reports the door **broken while it works**, or, if a
future tab reclaims the old word, reports it **open while it is gone.**

**Both red-proofs, in memory:**

| control | result |
|---|---|
| rename the tab, leave the lock | ⭐ `✗ custody-10 walks ['Data Input'] but the tab ships 'Uploads' — the lock and the label have parted`, `rc=1` |
| move the lock, leave the tab | ⭐ `✗ custody-10 walks ['Uploads'] but the tab ships 'Data Input'`, `rc=1` |

**Each fails independently** — the guard is not satisfied by the pair merely
changing together by accident.

---

## 3 · The two crawler copies — ⛔ they assert *different rules*

Measured, and this is sharper than "they have drifted":

| | canonical (backend, run by `demo-rot`) | frontend copy |
|---|---|---|
| lines | 1,376 | 1,597 |
| custody-10 | ⭐ **TWO locks** — My AXIOM in the sidebar **and** a runtime walk of its tab through to `/data-input` | ⛔ **ONE lock** — goes **straight to `/data-input`** and checks the surface |
| what that tests | **discoverability** — can a user *find* the door | only that the URL renders |
| sidebar labels | ✅ agree with the nav | ✅ agree (reconciled at `d900df1`) |
| runs | `demo-rot`, daily | ⛔ **nothing** |

⭐⭐ **THE FRONTEND COPY PREDATES THE 2 AUG AMENDMENT** that moved the door behind
My AXIOM. It is not stale by neglect — it encodes the **older rule**, from before
the door moved.

**Recommendation, not taken unilaterally:** ⭐ **delete the frontend copy**, and
let `check-sidebar-contract.py` carry the contract obligation alone — it already
runs on every frontend push, which is where nav changes happen, and it now guards
the label↔lock tie as well. ⛔ **But the frontend copy holds machinery the
canonical one lacks** — operator self-minting via `mint_operator_token` and the
standing verification tenant — so deleting it loses those. **That is a merge, and
a merge is its own lane.**

**Meanwhile the guard reports the divergence on every run** rather than accepting
it silently:

    · optimization-anchor/scripts/auth-regression.py: does not walk the My AXIOM
      tab — it checks /data-input directly, which does not test discoverability

---

## 4 · Both locks proven live

    ✓ custody-10 (a): My AXIOM is in the sidebar
    ✓ custody-10 (b): the 'Data Input' tab exists on /my-axiom
    ✓ the old 'KPIs' label is gone from My AXIOM        ← known-negative
    ✓ custody-10 (b): the upload door opens (landed /data-input)
    ✓ /dashboard?tab=kpis still owns the KPI measurement door

⭐ **The known-negative is what makes the rename real.** Asserting the new label
exists would pass on a page that still showed the old one too — which is the
duplication surviving the rename.

⛔ **AND ONE ASSERTION WAS WRONG ABOUT THE APP, NOT THE APP ABOUT ITSELF.** I first
asserted `/dashboard?tab=kpis` selects a tab with `aria-selected`. Dashboard's
visible strip is the **cross-page** group (Dashboard / Brief / SWOT & Risk /
Benchmarking); `?tab=kpis` switches the panel *beneath* it, so there is no strip
item to mark. **The page was working; the assertion was wrong.** §III.11 again —
rewritten to assert the content.

---

## 5 · The index and the synonyms

**Index: 107 → 107.** ⭐ The label moved, not the destination — `/data-input` is
one entry either way, and it now reads **"Data Input"**.

**Synonyms: 56 → 61**, all resolving. ⭐ **The two words now resolve apart:**

    upload · template · data input · statements  →  /data-input
    kpi · kpis · measure                         →  /dashboard?tab=kpis

**Verified in the generated index:**

    { label: "KPIs",       to: "/dashboard",  search: {"tab":"kpis"} }
    { label: "Data Input", to: "/data-input", search: {} }

⭐ **That separation is the point of the rename.** Before it, a reader typing
either word had one label to land on and no way to tell which concept they had
reached.

---

## 6 · Inbound links — derived and asserted

**300 refs across the touched pages** — `/dashboard` 47 · `/initiatives` 38 ·
`/risk-analysis` 38 · `/valuation` 34 · `/cei` 29 · `/data-input` **24** ·
`/my-axiom` 24 · `/twin` 20 · `/financial-forecasts` 20 · `/target-state` 14 ·
`/scenario-analysis` 12.

⭐ **No path moved** — this is a label change plus a lock change. All 24 links to
`/data-input` resolve exactly as before, and the comparison matrix's 13 and the
flow diagram's 17 are green.

---

## Guards and tests

| guard | verdict |
|---|---|
| ⭐ `check-sidebar-contract` (extended) | ✅ 14 labels · 3 groups · **custody-10 walks the label the tab ships** |
| `check-nav-index` | ✅ 107 destinations · 61 synonyms · all resolve |
| `check-tabs-addressable` · `check-scope-declared` · `check-routetabs-hoisted` · `check-flow-diagram-links` · `check-hydration-safe-session` | ✅ |
| `tsc` · `lint` · `ratchet` | ✅ at the ceiling |
| backend `pytest` | ✅ **2032 passed**, unchanged |

**No unit tests added** — this lane is a label, a lock and a guard. **1 guard
extended with 2 red-proofs, 5 new browser assertions, 5 new synonyms.**
⛔ **No other nav change.**

## Hashes

| repo | hash |
|---|---|
| `optimization-anchor` | **`7f9a55a`** |
| `axiom` | this commit |

## Owed

⭐ **The crawler merge** — fold the frontend copy's operator self-minting and
verification tenant into the canonical one, then delete it. Until then two copies
assert two different custody-10 rules, and only one runs.
⭐ Still open: **statements** (converge or not), **data search**, and the
`AXIOM_Architecture_A` entry with its correction.
