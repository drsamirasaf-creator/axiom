# The sidebar does not reflect the nav moves — because the moves were never made

**7 Aug 2026. DIAGNOSE ONLY. Nothing changed.** Both repos clean at start:
`axiom 16057ab` · `optimization-anchor aea73fe`, 0/0.

---

## T1 · It is (a). The moves never shipped.

### (a) Did the three nav moves ship? ⛔ **NO — and no commit contains them.**

The nav lane **stopped at its own T2 gate**: there is no stored plan or tier in
the product, so the PRO-tier gate the dispatch required could not be proven in
either direction. That was reported at `fc4bff8`. The following lane's T4 was not
started.

**The sidebar's three entries are exactly where they were**, read from
`AppLayout.tsx`:

| entry | section | still a top-level page |
|---|---|---|
| **SWOT & Risk** → `/swot` | ANALYZE | ✅ not tabs under Dashboard |
| **Prescience AI** → `/prescience-ai` | STRATEGIZE | ✅ not a tab under Optimization |
| **Monitoring** → `/twin` | EXECUTE | ✅ not a tab under PMO (`/initiatives`) |

⚠️ **Worth naming: "Monitoring" is `/twin`.** There is no `monitoring.tsx` route.
The label and the path differ, which matters for the move — the signpost has to
be left at `/twin`, and any lane searching for `/monitoring` will find nothing
and conclude the page does not exist.

⭐ **So the sidebar is correct today.** It faithfully renders three pages that are
still three pages. There is no drift to repair — only work not yet done.

### (b) Is the served bundle current? ⚠️ **NOT VERIFIED, and it cannot be the cause.**

The app root returns **HTTP 403** to an unauthenticated request, so I could not
read the deployed shell or its asset hashes. **I am not claiming (b) is clean.**

⭐ But it cannot be the cause: the source at HEAD still has all three as
top-level pages, so **even a perfectly current bundle would render the sidebar
exactly as it does now.** A stale bundle could only hide a change that exists,
and none does.

### (c) Is `nav-index.generated.ts` current? ⭐ **YES — byte-identical.**

Ran `python3 scripts/gen-nav-index.py` and diffed against the committed file:

| | |
|---|---|
| regenerated output | **identical, no diff** |
| destinations | **106** — 33 pages · 73 tabs |

The count is unchanged from the figure CORE has carried since the navigation
lane. The working tree was restored; nothing was committed.

> ### ⛔ **The cause is (a). Nothing to fix — the work is unstarted.**
> Fixing (b) or (c) would leave the defect and add a change, which is exactly
> what the dispatch's ordering exists to prevent.

---

## T2 · What the sidebar reads — ONE owner, with a generated projection

**The sidebar renders `businessSections`, a hand-maintained array in
`src/components/AppLayout.tsx:46`**, mapped at line 318.

⭐⭐ **And this is NOT the two-owners class, which is the answer I expected before
measuring.** `gen-nav-index.py` reads **both** `src/routes/` **and
`AppLayout.tsx`** — it locates `businessSections` (line 77) and derives from it.

| file | role |
|---|---|
| `AppLayout.tsx` → `businessSections` | **the single source of truth.** Hand-maintained. The sidebar renders it. |
| `nav-index.generated.ts` → `NAV_INDEX` | **a projection of it**, generated. Consumed by `NavSearch.tsx` **only** |

**So they cannot disagree in the way two hand lists would** — the index is
downstream, and `check-nav-index.py` fails the build if it drifts.

⛔ **What IS true, and is the finding worth recording:** the product's primary
navigation is a **hand-maintained array**. A nav move is a manual edit to
`businessSections`, and nothing derives that array from the routes — the
derivation runs the other way. The generated index will follow the edit; it will
not prompt it.

---

## T3 · Regeneration is enforced, not remembered

The dispatch's concern — *"a generated file that a human must remember to
regenerate is a hand-synced list wearing a generator's name"* — **does not apply
here.**

| | |
|---|---|
| `check-nav-index.py` | **regenerates and diffs** (`subprocess.run([GEN, "--check"])`) |
| wired into | **`.github/workflows/ci.yml:102`**, and reproduced by the pre-push replay |

⭐ So the index cannot silently go stale: a push that changed the sidebar without
regenerating would fail before it left the laptop. **That is why (c) came back
identical** — not luck, and not diligence.

---

## What this means for the nav-moves lane

The three moves are **unstarted**, and two things now sit in front of them:

1. ⛔ **The Prescience tier gate is still unresolved.** There is no stored
   plan/tier and no route gates on one, so moving Prescience under a
   Business-tier page changes nothing about who can read it — but it also does
   not fix that anyone already can.
2. ⚠️ **`check-inbound-refs` reads committed reports as a reference corpus.** It
   blocked a push last lane because a report named a `prescience` tab key that
   does not exist. **The signposts and the moves must land in the same commit**,
   or the guard will reject whichever arrives first.

⭐ And the sidebar edit itself is small: three entries in one hand-maintained
array. **The routing, signposts, inbound re-points and the `/dashboard?tab=urgent`
re-point are the work** — not the sidebar.

---

## What was written

**This report only.** No nav change, no regeneration committed, no fix. The
regenerated index was diffed in the working tree and restored.
