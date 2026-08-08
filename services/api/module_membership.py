"""Module membership for every served path. DECLARED, never inferred.

⛔⭐⭐ WHY A DECLARATION. Nothing in this codebase recorded which module a path
belongs to. The frontend's nav index carried a `section` field that looked like
the answer and was wrong for 3 of the 11 destinations that had one — a marketing
explainer attributed to the project-delivery module by a generator that carried
the last heading past the end of the array declaring it. Membership that a reader
cannot see being made is membership nobody checks.

⛔ "none" IS A DECLARATION. Auth, billing, platform metadata and the admin plane
belong to no module. Saying so is a decision; leaving them out is not.

⛔ AND "UNDECLARED" IS NOT "SAFE". 227 of 343 served paths have no module yet.
An unclassified path is UNRULED — `module_of` RAISES on one rather than
returning "none", because a toggle that silently let an unruled path through
would be indistinguishable from one that had been reviewed and cleared. Same
reasoning as `attribute()` raising on an internal orientation rather than
returning None: a falsy answer reads as "no module", when the truth is "nobody
has decided".

⭐ THE UNDECLARED COUNT IS A RATCHET, NOT A PERMANENT RED. The structural check
is green today — every served path appears in exactly one bucket — so the gate
proves something now and fails the moment a path is added to neither
(§III.25: a gate that is always red is off). What it forbids is GROWTH: the
undeclared count may fall and may never rise.

Guarded by: scripts/check-module-membership.py
"""
from __future__ import annotations


class PathNotDeclared(Exception):
    """Raised for a served path with no module declaration.

    ⛔ Deliberately an exception. Returning "none" would let a caller believe the
    path had been ruled out of every module, which is the opposite of the truth.
    """


TOGGLEABLE = ("internal_feedback", "external_feedback", "strategize", "execute")
MANDATORY = ("analyze",)

# ⛔ EXECUTE DEPENDS ON STRATEGIZE AND THE COMBINATION IS PERMITTED. The ten
# paths they share are the OKR spine — objectives, key results, KPIs,
# initiatives. STRATEGIZE writes it; EXECUTE reads it. Running EXECUTE without
# STRATEGIZE yields a PMO with no objectives above it, which is the
# strategy-execution gap as a configuration and is allowed, with a warning.
DEPENDS_ON = {"execute": "strategize"}


# ── ANALYZE — mandatory, never toggled ──────────────────────────────────
PATHS_ANALYZE: tuple[str, ...] = (
    "/api/v1/benchmarks/compare",
    "/api/v1/financials/datasets/{dataset_id}/eva-distribution",
    "/api/v1/financials/datasets/{dataset_id}/plan-vs-methods",
    "/api/v1/intelligence/cash-runway/{dataset_id}",
    "/api/v1/intelligence/covenants",
    "/api/v1/intelligence/readiness",
    "/api/v1/intelligence/readiness/apply",
    "/api/v1/intelligence/what-if",
    "/api/v1/intelligence/what-if/shocks",
    "/api/v1/metrics/dashboard/{dataset_id}",
    "/api/v1/metrics/dupont/{dataset_id}",
    "/api/v1/metrics/profitability/{dataset_id}",
    "/api/v1/metrics/ratios/{dataset_id}",
    "/api/v1/twin/lineage/{dataset_id}",
    "/api/v1/valuation/modes",
    "/api/v1/valuation/multiples",
    "/api/v1/valuation/real-option",
    "/api/v1/valuation/real-options/{dataset_id}",
    "/api/v1/valuation/run",
    "/api/v1/valuation/runs",
    "/api/v1/valuation/stress",
    "/companies/{company_id}/readiness",
    "/companies/{company_id}/urgent-items",
)

# ── STRATEGIZE — writes the OKR spine ───────────────────────────────────
PATHS_STRATEGIZE: tuple[str, ...] = (
    "/api/v1/financials/datasets/{dataset_id}",
    "/api/v1/intelligence/frontier/{dataset_id}",
    "/api/v1/intelligence/health/{dataset_id}",
    "/api/v1/intelligence/optimal-range/{dataset_id}",
    "/api/v1/intelligence/optimization/unified",
    "/api/v1/intelligence/optimize-analytics/{dataset_id}",
    "/api/v1/intelligence/optimize/{dataset_id}",
    "/api/v1/intelligence/recommendations/{dataset_id}",
    "/api/v1/intelligence/risk-analytics/{dataset_id}",
    "/api/v1/intelligence/target-state",
    "/api/v1/twin/compare/default",
    "/api/v1/twin/compare/{dataset_a}/{dataset_b}",
    "/api/v1/valuation/analytics/{dataset_id}",
    "/companies/{company_id}/initiatives",
    "/companies/{company_id}/key-results/{kr_id}",
    "/companies/{company_id}/kpi-variance",
    "/companies/{company_id}/kpis",
    "/companies/{company_id}/kpis/{kpi_id}",
    "/companies/{company_id}/objectives",
    "/companies/{company_id}/objectives/{obj_key}",
    "/companies/{company_id}/objectives/{obj_key}/initiatives",
    "/companies/{company_id}/objectives/{obj_key}/key-results",
    "/companies/{company_id}/people/detail",
)

# ── EXECUTE — reads the OKR spine ───────────────────────────────────────
PATHS_EXECUTE: tuple[str, ...] = (
    "/companies/{company_id}/initiative-impact",
    "/companies/{company_id}/initiative-impact/history",
    "/companies/{company_id}/initiatives/cockpit",
    "/companies/{company_id}/initiatives/reorder",
    "/companies/{company_id}/initiatives/{iid}",
    "/companies/{company_id}/initiatives/{iid}/actions",
    "/companies/{company_id}/initiatives/{iid}/blockers",
    "/companies/{company_id}/initiatives/{iid}/cadence-update",
    "/companies/{company_id}/initiatives/{iid}/csfs/{cid}/status",
    "/companies/{company_id}/initiatives/{iid}/detail",
    "/companies/{company_id}/initiatives/{iid}/history",
    "/companies/{company_id}/initiatives/{iid}/milestones",
    "/companies/{company_id}/initiatives/{iid}/objectives",
    "/companies/{company_id}/initiatives/{iid}/raci",
    "/companies/{company_id}/initiatives/{iid}/status",
    "/companies/{company_id}/issues/{issue_id}/initiative",
    "/companies/{company_id}/my-capabilities",
    "/companies/{company_id}/proposals",
    "/companies/{company_id}/proposals/{fingerprint}/reconsider",
)

# ── INTERNAL FEEDBACK — the employee voice ──────────────────────────────
PATHS_INTERNAL_FEEDBACK: tuple[str, ...] = (
    "/assessment/questionnaire",
    "/assessment/responses",
    "/assessment/submit",
    "/companies/{company_id}/assessment/current",
    "/companies/{company_id}/assessment/cycles",
    "/companies/{company_id}/assessment/cycles/{cid}/close",
    "/companies/{company_id}/assessment/cycles/{cid}/score",
    "/companies/{company_id}/assessment/framework",
    "/companies/{company_id}/assessment/invites",
    "/companies/{company_id}/assessment/seniority-gap",
    "/companies/{company_id}/assessment/summary",
    "/companies/{company_id}/assessment/swot",
    "/companies/{company_id}/axis-links",
    "/companies/{company_id}/initiatives/proposals",
    "/companies/{company_id}/invites",
    "/companies/{company_id}/issues",
    "/companies/{company_id}/posts/{pid}/flag-proposal",
    "/companies/{company_id}/readiness/derived",
    "/companies/{company_id}/threads",
    "/companies/{company_id}/threads/{tid}",
    "/companies/{company_id}/threads/{tid}/posts",
)

# ⛔ EXTERNAL FEEDBACK — DEFINED, ZERO COVERAGE. Voice of Customer, Supplier
# and Partner do not exist (§0.4 step 6). The toggle is declared now so that
# build lands inside it rather than being retrofitted around it. An empty list
# here is the correct state and the guard asserts it stays empty until the
# instruments exist.
PATHS_EXTERNAL_FEEDBACK: tuple[str, ...] = ()

# ── NONE — auth, billing, platform, admin. Declared, not omitted ────────
PATHS_NONE: tuple[str, ...] = (
    "/admin/accounts/{account_id}/pause",
    "/admin/accounts/{account_id}/resume",
    "/admin/audit",
    "/admin/customers",
    "/admin/pilots",
    "/admin/pilots/{company_id}/status",
    "/admin/transfer-offers",
    "/admin/transfer-offers/{offer_id}/revoke",
    "/admin/users/{user_id}/platform-role",
    "/api/v1/billing/checkout",
    "/api/v1/billing/config",
    "/api/v1/billing/status",
    "/api/v1/billing/webhook",
    "/api/v1/platform/about",
    "/api/v1/platform/pages",
    "/auth/change-email",
    "/auth/confirm-email",
    "/auth/forgot",
    "/auth/login",
    "/auth/oauth/{provider}/callback",
    "/auth/oauth/{provider}/start",
    "/auth/register",
    "/auth/resend-verification",
    "/auth/reset",
    "/auth/verify",
    "/health",
    "/internal/documents/backfill",
    "/internal/frontier/recompute",
    "/internal/sentinel/recompute",
    "/me",
)

# ⛔ UNDECLARED — unruled, not safe. `module_of` raises on these. The count is
# a ratchet: it may fall, never rise.
UNDECLARED: tuple[str, ...] = (
    "/access/accept-invite",
    "/access/activate",
    "/access/create-company",
    "/access/invite/info",
    "/access/invite/set-password",
    "/access/join",
    "/access/my-companies",
    "/access/redeem-invite-anonymous",
    "/access/resolve-cid/{cid}",
    "/access/showcase-companies",
    "/api/v1/auth/admin/grant",
    "/api/v1/auth/login",
    "/api/v1/auth/logout",
    "/api/v1/auth/me",
    "/api/v1/auth/register",
    "/api/v1/benchmarks/sectors",
    "/api/v1/education/modules",
    "/api/v1/education/modules/{slug}",
    "/api/v1/education/summary",
    "/api/v1/enterprises",
    "/api/v1/enterprises/{eid}",
    "/api/v1/enterprises/{eid}/state",
    "/api/v1/financials/datasets",
    "/api/v1/financials/datasets/upload",
    "/api/v1/financials/datasets/{dataset_id}/completeness",
    "/api/v1/financials/datasets/{dataset_id}/comprehensive-income",
    "/api/v1/financials/datasets/{dataset_id}/derived",
    "/api/v1/financials/datasets/{dataset_id}/forecast",
    "/api/v1/financials/datasets/{dataset_id}/frequency-view",
    "/api/v1/financials/datasets/{dataset_id}/pro-forma",
    "/api/v1/financials/datasets/{dataset_id}/profile",
    "/api/v1/financials/documents",
    "/api/v1/financials/oci/schema",
    "/api/v1/financials/templates",
    "/api/v1/financials/templates/{standard}",
    "/api/v1/intelligence/board-report/{dataset_id}",
    "/api/v1/intelligence/documents/{document_id}/analyze",
    "/api/v1/intelligence/documents/{document_id}/decisions",
    "/api/v1/intelligence/executive-brief/{dataset_id}",
    "/api/v1/intelligence/risk-dashboard/{dataset_id}",
    "/api/v1/intelligence/risk-profile/{dataset_id}",
    "/api/v1/intelligence/scenario",
    "/api/v1/intelligence/scenario-pro",
    "/api/v1/intelligence/scenario/levers",
    "/api/v1/intelligence/scenario/optimal",
    "/api/v1/learning/experiments",
    "/api/v1/learning/run",
    "/api/v1/learning/runs",
    "/api/v1/metrics/glossary",
    "/api/v1/metrics/ratio-independence/{dataset_id}",
    "/api/v1/packs/shared/{token}",
    "/api/v1/packs/{pack_id}/opens",
    "/api/v1/packs/{pack_id}/release",
    "/api/v1/packs/{pack_id}/releases",
    "/api/v1/reo/problems",
    "/api/v1/reo/runs",
    "/api/v1/reo/solve",
    "/api/v1/risk/analyses",
    "/api/v1/risk/run",
    "/api/v1/risk/runs",
    "/api/v1/simulation/run",
    "/api/v1/simulation/runs",
    "/api/v1/simulation/scenarios",
    "/api/v1/twin/actuals",
    "/api/v1/twin/reforecast",
    "/api/v1/twin/simulate",
    "/assessment/redeem-assess-invite",
    "/assets",
    "/assets/{name}",
    "/brochure/comparison-matrix",
    "/companies/{company_id}",
    "/companies/{company_id}/access",
    "/companies/{company_id}/admins",
    "/companies/{company_id}/admins/rank",
    "/companies/{company_id}/admins/step-down",
    "/companies/{company_id}/admins/{membership_id}/revoke",
    "/companies/{company_id}/assessment/axis/{l1_code}/comments",
    "/companies/{company_id}/assessment/cycles/{cid}",
    "/companies/{company_id}/assessment/cycles/{cid}/comments",
    "/companies/{company_id}/assessment/cycles/{cid}/invites",
    "/companies/{company_id}/assessment/cycles/{cid}/invites/seed",
    "/companies/{company_id}/assessment/invites/{invite_id}/link",
    "/companies/{company_id}/assessment/invites/{invite_id}/reinvite",
    "/companies/{company_id}/assessment/invites/{invite_id}/remind",
    "/companies/{company_id}/assessment/invites/{invite_id}/revoke",
    "/companies/{company_id}/assessment/items/{item_code}/drill",
    "/companies/{company_id}/assessment/seed-comments",
    "/companies/{company_id}/assessment/seed-history",
    "/companies/{company_id}/assessment/seed-okrs",
    "/companies/{company_id}/assessment/sentiment",
    "/companies/{company_id}/assessment/unseed-history",
    "/companies/{company_id}/assumptions",
    "/companies/{company_id}/assumptions/history",
    "/companies/{company_id}/authority",
    "/companies/{company_id}/causal-map",
    "/companies/{company_id}/changesets",
    "/companies/{company_id}/changesets/{cid}",
    "/companies/{company_id}/changesets/{cid}/commit",
    "/companies/{company_id}/changesets/{cid}/decide",
    "/companies/{company_id}/changesets/{cid}/discard",
    "/companies/{company_id}/changesets/{cid}/undo",
    "/companies/{company_id}/cid/rotate",
    "/companies/{company_id}/csf-proposals/{ppid}/approve",
    "/companies/{company_id}/csf-proposals/{ppid}/reject",
    "/companies/{company_id}/cycle-closure",
    "/companies/{company_id}/data-template",
    "/companies/{company_id}/data-upload",
    "/companies/{company_id}/data/changeset",
    "/companies/{company_id}/datasets",
    "/companies/{company_id}/datasets/{dataset_id}/forecast-horizon",
    "/companies/{company_id}/datasets/{dataset_id}/original",
    "/companies/{company_id}/datasets/{dataset_id}/restore",
    "/companies/{company_id}/departments",
    "/companies/{company_id}/departments/{department_id}/authority",
    "/companies/{company_id}/departments/{department_id}/authority/revoke",
    "/companies/{company_id}/departments/{department_id}/may-author",
    "/companies/{company_id}/departments/{department_id}/overrides",
    "/companies/{company_id}/departments/{department_id}/overrides/withdraw",
    "/companies/{company_id}/departments/{department_id}/signoff",
    "/companies/{company_id}/departments/{department_id}/signoff/diff",
    "/companies/{company_id}/departments/{department_id}/voice",
    "/companies/{company_id}/departments/{department_id}/voice/assign",
    "/companies/{company_id}/departments/{department_id}/voice/assignments",
    "/companies/{company_id}/departments/{dept_id}",
    "/companies/{company_id}/departments/{dept_id}/okr-map",
    "/companies/{company_id}/departments/{dept_id}/strategy-map",
    "/companies/{company_id}/documents",
    "/companies/{company_id}/documents/{doc_id}",
    "/companies/{company_id}/documents/{doc_id}/download-url",
    "/companies/{company_id}/documents/{doc_id}/extract",
    "/companies/{company_id}/documents/{doc_id}/proposals/seed",
    "/companies/{company_id}/execution-digest",
    "/companies/{company_id}/forecast/generate",
    "/companies/{company_id}/forecast/sets",
    "/companies/{company_id}/forecast/sets/{set_id}",
    "/companies/{company_id}/forecast/sets/{set_id}/primary",
    "/companies/{company_id}/frontier",
    "/companies/{company_id}/frontier/policy-surface",
    "/companies/{company_id}/frontier/search",
    "/companies/{company_id}/frontier/search/{job_id}",
    "/companies/{company_id}/goals",
    "/companies/{company_id}/goals/{goal_key}/initiatives",
    "/companies/{company_id}/initiatives/nudge-stale",
    "/companies/{company_id}/initiatives/proposals/{pid}/adopt",
    "/companies/{company_id}/initiatives/proposals/{pid}/dismiss",
    "/companies/{company_id}/initiatives/proposals/{pid}/park",
    "/companies/{company_id}/initiatives/stale",
    "/companies/{company_id}/initiatives/{iid}/assign-leader",
    "/companies/{company_id}/initiatives/{iid}/assignment",
    "/companies/{company_id}/initiatives/{iid}/cadence-updates",
    "/companies/{company_id}/initiatives/{iid}/csfs",
    "/companies/{company_id}/initiatives/{iid}/csfs/suggest",
    "/companies/{company_id}/initiatives/{iid}/csfs/{cid}/propose-text",
    "/companies/{company_id}/initiatives/{iid}/goals",
    "/companies/{company_id}/initiatives/{iid}/leader-status",
    "/companies/{company_id}/initiatives/{iid}/raci/{raci_id}/revoke",
    "/companies/{company_id}/initiatives/{iid}/rag",
    "/companies/{company_id}/initiatives/{iid}/rating",
    "/companies/{company_id}/initiatives/{iid}/reassign-leader",
    "/companies/{company_id}/initiatives/{iid}/revoke-leader",
    "/companies/{company_id}/invite",
    "/companies/{company_id}/issues/{issue_id}/comments",
    "/companies/{company_id}/issues/{issue_id}/status",
    "/companies/{company_id}/kpi-keys/status",
    "/companies/{company_id}/kpis/{kpi_id}/history",
    "/companies/{company_id}/kpis/{kpi_id}/links",
    "/companies/{company_id}/kpis/{kpi_id}/values",
    "/companies/{company_id}/logo",
    "/companies/{company_id}/members",
    "/companies/{company_id}/members/{membership_id}/approve",
    "/companies/{company_id}/members/{membership_id}/pause",
    "/companies/{company_id}/moves",
    "/companies/{company_id}/moves/entity",
    "/companies/{company_id}/moves/{move_id}",
    "/companies/{company_id}/multiverse",
    "/companies/{company_id}/overrides/audit",
    "/companies/{company_id}/participants",
    "/companies/{company_id}/participants/commit",
    "/companies/{company_id}/participants/invite",
    "/companies/{company_id}/participants/preview",
    "/companies/{company_id}/participants/template",
    "/companies/{company_id}/pilot-viewers",
    "/companies/{company_id}/pilot-viewers/{viewer_id}/revoke",
    "/companies/{company_id}/prescience-brief",
    "/companies/{company_id}/prescience/ask",
    "/companies/{company_id}/prescience/context",
    "/companies/{company_id}/prescience/conversations",
    "/companies/{company_id}/prescience/conversations/{conv_id}",
    "/companies/{company_id}/prescience/usage",
    "/companies/{company_id}/proposals/{fingerprint}/adopt",
    "/companies/{company_id}/proposals/{fingerprint}/dismiss",
    "/companies/{company_id}/radar/events",
    "/companies/{company_id}/recommendations",
    "/companies/{company_id}/recommendations/{fingerprint}/adopt",
    "/companies/{company_id}/recommendations/{fingerprint}/dismiss",
    "/companies/{company_id}/recommendations/{fingerprint}/park",
    "/companies/{company_id}/reports",
    "/companies/{company_id}/reports/latest",
    "/companies/{company_id}/reports/pdf",
    "/companies/{company_id}/reports/presentation",
    "/companies/{company_id}/reports/shares/{share_id}",
    "/companies/{company_id}/reports/{issue_id}/download-url",
    "/companies/{company_id}/reports/{issue_id}/share",
    "/companies/{company_id}/reports/{issue_id}/shares",
    "/companies/{company_id}/resilience-field",
    "/companies/{company_id}/roster",
    "/companies/{company_id}/roster/{membership_id}/resume",
    "/companies/{company_id}/roster/{membership_id}/revoke",
    "/companies/{company_id}/support/grant-admin",
    "/companies/{company_id}/synthesis",
    "/companies/{company_id}/threads/anchor",
    "/companies/{company_id}/threads/{tid}/archive",
    "/companies/{company_id}/transfer-admin",
    "/companies/{company_id}/twin/gap",
    "/companies/{company_id}/viability",
    "/initiatives/lead-accept",
    "/initiatives/lead-briefing",
    "/initiatives/rag-action",
    "/participants/sample-template",
    "/pilot-view/{token}",
    "/pilot-view/{token}/bridge",
    "/pilot-view/{token}/financials",
    "/pilot-view/{token}/pack",
    "/pilot-view/{token}/sentiment",
    "/report",
    "/reports/shared",
    "/webhooks/stripe",
)


DECLARED = {
    "analyze": PATHS_ANALYZE,
    "strategize": PATHS_STRATEGIZE,
    "execute": PATHS_EXECUTE,
    "internal_feedback": PATHS_INTERNAL_FEEDBACK,
    "external_feedback": PATHS_EXTERNAL_FEEDBACK,
    "none": PATHS_NONE,
}

#: The undeclared count at the moment this file was written. The guard fails if
#: the live count exceeds it, so the debt can be paid down and never grown.
UNDECLARED_RATCHET = 227


def module_of(path: str) -> str:
    """The declared module for a served path.

    ⛔ Raises `PathNotDeclared` for an undeclared path. See the module docstring:
    a falsy return would read as "belongs to no module", which is a ruling
    nobody made.
    """
    for mod, paths in DECLARED.items():
        if path in paths:
            return mod
    if path in UNDECLARED:
        raise PathNotDeclared(path)
    raise PathNotDeclared(f"{path} (not in the served inventory either)")
