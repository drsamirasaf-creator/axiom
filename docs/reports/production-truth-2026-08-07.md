# Production truth — what is served, and does it answer

**7 Aug 2026. READ-ONLY lane. No code changed, no production write.**
Heads at start: backend `215c74f` · frontend `10a1818`, both clean and in sync.

---

## 1 · What production is serving

⭐ **The dispatch's hypothesis is false, and that changes the action.** Production
is **not** at `265aff5`.

| | |
|---|---|
| Railway project · environment · service | `intelligent-gentleness` · production · `web` |
| **active deployment** | **`215c74f`** — status **SUCCESS**, built 6 Aug 20:03 UTC |
| every earlier deployment | **REMOVED** (superseded), including `37ce7c6`, `265aff5`, `a652732` |

`215c74f` contains `37ce7c6`. **The frequency-view fix is deployed. No redeploy is
needed, and no code change is needed** — the action is neither.

⭐ Railway deploys **per push to `main`**: twenty deployments are recorded and each
maps to a commit, so "is production current" is answerable from the deployment
list alone and does not require inference from behaviour.

---

## 2 · The paired READ against the served host

Verification READ only. **Auth mode: unauthenticated — no `Authorization` header
sent.** Dataset 45 is the showcase, which `require_report_read` admits anonymously
by design so the public demo works.

| endpoint | status | bytes | populated? |
|---|---|---|---|
| `/api/v1/financials/datasets/45/frequency-view` | **200** | 4,916 | **yes** |
| `/api/v1/financials/datasets/45/derived` (control, §8p) | **200** | 3,852 | **yes** |

⭐ **A 200 is not population, so the payloads were read.**

**frequency-view** — `base_frequency: annual`, `view: annual`,
`interpolated: false`; the view strip correctly reports **monthly and quarterly
disabled** for an annual dataset and annual enabled; **10 buckets, 2021–2030**;
real figures in all three blocks (income statement, balance sheet, cash flow).

**derived** — 10 years, `revenue`, `ebit`, `nwc` each carrying 10 values.

Both answer. The §8p defect is closed **in production**, not merely at HEAD.

### ⚠ One finding the payload surfaced

`unclassified: ["cash_flow.net_borrowing"]`.

The frequency view **drops** that line and **says so** — the designed path when a
statement line has no registry token (§8o ruling 3: nothing infers an aggregation
rule from a name). ⛔ But it is a real coverage gap: **`cf.net_borrowing` has no
vocabulary token**, so it is absent from every frequency view. It is one line of
one block, and it is reported rather than guessed at — which is the discipline
working, and also a gap worth closing.

### ⭐ A tenant-isolation control, obtained in passing

The same path, same unauthenticated mode, against a **non-showcase** dataset
returns **404 `dataset not found`** — no payload. The showcase exemption does not
widen to customer data. Recorded because the anonymous readability of dataset 45
would otherwise read as a hole.

---

## 3 · Frontend head

| | |
|---|---|
| HEAD | `10a1818` — *"The strategy map's edges were drawn in the background colour"* |
| behind `origin/main` | **0** |
| ahead of `origin/main` | **0** |
| stash entries | **0** |
| working tree | clean |

Measured **separately**, as required: there is no Lovable divergence to resolve,
and nothing was auto-resolved. Backend likewise `215c74f`, 0/0, clean.

---

## 4 · What was written

This report only. **No code, no schema, no production write, no repository setting
changed.** One finding from this lane is deliberately **not** recorded here and was
reported in chat instead, because committing it would extend the exposure it
describes.
