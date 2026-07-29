# Two outstanding items — report only, nothing fixed

**Date:** 2026-07-29

---

## 1. The demo-ranking suite failure — **a real defect, in the seed data**

Neither a stale expectation nor a rendering bug. The check is correct, the code
is behaving as documented, and the thing the check exists to catch has happened.

### Evidence chain

**The API is clean.** `GET /companies/20/initiatives` (Meridian, the one live
showcase — 21 and 22 are in `RETIRED_SHOWCASE_IDS`) returns 15 rows, every
`ref_code` letter+number: A1–A14 and B1. **Zero bare codes.**

**The DOM is not.** 15 `span.font-mono.bg-secondary` badges, 15 matching
`^[A-Z][0-9]*$`, **6 bare `A`** — and each is attached to a real initiative row,
not a band-section header:

    Yield & scrap reduction program · Overtime normalisation ·
    Retention & engagement program · Hiring pipeline acceleration ·
    Board governance cadence reset · EU market entry program

**The join is exact.** Those six titles are precisely the six rows with
`rank IS NULL` — `ref_code` A9, A10, A11, A12, A13, A14.

### Why the page shows `A` when the API says `A9`

`accounts.py:5704`:

```python
def _display_code(i):
    """Within-band display code = band letter + rank ("A1", "B3"); unranked → band
    letter alone ("A"). The band comes from the CURRENT priority/status."""
    band = _band_of(i.status, i.current_priority)
    rank = getattr(i, "rank", None)
    return f"{band}{rank}" if rank else band
```

The frontend renders `{row.display_code ?? row.ref}` (`initiatives.tsx:632`) and
faithfully prints what it is handed. `display_code` is `"A"` — non-null, so the
`??` fallback to `ref` never fires.

⭐ **There are two codes with different completeness guarantees.** `ref_code` is
minted at creation by `_next_ref` and is always letter+number. `display_code` is
derived per-request from band+rank and degrades to a bare letter. The check
asserts the second is always complete; the backend documents that it is not.

### So who is wrong? — the data

The check's own comment settles it:

> *Guards the showcase against a future seed edit reintroducing an unranked
> initiative.*

It is not asserting `_display_code` is wrong. It is asserting **the showcase seed
contains no unranked initiative**, and 6 of 15 now are. The guard fired for
exactly its stated reason. The fix is a ranking pass over Meridian's A-band, not
a code change — and it needs a named write lane.

### Two things noticed while pinning this, neither chased

* **`if rank` is falsy-not-null.** `rank = 0` renders a bare band letter too.
  The column comment says `rank (1..N); null = unranked`, so 0 is out of
  contract today — but it is the same falsy-vs-`None` trap this codebase has
  been bitten by before, one seed edit away from mattering.
* **Two surfaces prefer different fields.** The list badge renders
  `display_code`; `LeaderInitiatives.tsx:83` renders `i.ref || i.ref_code || String(i.id)`.
  For an unranked initiative those disagree — `A` in one place, `A9` in another,
  same row. Not verified end-to-end on screen; flagged, not claimed.

---

## 2. The three frontend gates have nowhere to run

`check-no-ts-period-format.py`, `check-period-labels-consumed.py` and
`check-period-labels-published.py` live in `axiom/scripts` and read the sibling
`optimization-anchor` checkout through `AXIOM_FRONTEND`. On a GitHub Actions
runner for the axiom repo that sibling does not exist, so all three skip.
`check-no-ts-period-format` has been wired into `ci.yml` since it was written and
**has never checked anything**.

(Two of the three no longer print a success line when they skip — that was fixed
in `e87b392`. The skip itself is unchanged.)

### The options, with their real costs

| # | Approach | Cost | What it actually buys |
| --- | --- | --- | --- |
| 1 | **Cross-repo checkout in axiom CI** — `actions/checkout` with `repository: drsamirasaf-creator/optimization-anchor` + a PAT or deploy key in secrets | one credential to create, store and rotate | Real enforcement on every backend PR. **The only option that catches the failure that fails open** — see below |
| 2 | **Move the gates into the frontend's CI** | same credential problem, mirrored — they need the *backend* source for the emitter cross-check | nothing net |
| 3 | **Pre-push hook in both repos** | none | Enforcement where both checkouts exist, which is where the work actually happens. **Not versioned, not shared by clone, bypassable with `--no-verify`** |
| 4 | **Scheduled cross-repo job** | same credential as 1 | catches drift late, cannot block a push |

### Recommendation

**A pre-push hook now (3), and treat (1) as the real answer when you want to
spend the credential.**

The hook fits how this project actually runs — one machine, both repos checked
out side by side, every session ending in a pushed `origin/main`. It costs
nothing and closes the gap today.

⭐ **But state its weakness rather than discover it later:** a hook is local. It
protects this machine and nothing else, and `--no-verify` walks past it. It is a
floor, not a gate.

⭐ **And the part that most needs option 1 is the backend-emitter cross-check.**
`check-period-labels-published.py` fails hard when a sixth `period_labels`
emitter appears — that is the check whose absence *fails open*, because a new
backend emitter with no frontend publisher is exactly the defect this lane just
fixed, and it originates in the backend repo where the gate is currently inert.

### Either way, one thing should change regardless

`ci.yml` currently runs `check-no-ts-period-format.py` and goes green. Whatever
is decided about the credential, that step should say plainly that it does not
enforce anything without a frontend checkout — otherwise a green CI reads as
coverage the run did not have. That is the same false-claim shape `e87b392`
removed from the gates' own output.

---

Nothing built. Both items await a ruling.
