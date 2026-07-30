# The reseed hypothesis — BLOCKED ON THE INSTRUMENT

Report only. **Stopped rather than worked around**, per the constraint.

**Verdict: UNDECIDABLE from available evidence** — for two independent reasons,
one of which would hold even with a working database client.

---

## 1. The instrument is still down

    PSYCOPG UNAVAILABLE: ImportError: no pq wrapper available
      - couldn't import psycopg 'c' implementation: No module named 'psycopg_c'
      - couldn't import psycopg 'binary' implementation: list index out of range
      - couldn't import psycopg 'python' implementation: libpq library not found

The single pull was attempted once and failed. **No workaround attempted** — no
alternative driver, no psql shell-out, no partial substitute. An unreliable
instrument has already cost three lanes, and a fourth lane built on a
hand-rolled substitute would be worse evidence than none.

**The bucketing of the 42 against per-dataset reseed events was not performed.**

## ⭐ 2. The direct evidence does not exist, and this is a repo fact not a query

The dispatch asked whether datasets 3 and 45 carry a timestamp indicating when
their payload was last written.

**They do not.**

    FinancialDataset columns: … uploaded_at, created_at …          (no updated_at)

Neither carries `onupdate`; both are set at insert. And the showcase backfills
mutate the payload with

    row.data = data
    flag_modified(row, "data")     # JSON column dirty flag
    db.commit()

⭐ **`flag_modified` bumps no timestamp.** A payload rewritten at boot leaves
`created_at` and `uploaded_at` exactly as they were. **So the direct evidence is
structurally unavailable — a working psycopg would not have produced it.**

## 3. What the repo does establish

### Candidate reseed events (from `seed.py` history)

    2026-07-25 03:16  a7a7b89  Urgent Items I4 + demo I5 seed
    2026-07-25 03:28  0138c31  Revert PART C demo-I5 seed: live active dataset is
                               NOT the meridian() fixture
    2026-07-25 03:40  177634c  ⭐ Capture prod dataset 45 into seed:
                               meridian_with_management_plan()
    2026-07-25 03:43  b52c31b  harden management-plan backfill
    2026-07-30 16:03  40f7e94  extract company creation from the logo backfill

**A dense cluster on 25 Jul 03:16–03:43, one commit naming dataset 45
explicitly.** This is the reseed window the hypothesis proposes.

### The one clause that can be checked without a query

From the prior lane's already-measured spans (`80e5a50`, not re-derived here):

    DIVERGE (42)     2026-07-14 .. 2026-07-24
    reproduce (345)  2026-07-14 .. 2026-07-30

⭐ **Every divergent run predates the 25 Jul 03:16 cluster.** The divergent span
ends 24 Jul; the cluster begins the next morning. **Consistent with the
hypothesis.**

### The clause that cannot be checked, and why it is the one that matters

The test requires **both** halves: every divergent run predates a reseed **and no
reproducing run does**.

286 of the 345 reproducing runs also predate 28 Jul. Whether they predate a reseed
**of their own dataset** is exactly the unanswered question — it needs per-dataset
reseed attribution crossed against per-run dataset membership, which is the query
that could not run.

**Without it the observation is a correlation with a date, not a discrimination.**
The prior lane already produced one clean date split that turned out to be a
symptom rather than a cause (the quarterly fix, refuted by frequency), so a second
unverified date split should not be promoted to a finding.

## 4. One candidate mechanism excluded from the repo

`seed.py:106-113` mutates **stored ValuationRun results**:

    for vr in db.query(ValuationRun).filter_by(tenant=SHOWCASE_TENANT).all():
        if res.get("subject") in _NAME_MAP:
            res["subject"] = _NAME_MAP[res["subject"]]
            flag_modified(vr, "result")

⭐ Worth knowing that the seed rewrites stored run results at all — but it
rewrites **`subject`, a company-name string**. It cannot move an enterprise
value. **Excluded as the numeric cause.**

---

## Verdict

| | |
|---|---|
| Hypothesis | **UNDECIDABLE from available evidence** |
| Supporting | every divergent run predates the 25 Jul reseed cluster; divergence confined to showcase datasets, which are the only ones mutated at boot; one seed commit names dataset 45 |
| Missing | the second clause — that no reproducing run predates a reseed of *its own* dataset |
| Blocking | psycopg unavailable; **and** no payload-write timestamp exists, so the direct evidence cannot be obtained even with a working client |

**What would settle it, when the client is available:** bucket both populations
per dataset against that dataset's own reseed events. If the reproducing runs sit
on datasets never touched by a backfill and the divergent ones do not, the
hypothesis is established without a bisect.

**What would settle it independently of the client:** a payload-write timestamp
or a payload hash on `FinancialDataset` — which does not exist today, and whose
absence is itself the reason this class is hard to diagnose after the fact.

No remediation. No build.
