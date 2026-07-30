# Recoverability audit — could a stranger rebuild AXIOM from the repos alone?

Read-only survey. Nothing changed. Gaps only — what is present is not listed.

**Short answer: no, not without you.** The application code is recoverable. The
*environment* is not, and the demo surface is not. Ranked by what breaks first.

---

## GAP 1 — No environment manifest. 58 variables, none listed. ⭐ BREAKS FIRST

**Missing:** any `.env.example`, `.env.sample` or equivalent in either repo.

**Measured:** 58 distinct variables are read by `os.environ` / `getenv` across
`services/` and `scripts/`. Documentation coverage, by grep across `README.md`
and `docs/`:

| variable | class | documented in |
|---|---|---|
| `DATABASE_URL` | boot-blocking | **0 files** |
| `AXIOM_SECRET` | boot-blocking (auth) | 2 |
| `R2_BUCKET`, `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` | document storage | **0 files** |
| `RESEND_API_KEY`, `MAIL_FROM` | all outbound mail | **0 files** |
| `SENTRY_DSN` | monitoring | 0 |
| `ANTHROPIC_API_KEY` | Prescience, doc intel | 3 |
| `STRIPE_*` (4 vars) | billing | 2 |

**What breaks:** the process does not start without `DATABASE_URL`. With it but
without `AXIOM_SECRET`, auth is undefined. With both, uploads 503 and mail is
silently dead — those two fail *quietly*, which is worse than not booting.

**⭐ And the Railway-only class is worse than undocumented — it is anecdotal.**
`FORWARDED_ALLOW_IPS=*` exists in exactly one place: a narrative paragraph in
`docs/ledger/AXIOM_LEDGER_ARCHIVE.md:925`, describing the incident that caused
it. It is in no setup document. Railway ignores the `Procfile`, so the
`--forwarded-allow-ips="*"` flag written there is **not what is actually
running** — the platform env var is. A rebuilder reading the Procfile would
conclude, wrongly, that it is handled.

**Work to close:** ~1 hour. The 58 names are already enumerable by grep; the
judgement needed is which are required vs optional, and which platform settings
have no in-repo representation at all.

---

## GAP 2 — `requirements.txt` pins nothing. ⭐ 0 of 20 lines carry a version

**Missing:** version pins and a lockfile on the Python side.

    pinned (==) in requirements.txt : 0
    total lines                     : 20

**What breaks:** a rebuild resolves whatever is newest that day. This codebase
is sensitive to it — `openpyxl` shapes the template writer, `pydantic` v2
semantics run the response models, SQLAlchemy 2.x styles the models. A rebuild
six months from now silently gets different libraries than production runs.

Not hypothetical for this repo: the frontend already carries a 24-hour
supply-chain guard (`bunfig.toml: minimumReleaseAge = 86400`) precisely because
unpinned resolution is understood to be a risk there. The backend has no
equivalent.

**Contrast:** the frontend **does** commit `bun.lock`. Only the backend is
unpinned.

**Work to close:** ~30 minutes to `pip freeze` a known-good set; longer to
decide floor-vs-exact per package.

---

## GAP 3 — The demo surface is not reproducible. Meridian is half-seeded

**Present and working:** `seed_showcase()` is called at boot from
`core/db.py:62-63`, so **company 20, its datasets and its documents rebuild
automatically**. The assessor commentary is hardcoded in `accounts.py` and
rebuilds with it.

**Missing:** the assessment cycle and its respondents. Those are created by
*calling API endpoints with request bodies that exist nowhere in the repo*:

| endpoint | body | in repo? |
|---|---|---|
| `seed_assessment_history` | `SeedHistoryIn{cycles: [...]}` | **no** — caller supplies every cycle |
| `seed_assessment_invites` | `SeedInvitesIn{invites: [...]}` | **no** — caller supplies all 30 |
| `seed_assessment_comments` | `SeedCommentsIn{dry_run}` only | yes — text is in the source |
| `seed_okrs` | `SeedOkrIn` | **no** |

**What breaks:** a rebuilt Meridian has a company, financials and documents — and
no assessment cycle, no 30 banded respondents, no CEI, no sentiment, no
seniority gap. Roughly half the demo, including every surface built in the
assessment lanes.

⭐ **The 7 departments could not be confirmed as seeded from committed code.**
The only department list in the repo is `participant_upload.SAMPLE_DEPARTMENTS`
— four placeholders named "Department A".."D", which is a *template* fixture,
not Meridian's org chart. Meridian's real departments appear to exist only in
production.

**Work to close:** ~half a day. The bodies must be recovered from the live
database (they are still there) and committed as fixtures, then a
`seed_showcase_assessment()` written to apply them at boot beside the existing
seed.

---

## GAP 4 — 75 of 86 tables have no migration. The history does not rebuild the schema

**Present:** Alembic is configured and committed — `alembic.ini`, 14 revisions in
`migrations/versions/`.

**Missing:** migrations for almost everything. There are **two declarative
bases**:

| base | tables | how the schema is made |
|---|---|---|
| `core/db.py:18` `Base(DeclarativeBase)` | 11 | Alembic revisions |
| `accounts.py:40` `declarative_base()` | **75** | `Base.metadata.create_all(engine)` at boot, `accounts.py:13012` |

Plus `_ensure_ax_columns()` at `accounts.py:12810`, which issues **80 additive
`ALTER TABLE`s** at boot for columns added after their table already existed.

**⭐ The good news, measured rather than assumed: the live schema matches the
models exactly.**

    live tables                       87  (86 + alembic_version)
    columns live but in no model       0
    tables live but in no model        0

So nothing was made by hand in production, and a clean boot *does* produce the
right schema. **This gap is not "the rebuild fails" — it is "the rebuild works
for a reason nobody can review."**

**What breaks:** not the rebuild. What is missing is the *surface*: 75 tables
have no schema history, so there is no down-migration, no record of when a
column appeared, no diff to review before a schema change ships, and no way to
stage one. The 27 Jul outage — a model column that `_ensure_ax_columns` never
learned about — is exactly the failure this absence permits, and it is the
second time that pattern has been paid for.

**Work to close:** ~1 day to autogenerate a baseline revision from the models and
stamp existing deployments. It buys reviewability, not recoverability.

---

## GAP 5 — Third-party accounts are unnamed. Four services, no setup path

**Missing:** any document naming what external accounts are required.

| service | used for | named in README/docs |
|---|---|---|
| Cloudflare R2 | every uploaded document and generated report | **no** |
| Resend | all outbound mail — invites, verification, resets | **no** |
| Sentry | error monitoring | **no** |
| Anthropic | Prescience, document intelligence, sentiment | yes (1 file) |
| Stripe | billing | yes (`docs/BILLING_SETUP.md`) |
| Railway | hosting, Postgres | yes (2 files) |

**What breaks:** R2 and Resend fail *quietly*. Uploads return 503 with
"Document storage is not configured", which reads as a bug rather than a missing
account. Mail simply never arrives — no invite, no verification, no reset — and
nothing in the UI says why.

**Work to close:** ~2 hours of writing, assuming the account owner is available
to say which plan and which bucket.

---

## GAP 6 — The frontend build depends on a vendor-hosted registry

**Missing:** any note that the build resolves packages from outside public npm.

Six `@lovable.dev/*` packages resolve from
`https://europe-west{1,4}-npm.pkg.dev/lovable-core-prod/sandbox-npm-cache/` — a
Google Artifact Registry owned by Lovable, recorded in `bun.lock`. One of them,
`@lovable.dev/vite-tanstack-config`, is imported directly by `vite.config.ts`
and supplies the nitro, TanStack Start and Tailwind plugin chain. **The app does
not build without it.**

**Measured, so the severity is honest:** the tarballs are fetchable
**anonymously** — HTTP 200 without credentials. So this is *not* an auth
lock-in today.

**What breaks:** nothing today. It is a single vendor-controlled point of
failure with no mirror and no vendored copy, on the critical build path. If that
registry goes away, `vite.config.ts` has no substitute in the repo.

**Answering the question directly:** Lovable is a **build** dependency, not only
an editing one. Two-way sync is for editing; the config package is required to
compile.

**Work to close:** ~1 hour to vendor the config package, or a note recording the
exposure. Replacing it is larger — it would mean rebuilding the plugin chain.

---

## GAP 7 — Frontend environment and build docs

**Missing:** `.env.example` in `optimization-anchor`; `VITE_FX_API_KEY` (the only
`import.meta.env` variable read by `src/`) is documented nowhere. `README.md` is
29 lines.

**Present:** `bun.lock` is committed, and `package.json` carries the working
scripts (`build`, `build:preview`, `preview:static`).

**Work to close:** ~30 minutes.

---

## Nothing dangerous is gitignored

`.gitignore` covers `__pycache__/`, `*.pyc`, `.venv/`, `*.db`, `.pytest_cache/`,
`.env`. Only `.env` is runtime-required, and that is Gap 1 by another route.
Untracked files on this machine are local databases and caches — nothing needed
to run.

---

## Ranked

| # | gap | breaks | effort |
|---|---|---|---|
| 1 | no env manifest (58 vars) | **process will not start** | ~1h |
| 2 | requirements.txt unpinned | build is not reproducible | ~30m |
| 3 | assessment seed not in repo | half the demo missing | ~half day |
| 4 | 75 tables outside Alembic | schema unreviewable, not unbuildable | ~1d |
| 5 | third-party accounts unnamed | uploads and mail fail silently | ~2h |
| 6 | vendor registry on the build path | single point of failure | ~1h to record |
| 7 | frontend env + thin README | frontend misconfigures quietly | ~30m |

**Roughly two days closes 1, 2, 3, 5, 6 and 7** — everything that stops a clean
rebuild reaching a running system with a complete demo. Gap 4 is a separate day
and buys reviewability rather than recoverability.

⭐ The pattern across all seven: **the code is in the repo and the knowledge is
not.** Every gap is something that lives in your head, in Railway's dashboard, or
in a session transcript — and each is individually an hour or two to write down.
