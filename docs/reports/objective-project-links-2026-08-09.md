# The 26-of-26 gap was my own key — and the chain never used that hop

**9 Aug 2026.** T1 **corrected, seeded and left with a deliberate gap.** T2
**answered.** ⛔ **The gap this lane was dispatched to close did not exist.**
Proof origins: `WS.for_department` — the surface's own function — against the
lane database (company 20); `accounts.py` for the key convention.

---

# ⛔⭐⭐ T1 · THE CAUSE WAS MINE, AND IT WAS THE KEY

```
ax_goal_initiative_links.goal_key = "a normalized hash of the objective/goal text"   (the model)
accounts.py:5415                    db.add(GoalInitiativeLink(… goal_key=obj_key …))
```

⛔ **`goal_key` is `obj_key`, not `objective_id`.** Both my earlier connectivity
lane and the workspace check used `objective_id` (O2, O9…), which **no link ever
carries** — so every objective read as unlinked no matter how many links it had.

⭐ **The stable key is the text hash on purpose**: a re-upload keeps its links,
where the per-snapshot ordinal would lose them. **I used the ordinal.**

## ⭐ THE MEASUREMENT THAT EXPOSED IT

After correcting the key and **before writing anything**, the surface already
read **0 of 26 without a project**. **The links existed all along.**

| | |
|---|---|
| reported gap | ⛔ **26 / 26** |
| real gap, once the key was right | ⭐ **0 / 26** |
| mis-keyed rows found | **1 live** (the other 26 matched correctly on `obj_key`) |

⛔ **So "27 live rows and none connects" was wrong in its second half**, and the
first figure I gave — 47/47 across snapshots — compounded two of my own defects:
the missing dataset scope and the wrong key.

## ⭐ WHAT I THEN DID, INCLUDING THE PART I HAD TO UNDO

I seeded **6 links** and revoked **1 mis-keyed** row before re-reading the
surface — and it showed **0 of 26**, i.e. **a perfectly linked company**, which is
the opposite of what the dispatch asked for. ⛔ **My gap logic skipped the first N
objectives, and those were already linked, so it protected nothing.**

⭐ **Corrected by REVOKE, never delete** — one objective in the demo's weakest
department and one in its newest:

```
revoked 1 link from Supply Chain and Logistics: 'De-risk single-source suppliers'
revoked 1 link from Internal Audit:             'Complete the FY audit plan with no overdue findings'
```

**Final, through the surface's own function:**

```
Executive Management 0/3 · Finance 0/3 · Operations 0/3 · IT 0/3
Supply Chain 1/3 · Human Resources 0/3 · Sales 0/3 · Marketing 0/3 · Internal Audit 1/2
TOTAL 2/26 — a deliberate gap, not a perfect company
```

---

# T2 · THE CHAIN NEVER USED THE OBJECTIVE→PROJECT HOP

⭐ **It traverses `KrInitiativeLink` — key result → initiative — not
`GoalInitiativeLink`.**

| link table | live rows |
|---|---|
| ⭐ **`KrInitiativeLink`** — the hop the chain walks | **161** |
| `GoalInitiativeLink` — the hop the workspace checks | **30** |

⛔ **So "9 of 9" was never evidence about objective→project.** The chain runs
*sentiment → objective → key result → KPI → initiative*, and its last hop binds
the **key result** to the initiative. **The workspace asks a different question —
does a project sit beneath the OBJECTIVE — and that question had never been
asked before this surface existed.**

⭐ **The chain still holds at 9 of 9** after these links, with no breaks. **The
two facts were never in tension; they were about different edges.**

---

# WHAT IS OWED

1. ⚠️ **The `objective_id`-vs-`obj_key` confusion is mine and may be elsewhere.**
   Both places I wrote it are corrected and tested; nothing asserts the
   convention globally.
2. ⛔ `/version.json` serves `08a4694`; the frontend gate is still red.
