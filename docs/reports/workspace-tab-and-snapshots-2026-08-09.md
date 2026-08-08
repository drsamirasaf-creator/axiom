# My workspace moves under My AXIOM — and the "duplicates" were snapshots

**9 Aug 2026.** T1 **moved.** T2 **measured — and it found a defect in my own
module, now fixed and red-proved.** T3 **measured; nothing seeded.**
Proof origins: authorized read queries against the lane database (company 20);
the three nav guards and the suite, run locally.

---

# T1 · MOVED — NAV ENTRY ONLY

⭐ **A tab here is a LINK TO A FLAT ROUTE.** `/workspace` is unchanged, so every
inbound reference still resolves: **no path change, no redirect, no signpost.**

| | |
|---|---|
| removed from | `businessSections` → **ANALYZE** |
| added to | **`MY_AXIOM_TABS`**, between *My AXIOM* and *Team* |
| module membership | ⛔ re-declared **`analyze` → `none`** — My AXIOM is `none`, and **a page that changes section changes module** |
| both `auth-regression.py` copies | ⭐ updated **in the same commit** |
| ⭐ **destination count** | **107 destinations · 34 pages · 73 tabs** — unchanged, because the entry moved rather than appearing or leaving |

**All three guards green:** sidebar contract, routes-reachable, module membership.

---

# T2 · ⛔⭐⭐ NOT DUPLICATE ROWS — THREE SNAPSHOTS, AND THE CHECK WAS READING HISTORY

```
id=38   O2  ds=42  template  key=f74917bc5d  Expand EBITDA margin by 400bps
id=48   O2  ds=43  template  key=f74917bc5d  Expand EBITDA margin by 400bps
id=58   O2  ds=45  template  key=f74917bc5d  Expand EBITDA margin by 400bps
id=45   O9  ds=42 · id=55 O9 ds=43 · id=65 O9 ds=45   Automate the monthly close
id=182  O101 ds=45 in_app                     Cut cost-to-serve per invoice 20%
```

⭐ **Same `objective_id`, same `obj_key`, one row per DATASET VERSION.**
Objectives are **snapshot-scoped**: a re-upload mints new rows and the old ones
stay. **7 rows, 3 distinct texts, and only 3 rows are on the active dataset (45).**

⛔ **So it is neither of the two defects the dispatch offered.** Not duplicate
rows, and not one row emitted repeatedly. **It is three legitimate rows and a
check that failed to scope to the active dataset — my defect, in
`workspace.py`.**

⭐ **And the earlier re-keying lane is exonerated by the same values**: the O112–O116
re-key touched `objective_id`, and these rows carry O2/O9 with **identical
`obj_key` hashes across all three snapshots**. Nothing was duplicated; nothing
needs revoking. **No removal is proposed, because nothing here is wrong in the
data.**

## ⭐ FIXED AND RED-PROVED

`for_department` now filters objectives, key results and KPIs to
`_active_company_dataset`. **A test plants the same objective on two stale
snapshots and the live one and asserts it is listed ONCE**; removing the filter
fails it. **15 tests, suite 2,582.**

---

# T3 · THE FRACTION — AND THE FIRST FIGURE WAS INFLATED BY THE SAME BUG

| scope | objectives with no project |
|---|---|
| ⛔ all snapshots (what the surface showed) | **47 / 47** |
| ⭐ **active dataset only (the true figure)** | **26 / 26** |

**Per department, on the active dataset: 3/3 for eight departments, 2/2 for
Internal Audit.**

⛔⭐⭐ **It is 100% either way.** **Not one objective in the company has a project
beneath it**, so the workspace is **correctly reporting a real gap** — the
objective→initiative link was never seeded.

⚠️ **27 live `GoalInitiativeLink` rows exist company-wide** and none of them
connects an objective to an initiative *of the same department*, which is what
the check requires. **Reported, not seeded**, per the dispatch.

---

# WHAT IS OWED

1. ⛔ **The objective→project link is unseeded across all nine departments** —
   26 of 26. A seeding lane, not this one.
2. ⛔ `/version.json` serves `08a4694`; the frontend gate is still red.
