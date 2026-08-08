# The duplicates, the fraction, and .build-commit

**9 Aug 2026.** T1 and T2 were **measured in the interrupted lane and the fix is
already shipped** (`c53afd4`); this report confirms the result on the live
surface. T3 **measured — and gitignoring it is NOT free.**
Proof origins: authorized read queries against the lane database (company 20);
`vite.config.ts` and `.githooks/post-commit` at HEAD `3253e10`.

---

# T1 · ⛔⭐⭐ NEITHER DEFECT — THREE SNAPSHOTS, AND THE CHECK READ HISTORY

**The stored rows, Finance and Accounting:**

```
id=38   O2   ds=42  template  obj_key=f74917bc5d  Expand EBITDA margin by 400bps
id=48   O2   ds=43  template  obj_key=f74917bc5d  Expand EBITDA margin by 400bps
id=58   O2   ds=45  template  obj_key=f74917bc5d  Expand EBITDA margin by 400bps
id=45/55/65  O9   ds=42/43/45 template            Automate the monthly close to 3 days
id=182  O101 ds=45  in_app                        Cut cost-to-serve per invoice 20%
```

⭐ **Same `objective_id`, same `obj_key` hash, one row per DATASET VERSION.**
Objectives are **snapshot-scoped**: a re-upload mints new rows and the old ones
stay. **7 rows, 3 distinct texts, 3 of them on the active dataset (45).**

⛔ **So it is neither option the dispatch offered.** Not duplicate rows in the
defect sense, and not one row emitted repeatedly. **It is three legitimate rows
and a check that did not scope to the active dataset — my defect, in
`workspace.py`.**

## ⭐ THE RE-KEYING LANE IS EXONERATED BY THESE VALUES

The O112–O116 re-key changed **`objective_id`**. These rows carry **O2 and O9**
with **identical `obj_key` across all three snapshots** — so that lane did not
duplicate, and did not touch them. ⛔ **Nothing needs revoking, and no removal is
proposed**, because nothing in the data is wrong.

## ⭐ FIXED, RED-PROVED, AND CONFIRMED ON THE LIVE SURFACE

`for_department` now filters objectives, key results and KPIs to
`_active_company_dataset`. A test plants one objective on two stale snapshots and
the live one and asserts it is listed **once**; removing the filter fails it.

```
AFTER — Finance and Accounting, as the surface now reports it:
  1 x  Expand EBITDA margin by 400bps
  1 x  Automate the monthly close to 3 days
  1 x  Cut cost-to-serve per invoice 20%
  total items: 9   (was 15)
```

---

# T2 · THE FRACTION — 100% EITHER WAY

| scope | objectives with no project |
|---|---|
| ⛔ all snapshots (what the surface showed before the fix) | **47 / 47** |
| ⭐ **active dataset only — the true figure** | **26 / 26** |

Per department on the active dataset: **3/3** for eight departments, **2/2** for
Internal Audit.

⛔⭐⭐ **Not one objective in the company has a project beneath it.** The
objective→initiative link was never seeded, so **the workspace is correctly
reporting a real gap** and the fix is seeding, not the check.

⚠️ **27 live `GoalInitiativeLink` rows exist company-wide**, and none connects an
objective to an initiative *of the same department* — which is what the check
requires. **Not seeded here, per the dispatch.**

---

# T3 · ⛔ `.build-commit` IS READ, AND GITIGNORING IT HAS A COST

**Tracked deliberately, and it has exactly one reader** — `vite.config.ts:108`:

```ts
function resolveCommit(): [string, string] {
  return fromEnv() || fromGitDir() || fromGitBinary() || fromFile() || ["unknown", "none"];
}
```

⭐ `fromFile()` reads `.build-commit` as the **fourth and last fallback**, and its
value becomes **`/version.json`'s `commit`** — the exact marker
`check-deploy-version.py` asserts the deploy against.

⛔⭐⭐ **So gitignoring it trades one hazard for another.** A builder with no
`.git` directory, no git binary and no SHA in its environment would fall through
to `["unknown", "none"]` — and `check-deploy-version.py` treats
**`commit: "unknown"` as a FAILURE**, by design: *"it is not a pass; it is the
same silence the check exists to break."*

⚠️ **The hazard is real and structural**: the **post-commit** hook writes HEAD
*after* the commit, so the committed copy always lags by exactly one and the file
is dirty the moment any commit lands. Its own comment admits the lag — *"It can
lag by one commit — hence the source field, which says so plainly rather than
pretending to certainty."*

⭐ **In practice it is not currently load-bearing**: the live `/version.json`
reports `"source": "gitdir:ref"`, so `fromGitDir()` wins and the file is never
consulted. **But that is a fact about the current builder, not about all
builders**, and the fallback exists precisely for the one that differs.

⛔ **Reported, not changed.** Three options, none free: gitignore it and lose the
last fallback; move the write to **pre-commit** so the committed value matches
the commit; or leave it and keep resolving the conflict mechanically. **The
second is the only one that removes the dirt without removing the fallback**, and
its own comment already claims it is written by the pre-commit hook — **which it
is not.** That mismatch is worth a lane of its own.

---

# WHAT IS OWED

1. ⛔ **The objective→project link is unseeded across all nine departments** —
   26 of 26.
2. ⚠️ **`.build-commit`'s comment says pre-commit; the hook is post-commit.**
3. ⛔ `/version.json` serves `08a4694`; the frontend gate is still red.
