# Assessor comment drill-down — PART A REPORT

**Date:** 2026-07-29 · **Report before build.**

**Ruling being implemented:** verbatim comments are shown to the CXO. Anonymity
means the assessor's NAME is not shown. No further promise is made to assessors.

---

## A1 — What is stored on a comment

A comment is a **column on the per-item response row**, not an entity of its own.
`AssessmentResponse` (`accounts.py:310`):

| field | type | note |
| --- | --- | --- |
| `comment` | Text, nullable | the verbatim |
| `participant_ref` | String(64), indexed | **pseudonymous** (`P3`), minted at redemption |
| `item_id` | Integer | the L2 item — the axis link is via the item's `l1_code` |
| `score` | Integer, nullable | 1–10, NULL when abstained |
| `abstained` | Boolean | excluded from means |
| `department` | String(80), nullable | inherited from the participant |
| `seniority` | String(40), nullable | inherited (§4u band) |
| `cycle_id` | Integer, indexed | |
| `submitted_at` | DateTime | |

Plus `AssessmentOverall` — one end-of-questionnaire freeform comment per
participant per cycle, linked to `participant_ref` only.

**Not stored, and this matters for B1:**

* ⭐ **No per-comment tone.** There is no column and no derived field. See A2.
* **No stable comment id.** A comment is identified only by (row id, item).
* **No explicit ordering.** Order is query order, and the existing endpoint
  deliberately *shuffles* it (see A5).

⭐ **`participant_ref` is the identity risk, and it is pseudonymous, not
anonymous.** It is stable across a cycle, so the same `P3` appears on every item
that participant commented on. Two comments carrying the same ref can be joined
into one person's set of opinions — which, with `department` and `seniority` also
on the row, is a re-identification vector in a small department. The existing
endpoint already treats it that way.

---

## A2 — Tone is classified PER ITEM and PER CATEGORY. Never per comment.

`_sentiment_layer` (`accounts.py:11066`) groups comments by item, batches the
items under their L1, and calls `_anthropic_sentiment` once per L1. The
classifier receives `{code, title, comments[]}` and returns:

```json
{"category": {"sentiment": "...", "theme": "..."},
 "items":    {"<item_code>": {"sentiment": "...", "theme": "..."}}}
```

**Comments go in as a list; one verdict comes out per item and one per category.**
The individual comment's contribution is not recoverable — nothing is returned
per comment, and nothing is stored per comment.

⭐ **So B1's "each comment's own tone if it exists" — it does not exist.** The
finest granularity available is the **item (L2)** the comment sits on. The
drill-down will show the item's tone beside each comment and label it as the
item's tone. Presenting an item-level verdict as if it were the comment's own
would be a fabricated attribution — the reader would take "negative" to be a
judgement of the sentence in front of them when it is a judgement of the group.

Per-comment tone is buildable (one classifier call per comment, or a batch that
asks for per-comment verdicts) but it is a new AI cost and a new prompt contract,
and it is not in this lane.

---

## A3 — Every place the app states something the ruling makes false

**Three sites. The second is the one that matters.**

| # | file:line | text | audience |
| --- | --- | --- | --- |
| 1 | `SentimentPanels.tsx:110` | "Aggregate tone only — no individual comments are shown." | CXO |
| 2 | **`assess.tsx:702`** | **"anonymous — leadership sees aggregate results only"** | **the assessor, at the point of consent** |
| 3 | `SentimentPanels.tsx:3,8` | module docstring: "Aggregate comment TONE only — NEVER verbatim text" | developer |

⭐ **SITE 2 IS A PROMISE MADE TO THE PERSON WHOSE WORDS THESE ARE, IN THE FLOW
WHERE THEY DECIDE WHAT TO WRITE.** It is rendered by `IntroCard` before the
assessor answers anything. The dispatch asked for equivalent wording in the
respondent-facing flow specifically, and this is it.

Changing what the CXO sees without changing this sentence would leave the product
telling assessors their words stay aggregate while showing those words verbatim
to leadership. The ruling is explicit that anonymity means the NAME is not shown
and no further promise is made — so the sentence must say that, in the assessor's
own flow, before they write.

Proposed replacement, stated for the record rather than chosen unilaterally:

> **anonymous — your name is never shown; your written comments may be read by
> leadership**

That is the ruling, said plainly, at the moment it is relevant.

---

## A4 — The endpoint exists, and it cannot serve this surface

`GET /companies/{company_id}/assessment/cycles/{cid}/comments` (`accounts.py:11113`).

**Returns:** `by_item` (keyed `item_code`), `by_category` (keyed `l1_code` — this
IS the axis grouping), and `overall`. Each group carries `title`, `n` (distinct
participants), and `comments`.

**Three reasons it cannot back the drill-down as it stands:**

1. ⭐ **`require_company_admin`.** The sentiment tab it hangs off uses
   `_summary_access`, which is anonymous-readable. This endpoint is admin-only,
   so V2 (anonymous demo access) would 403. The drill-down needs an
   `_summary_access` route.
2. **Cycle-scoped, not axis-scoped.** It returns every axis at once. Workable —
   `by_category` is already the L1 grouping — but it ships the whole cycle's
   comments to render one axis.
3. **No tone, no score, no L2 decomposition.** It returns text only.

**So: a new endpoint, reusing this one's anonymity machinery rather than
reinventing it.**

---

## A5 — k-anonymity DOES apply to comments today

Two independent floors, both `KFLOOR = 3` (`assessment_engine.py:263`):

* **`/comments`** — `_emit` counts **distinct `participant_ref`** per group; below
  3 it emits `{"suppressed": true, "n": n, "reason": "below_anonymity_floor",
  "comments": []}` — the count survives, the contents do not. Same for `overall`.
* **`/assessment/sentiment`** — a department/seniority slice totalling under 3
  comments returns `suppressed` with a message.

And in anonymous cycles `/comments` additionally **omits `participant_ref`
entirely** and **shuffles** each group, so list order cannot reconstruct a person.

⭐ **The floor counts PARTICIPANTS, not comments.** One person leaving five
comments on an axis is n=1 and stays suppressed. That is the correct choice and
the drill-down must keep it: five comments from one identifiable person is a
worse exposure than five comments from five.

**This is the constraint V1 must be checked against.** Meridian / Strategy
Purpose & Governance is stated as 4 comments — if those come from fewer than 3
distinct participants, the honest result is *suppressed*, not four readable
comments. Verified at build time, not assumed.

---

## What Part B inherits

1. **New endpoint** under `_summary_access`, axis-scoped, reusing `_emit`'s floor
   and the anonymous shuffle. Never returns `participant_ref`, name, or email.
2. **Item-level tone**, labelled as such — there is no per-comment tone to show.
3. **L2 decomposition** is already computed (`item_sentiment`, `item_rag`,
   `item_divergence`, `item_dispersion`) — surfaced, not recomputed.
4. **Three copy sites** corrected, including the assessor-facing consent line.
5. **A real route with a URL** (B4), not a drawer — §4m.
