# "One drawer per page session" — the pattern was not real

**Diagnosis only. Nothing fixed, nothing retried.** 5 Aug, on `766f21d` / `409f3a4`.

---

## ⭐⭐ THE HEADLINE: NO SUCH BEHAVIOUR EXISTS, AND I INVENTED THE MECHANISM

Four measurements, all against the shipped tree:

| sequence | result |
|---|---|
| ⭐ **human path** — open drawer, close it, open another | ✅ **works.** Second drawer opens and shows the second project |
| ⭐ **the harness's exact path** — nav → click → nav → click | ✅ **works.** Both drawers open |
| ⭐ **fresh page per project** — new page, seat, click | ✅ **works.** Both pages seat, both rows present |
| tree state at `409f3a4` | ✅ **genuinely clean** |

**There is no "first opens, second never does."** The product does not do it, and
neither does the sequence I said reproduced it.

---

## 1 · Does a human see it? — ⛔ NO

Measured directly: click *Platform v2 re-architecture* → drawer opens → click the
close control → drawer closes → click *Platform v2 migration wave 1* → **drawer
opens and renders the second project.**

⭐ **This is not a product defect on the Projects page.** Had it been one it would
have outranked the Gantt entirely, which is why it was worth testing first.

---

## 2 · The mechanism — ⭐⭐ THREE DIFFERENT HARNESS BUGS, READ AS ONE

The four attempts did not share a cause. Each failed for its own reason, and the
**identical symptom** made them look like one mechanism:

| attempt | what it did | why it failed |
|---|---|---|
| 1 | `?open=36` (a row id) | ⛔ `?open=` matches **`ref`**, not id — `items.find(i => i.ref === search.open)` |
| 2 | `?open=A7` | the effect fires only once `items` has loaded; asserted before that settled — **a race** |
| 3 | click row by title | ⛔ the second title was *"Dynamic pricing **&** packaging revamp"* — an `&` in a Playwright `text=` selector |
| 4 | fresh page + `seat()` | ⭐⭐ **`seat()`'s return value was never checked.** It was called bare while every other precondition in that file was wrapped in `check()` |

⭐⭐ **AND THE GENERALISATION WAS THE REAL ERROR.** Three unrelated bugs produced
one symptom, and I wrote *"the pattern is the session, not the project"* — a
mechanism, stated with confidence, that no measurement supported. **A repeated
symptom is evidence of a repeated OBSERVATION, not of a repeated cause.**

⛔ **The `data-project-tab` probe the failing assertion waited on existed only in
the unpushed build**, so the exact failure cannot be re-run against the reverted
tree. That is a consequence of reverting, and it is the correct trade: an
unproven build should not sit in `main` to keep a harness reproducible.

### What the drawer state actually does

`initiatives.tsx`: `drawer` (the target) and `openDId` (visibility) are separate,
the render guard is `{drawer && openDId && …}`, and `onClose` sets **only**
`openDId = false`.

⭐ **So a closed drawer retains its stale target.** It is benign today — every row
click sets *both* — and it is **not** what was observed. Recorded as an
observation, not a defect, because a future path that flips `openDId` without
setting `drawer` would reopen the previous project.

---

## 3 · What "fresh page per project" means — ⭐ THE MOST INFORMATIVE FACT

The dispatch is right that this is the decisive one.

A fresh page defeats **all** component state, and the module-scoped active-company
store with it. **It still failed.** ⭐⭐ **That should have ruled out "session
state" immediately — and instead it was read as confirming a stronger version of
the same theory.**

Measured now: **both pages seat successfully, both rows are present.** So the
fresh-page attempt failed on something the attempt itself introduced — the
unchecked `seat()` — and not on anything it was meant to isolate.

⭐ **An experiment designed to eliminate a hypothesis, which fails, has either
eliminated it or is broken. It cannot confirm it.** Treating the failure as
support for the hypothesis inverted the logic of the test.

---

## 4 · The tab strip — ⭐ clean, verified

At `409f3a4`:

    ProjectSchedule.tsx        absent
    data-project-tab           0 matches
    data-schedule              0 matches
    git diff origin/main       empty
    src/components/initiatives/  AssignLeaderDialog · LeaderInitiatives ·
                                 LiveProposalsInbox · PortfolioCockpit ·
                                 ProjectExecution

**Nothing was left behind.** The nested-strip mistake — a second tab bar inside
`ProjectExecution` when the drawer already had one — was reverted with the rest.

---

## ⭐ WHAT THIS COSTS, AND THE CLASS IT BELONGS TO

§III.11 recorded an assertion that **fails when everything rendered**. This is the
next turn of the same screw: **four assertions that failed for four reasons, and a
mechanism asserted to explain all four.**

⛔ **The diagnosis was written before the measurement.** The previous lane's
correction was *diagnose rather than retry* — and this lane's report obeyed the
letter of it (it stopped) while breaking the substance (it stated a cause it had
not tested). ⭐ **Stopping is not the same as diagnosing.**

**What would have caught it:** running the human path first. It takes one minute,
it is the question that decides whether anything else matters, and it was
available at every one of the four attempts.

---

## Not fixed

No harness re-run, no rebuild, nothing pushed to the frontend. Both repositories
are clean at `766f21d` / `409f3a4`. ⭐ **The Gantt build remains unlanded and its
absent-path assertion remains unproven — but the reason is now known to be a
harness composition error, not a product behaviour.**
