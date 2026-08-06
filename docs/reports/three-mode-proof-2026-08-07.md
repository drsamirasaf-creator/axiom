# Three-mode proof — T1 does not clear. T2 not run.

**7 Aug 2026.** Heads at start: backend `c53713b` · frontend `2605c28` — clean,
**0 ahead, 0 behind**, no stash, measured separately.

---

## T0 · The prose pair — it was NOT recorded. It is now.

`2605c28` recorded the **stroke** exemptions, a different guard. The two prose
matches from the production-truth lane existed **only in a chat message**; no
guard, no baseline, no file.

New: **`scripts/check-report-exposure.py`**, wired into CI.

⭐⭐ **The judgements were right and the instrument was wrong**, and both are now
recorded:

| match | judgement, recorded |
|---|---|
| `"public demo"` | describes **why** dataset 45 is anonymously readable — the showcase exemption in `require_report_read`. A statement about a product decision, not about the repository. |
| `"exposure"` | the sentence saying a finding was **deliberately withheld** and reported in chat. Naming the withholding is the honest act; deleting the pointer would leave a reader unable to tell the report is incomplete by design. |

⛔ **And the original instrument could not have been the guard.** It grepped
`public\|visibility\|private\|exposure` — and `public`/`private` are core **domain**
vocabulary here. Measured: `value-per-share-2026-08-03.md:174` says *"No live
dataset is public"*, meaning a **public company**. A recogniser that floods on
domain language gets muted, so the shipped pattern is phrase-scoped to repository
visibility and flags **neither** of the two.

They are therefore recorded as **HISTORICAL**, not as live overrides — an override
list must measure the present, and neither is a present hit. **148 reports scanned,
0 live matches.** Red-proofed: inserting *"The repository is public"* into a report
fails the gate.

---

## ⛔ T1 · Does not clear. STOP.

The dispatch cites lines 1289/1293; the live references are **17, 1509, 1535**.

| mode | mechanism | obtainable without `AXIOM_SECRET`? |
|---|---|---|
| **operator** | `OPERATOR_TOKEN` as a pasted input **is gone**. `mint_operator_token.mint()` builds a fresh 15-minute JWT | ⛔ **No.** Its own docstring: *"signed with **AXIOM_SECRET**"*, read from the Railway environment |
| **member** | `MEMBER_TOKEN` read from `os.environ` | ⛔ **No.** Not set locally, **not a repository secret**, and the code itself skips with *"f4 account pending"* |

**Where demo-rot gets credentials:** three GitHub Actions secrets —
`AXIOM_CRAWL_BASE_URL`, `AXIOM_CRAWL_EMAIL`, `AXIOM_CRAWL_PASSWORD`. **An
email/password pair, not tokens.** Enumerated by name via the authenticated API:
**3 secrets exist; `MEMBER_TOKEN` and `OPERATOR_TOKEN` are not among them.**

⭐ **There is exactly one route to a token without the signing key, and it is not
available to this lane:** a run **inside CI**, where those three secrets are
injected and `crawler-login.py` signs in through the browser. GitHub secrets are
write-only to the API, so a local lane cannot read them.

**Which company does the member token belong to?** ⛔ **None — it does not exist.**
The account is marked *pending* in the code. A member of the wrong enterprise 404s
correctly and proves nothing; a member that was never provisioned proves less.

> ⚠️ **This is the founder decision the dispatch anticipated.** Whether lanes get
> read-only member and operator tokens is unruled. **I did not mint, and I did not
> fetch `AXIOM_SECRET`.**

## ⛔ T2 · Not run

T1 gates it. `frequency-view` was **not** added to `auth-regression.py`: adding a
path to a crawler that cannot authenticate would put an unexercised route in the
instrument and read as coverage. **`auth-regression.py` still has 0 occurrences of
"frequency"**, and that remains true and now recorded.

---

## T3 · The coverage fraction

The crawler's API route set is **implicit** — whatever the crawled pages request —
so it cannot be read off the source directly. What **can** be measured is the
**upper bound**: every API path the frontend could ever request.

| | count |
|---|---|
| openapi paths (**denominator**) | **340** |
| distinct API path literals in frontend source | 213 (**199** normalised) |
| normalised literals that match an openapi path | **179** |
| **upper bound on crawler API coverage** | **179 / 340 = 52.6%** |
| openapi paths the frontend never references | **161** |

⛔ **179/340 is a ceiling, not the achieved figure.** The real number is lower —
it counts every path the frontend *could* call, including ones behind routes the
crawler never reaches and behind interactions it never performs. **The achieved
figure is unmeasurable without a run**, and the run is blocked by T1.

⭐ **161 openapi paths are unreachable from the frontend at all.** That is a
separate finding: nearly half the API surface has no frontend caller, so no
page-driven crawler can ever reach it, however well authenticated.

---

## What was written

`scripts/check-report-exposure.py` (new, CI-wired) and this report. **No tokens
minted. `AXIOM_SECRET` not fetched. No route added to the crawler.**
