# The enterprise gap — measured. REPORT BEFORE BUILDING.

Nothing built.

## Why `enterprise_id = None` — neither contract nor oversight, but COUPLING

The company IS created by committed code. `_backfill_showcase_logos()`
(`core/seed.py:133`) creates the Enterprise row and re-links the dataset:

    ent = Enterprise(tenant=SHOWCASE_TENANT, name=name, ...)
    db.add(ent); db.flush()
    ...
    if ds.enterprise_id != ent.id:
        ds.enterprise_id = ent.id
    ds.is_active = True          # so /companies/{ent.id}/reports works

⭐ **But it returns before reaching any of that when R2 is unconfigured:**

    client, bucket = _r2_client()
    if client is None:
        return

**So company creation rides inside a logo backfill, behind an object-storage
guard.** The guard is correct for its stated purpose — do not attempt to upload a
wordmark with no bucket. It also, silently, prevents the company from existing.

That is the answer to the question as posed: not a deliberate contract that
datasets stand alone, and not a forgotten line. **A guard that correctly protects
one thing also disables another, because two unrelated concerns share a
function.** Same shape as the participant case in reverse — there the absence was
a contract; here it looks like a contract and is an accident of placement.

**Consequence:** on any rebuild without R2 credentials — which is every local
rebuild, every CI run, and any deployment where storage is configured after the
first boot — there is no company, and all 2,061 company-scoped rows have nothing
to attach to. The function name says "logos". Nothing says "and the company".

## What enterprise 20 actually contains

    tenant='showcase'  name='Meridian Industries, Inc.'  ownership=public
    statement_units=actual  logo_r2_key=logos/20/…png  logo_content_type=image/png

**2,061 rows across 34 tables** are scoped to it:

| relation | rows | | relation | rows |
|---|---:|---|---|---:|
| ax_trajectory_cache | 1565 | | ax_kpi_objective_links | 41 |
| ax_key_results | 82 | | ax_kpi_aliases | 49 |
| ax_kpi_plan | 65 | | ax_kr_aliases | 42 |
| ax_objectives | 41 | | ax_kpi_initiative_links | 41 |
| ax_initiatives | 15 | | ax_strategic_moves | 14 |
| ax_departments | **7** | | ax_department_aliases | 12 |
| ax_document_chunks | 12 | | ax_prescience_conversations | 10 |
| ax_assessment_cycles | **6** | | ax_assessment_invites | **7** |
| ax_threads | 7 | | ax_document_proposals | 6 |
| ax_recommendation_dispositions | 5 | | financial_datasets | 4 |
| ax_report_issues, ax_radar_snapshots, ax_dataset_prefs, ax_decision_frontiers, ax_dp_policy_surfaces, ax_viability | 3 each | | ax_documents, ax_document_text, ax_radar_events, ax_prescience_usage | 2 each |
| ax_assessment_config, ax_assessment_frameworks, ax_prescience_context, ax_readiness | 1 each | | | |

⭐ **`ax_trajectory_cache` is 76% of the total and is derived** — it regenerates.
Excluding it, the real content is **~496 rows**.

⭐ **And the OKR surface is larger than the assessment one.** 41 objectives, 82
key results, 65 KPI plans and 41+41 links — 270 rows — against the assessment's
~14 (cycles, framework, config, invites; the 14,430 responses are already
recovered in the gap-3 fixture). Gap 3 was scoped as "the demo's missing half";
measured, the assessment is the smaller half of what does not rebuild.

## What this changes about the plan

The gap-3 seed is written, committed and correct — it simply has nothing to
attach to. Closing the enterprise gap unblocks it, but the enterprise gap is not
one row: it is one row plus the decision of which of the other 33 relations are
part of "the demo" and which are incidental.

**A recommendation, not an action:** fix the coupling first and separately. Move
Enterprise creation out of `_backfill_showcase_logos()` into its own
`_ensure_showcase_enterprises()` that runs unconditionally, leaving the logo
upload behind the R2 guard where it belongs. That is a small, self-contained
change that makes the company exist on every rebuild — and it is verifiable on
its own, before anything larger is attempted.

Then the remaining question is scope, and it is yours: departments and OKRs are
demo surfaces; prescience conversations, radar events and trajectory cache are
usage residue. I would seed the first and let the second regenerate, but I have
been wrong twice about what is deliberate here, so I am not deciding it.

## Denominator

Still not restated. The company does not rebuild, so the honest figure is not
"4 of 13" — but naming a new number before the enterprise path is fixed would
repeat the failure that produced the ~195.
