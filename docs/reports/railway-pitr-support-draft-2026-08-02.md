# DRAFT — Railway support report: `volumeInstancePITRRestore` cannot reach the pgBackRest catalog

**Status: DRAFT. Not sent.** Prepared 2026-08-02.

---

## Summary

`volumeInstancePITRRestore` has failed **ten times across two days** with an
identical error, against a Postgres volume that **has four backups, three of them
produced by Railway's own schedules**. The error describes itself as transient; it
is not.

We are not asking you to confirm a cause we have guessed at. **We do not know what
the mutation requires that is not satisfied here**, and the question at the end is
exactly that.

---

## Environment

| | |
|---|---|
| Workspace | `drsamirasaf-creator's Projects` |
| Subscription model | **TEAM** |
| `subscriptionPlanLimit.volumes.maxBackupsCount` | **10** |
| Project | `intelligent-gentleness` — `5145104d-831f-4271-bc97-e0301f3e539e` |
| Environment | `production` — `be4a60ab-9563-4ff8-a1a6-3458612894eb` |
| Services | `web` (`685900c2-a8c4-4cd8-8748-27965462068e`), `Postgres` (`e880b63f-0302-49db-9816-6d65251d0d87`) |
| Volume | `postgres-volume` — `15f477d0-78ba-4098-81be-dabbf33a492d` |
| **Volume instance** | **`16ab7d63-dd83-4f0e-ba38-d327fe1c47dc`** — state `READY` |

The Postgres service is healthy and serving production traffic throughout; the
application's `/health` returned **200** immediately before and after every
attempt.

---

## The backups that exist

Queried via `volumeInstanceBackupList(volumeInstanceId:)`:

| createdAt | referencedMB | kind | expiresAt |
|---|---|---|---|
| 2026-07-31T15:17:50.947Z | 249 | manual (`scheduleId: null`) | none |
| 2026-08-01T11:11:00.816Z | 250 | **scheduled — DAILY** | 2026-08-07T11:11:00.810Z |
| 2026-08-01T11:21:01.065Z | 250 | **scheduled — MONTHLY** | 2026-10-29T11:21:01.057Z |
| 2026-08-01T20:29:01.233Z | 250 | **scheduled — WEEKLY** | 2026-08-28T20:29:01.134Z |

Schedules, via `volumeInstanceBackupScheduleList(volumeInstanceId:)`:

| kind | cron | retentionSeconds |
|---|---|---|
| DAILY | `11 11 * * *` | 518400 |
| WEEKLY | `29 20 * * 6` | 2332800 |
| MONTHLY | `21 11 1 * *` | 7689600 |

All three schedules have produced a backup. The backup mechanism itself appears
to be working.

---

## The mutation and its arguments

Signature confirmed by schema introspection immediately before each round of
calls:

```
volumeInstancePITRRestore(
  newServiceName:   String
  sourceRepoPath:   String
  targetTimestamp:  DateTime
  volumeInstanceId: String
): WorkflowId!
```

Called as:

```graphql
mutation($n:String!, $t:DateTime!, $v:String!) {
  volumeInstancePITRRestore(
    newServiceName:   $n,
    targetTimestamp:  $t,
    volumeInstanceId: $v
  ) { workflowId }
}
```

with `v = 16ab7d63-dd83-4f0e-ba38-d327fe1c47dc` and a fresh, unused
`newServiceName` on every call.

**`sourceRepoPath` was not supplied.** It is nullable in the schema and we have no
documentation describing what value it expects. If it is required in practice,
that alone may be the answer — see the question below.

---

## The error, verbatim

Identical on every one of the ten attempts:

> `Couldn't reach the source service's pgBackRest catalog. This is usually
> transient (network or storage hiccup) — try again in a moment. If it persists,
> check that the source service is healthy.`

`extensions.code: INTERNAL_SERVER_ERROR`, `path: ["volumeInstancePITRRestore"]`.

---

## The ten attempts

**Round 1 — 2026-07-31, six attempts over roughly four minutes**, immediately
after the schedules were created (15:17Z) and the manual backup was taken. All
six returned the message above.
⚠️ **Trace IDs were not captured for these six.** They can be located by project
and environment within that window.

**Round 2 — 2026-08-02, four attempts between 04:58Z and 05:01Z.** Each used a
different `targetTimestamp`, chosen to test a different hypothesis about the
recovery window:

| # | targetTimestamp | why this instant was chosen | traceId |
|---|---|---|---|
| 7 | `2026-08-01T21:00:00.000Z` | ~31 min after the WEEKLY backup — a point that should be covered by both that base backup and subsequent WAL | `4112772726786148898` |
| 8 | `2026-08-01T20:35:00.000Z` | ~6 min after the WEEKLY backup — minimises reliance on WAL replay | not captured |
| 9 | `2026-08-02T04:00:00.000Z` | ~1 h before the call — the most recent plausible point | not captured |
| 10 | `2026-08-01T11:11:30.000Z` | 30 s after the DAILY backup's own timestamp — the instant most likely to sit on a base backup | not captured |

⚠️ We record honestly that **only attempt 7's trace ID was captured**. An earlier
call in round 2 (`616896639595253420`) was a **GraphQL validation error**, not a
catalog failure — it omitted the `{ workflowId }` selection set — and is **not**
counted among the ten.

The four timestamps span the entire window in which backups exist, from the
oldest scheduled backup to roughly an hour before the calls.

---

## What we ruled out, and how

**1. "No scheduled backup had run, so the pgBackRest stanza was never
initialised."**

This was our own recorded hypothesis after round 1 — written down explicitly as an
inference rather than a measurement, so that it could be tested.

**It is disproven.** Three scheduled backups have since run (11:11Z, 11:21Z and
20:29Z on 2026-08-01, 250 MB each). Round 2 was executed after all three, and the
error is byte-identical to round 1.

**2. "The chosen recovery point is outside the available window."**

Four different `targetTimestamp` values were tried, including one 30 seconds after
a base backup's own timestamp and one an hour before the call. All four failed
identically. A window problem would be expected to produce a different message, or
to succeed for at least one of them.

**3. "The source service is unhealthy", as the error suggests.**

The `Postgres` service is `READY`, the volume instance is `READY`, and the
application served production traffic — `/health` 200 — before, during and after
both rounds. Row counts and content hashes across 101 tables were identical before
and after, so nothing about the source was disturbed.

**4. "It is transient."**

Ten identical failures across two days, two rounds separated by ~38 hours, and
four distinct recovery points. We have stopped retrying.

**5. Plan limits.**

`maxBackupsCount` is **10** on the current plan and four backups exist, so we are
not at a limit. (Our own notes record this workspace as `PRO`; the API reports
`TEAM`. If that distinction matters to PITR entitlement, please say so.)

---

## What we did *not* do

`volumeInstanceBackupRestore(volumeInstanceBackupId, volumeInstanceId)` **was never
called.** It takes no target parameter, and with a single volume instance we read
that as restoring in place — over the production database. If that reading is
wrong, we would like to know, but we were not willing to test it on a live system.

No `pg_dump` workaround was used. A dump-and-load would demonstrate that
`pg_dump` works; it would not demonstrate that **Railway's backups restore**,
which is the only thing we are trying to establish.

---

## The question

**What does `volumeInstancePITRRestore` require, for this volume instance, that is
not currently satisfied?**

Specifically, if any of these is the answer, that would fully resolve it:

- Is `sourceRepoPath` required in practice, and what value should it take?
- Does PITR require something beyond the scheduled volume backups we have — a
  separate WAL-archiving or stanza-initialisation step we have not performed?
- Is PITR available on the `TEAM` model for this volume type at all?
- Is there a way to query whether a pgBackRest catalog exists for a volume
  instance? We found no such field in the schema, so we cannot tell from the API
  whether the precondition is met before calling.

We have deliberately not proposed a cause. Our one hypothesis was recorded, tested
and disproven, and we would rather you diagnose from the evidence than confirm a
second guess.

---

## Why this matters to us

We hold backups we have never restored. Until a restore is demonstrated end to
end, our recovery-time objective is unknown — not long, not short, **unmeasured**
— and the backups remain a hypothesis rather than a guarantee. That is the state
we are trying to leave.
