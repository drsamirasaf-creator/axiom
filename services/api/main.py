"""AXIOM API — modular monolith entrypoint (SPEC-008 §19.2/§19.3). REQ-CORE-003."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from .core.db import init_db

# Root logging config so app INFO (custom loggers like axiom.prescience.nightly)
# reaches stdout. Without a configured root, non-uvicorn INFO records fall through
# to Python's last-resort handler (WARNING+ only) and vanish. Chatty third-party
# loggers are pinned to WARNING so INFO doesn't open a firehose.
import logging as _logging
_logging.basicConfig(level=_logging.INFO)
for _noisy in ("botocore", "boto3", "s3transfer", "urllib3", "httpx", "httpcore",
               "sqlalchemy.engine", "asyncio"):
    _logging.getLogger(_noisy).setLevel(_logging.WARNING)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
from .modules.enterprise_state.router import router as enterprise_router
from .modules.optimization.router import router as reo_router
from .modules.simulation.router import router as simulation_router
from .modules.risk.router import router as risk_router
from .modules.learning.router import router as learning_router
from .modules.education.router import router as education_router
from .modules.financials.router import router as financials_router
from .modules.financials.router import metrics_router
from .modules.valuation.router import router as valuation_router
from .modules.benchmarks.router import router as benchmarks_router
from .modules.identity.router import router as auth_router
from .modules.twin.router import router as twin_router
from .modules.platform.router import router as platform_router
from .modules.intelligence.router import router as intelligence_router
from .accounts import include_accounts

# ⭐ ERROR MONITORING, ERRORS ONLY. On 29 Jul a missing migration made every read
# of ax_initiatives raise UndefinedColumn — six anonymous demo surfaces returned
# 500 for about thirty minutes, on the front door, and it was found by a human
# looking rather than by anything telling us. Sentry would have fired on the first
# request.
#
# traces_sample_rate=0 deliberately: this is not APM and should cost nothing per
# request. `environment` separates the showcase demo from real tenants so a
# seeded-data error cannot be mistaken for a customer one. Unset DSN = disabled,
# and the app must boot identically without it — a monitoring dependency that can
# take the service down is worse than no monitoring.
def _init_sentry():
    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        return False
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
        sentry_sdk.init(
            dsn=dsn,
            environment=os.environ.get("AXIOM_ENV", "production"),
            release=os.environ.get("RAILWAY_GIT_COMMIT_SHA") or None,
            traces_sample_rate=0.0,
            send_default_pii=False,
            integrations=[StarletteIntegration(), FastApiIntegration()],
        )
        return True
    except Exception:
        # Never let monitoring break boot.
        return False


_SENTRY_ON = _init_sentry()

app = FastAPI(
    title="AXIOM",
    version="0.1.0",
    lifespan=lifespan,
    description=("The computational platform of the Dynamic Corporate Transformation "
                 "ecosystem. Phase 7 adds the Intelligence Layer: AI document "
                 "analysis behind deterministic explainability gates (verbatim "
                 "source quotes, whitelisted fields, published bounds, user "
                 "approval per Product §6.15), the REO-distance Enterprise "
                 "Health Index, the transformation path recommender priced "
                 "through the certified valuation engine, and the DRO stress "
                 "panel (TV-ambiguity worst-case EV + breakeven radius). Built "
                 "on the Phase 6 Financial Core. The AI proposes; deterministic "
                 "gates and certified engines dispose (ADR-006). Mathematics "
                 "lives here, never in the frontend (SPEC-008 §7.1)."))

# ADR-007: origins from AXIOM_ALLOWED_ORIGINS (default "*" until set).
from .core.config import allowed_origins
# allow_headers must list Authorization explicitly: per the Fetch spec a
# "*" wildcard does NOT authorize the Authorization header, so browser
# requests to authenticated endpoints (e.g. GET /me) fail their preflight.
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins(),
                   allow_methods=["*"],
                   allow_headers=["Authorization", "Content-Type", "X-AXIOM-Tenant"])


# Unhandled 500s are produced by Starlette's ServerErrorMiddleware OUTSIDE the
# CORS middleware, so they ship without an Access-Control-Allow-Origin header and
# the browser surfaces them as an opaque "Failed to fetch" (CORS error) instead of
# a readable 500. Re-attach CORS headers here (echoing the request Origin only when
# it is in the allowed list — never a blanket "*" when the list is locked down) so
# every future server error presents honestly. Handled 4xx already carry CORS via
# the middleware; this covers the 5xx path only.
import logging
from starlette.responses import JSONResponse


@app.exception_handler(Exception)
async def _cors_safe_500(request, exc):
    logging.exception("unhandled error on %s %s", request.method, request.url.path)
    resp = JSONResponse({"detail": "Internal Server Error"}, status_code=500)
    origin = request.headers.get("origin")
    allowed = allowed_origins()
    if origin and (origin in allowed or "*" in allowed):
        resp.headers["Access-Control-Allow-Origin"] = "*" if "*" in allowed else origin
        resp.headers["Vary"] = "Origin"
    return resp

import time as _time

from sqlalchemy import text as _sa_text

_PROBE_ENGINE = None


def _probe_engine():
    """⭐ A DEDICATED NullPool ENGINE FOR THE HEALTH PROBE.

    Built once, lazily. NullPool opens and closes one connection per probe, so
    the check CANNOT borrow from — or exhaust — the application's pool. The
    connect timeout is short because a probe that hangs is a probe that reports
    nothing while the platform waits.
    """
    global _PROBE_ENGINE
    if _PROBE_ENGINE is None:
        from sqlalchemy import create_engine as _ce
        from sqlalchemy.pool import NullPool as _NullPool

        from .core.config import database_url as _dburl
        url = _dburl()
        kw = {"poolclass": _NullPool}
        if url.startswith("postgresql"):
            kw["connect_args"] = {"connect_timeout": 3}
        _PROBE_ENGINE = _ce(url, **kw)
    return _PROBE_ENGINE


@app.get("/health", tags=["platform"])
def health():
    # ⭐ MONITORING STATE IS OBSERVABLE, NOT ASSERTED. Sentry was recorded as
    # "shipped" in a previous session while it was inert — the code was deployed
    # and SENTRY_DSN was unset, so _init_sentry() returned False and nothing was
    # ever captured. "Deployed" and "running" are different claims and only one of
    # them was true. The environment tag is echoed too, so a demo error can never
    # be mistaken for a production one by whoever reads the dashboard.
    # ⭐ THE RELEASE IS ECHOED BECAUSE PUSHED IS NOT PUBLISHED. A crawl run on
    # 2026-07-29 recorded plan-vs-methods 500s on two datasets and was written up
    # as a live defect; the endpoint was already fixed and the crawl had simply
    # started before Railway finished deploying the fix. 20/20 clean minutes
    # later. A verification tool that cannot name the build it tested produces
    # findings nobody can attribute — the red belonged to a commit that no longer
    # existed. Sentry already tags this same value as `release`, so an event and
    # a crawl can now be tied to one build.
    #
    # None means the platform did not inject the SHA. It is reported as null
    # rather than "unknown" or "": a caller must be able to tell "this build has
    # no identity" from "this build is at commit ''", and asserters MUST refuse
    # on null rather than treat it as a match.
    #
    # ⭐⭐ G4 — IT NOW VERIFIES THE APP IS USABLE, NOT MERELY ALIVE. Until 31 Jul
    # this returned a STATIC DICT: it could not fail, so it returned 200 with the
    # database unreachable. ⭐ THAT IS WORSE THAN NO HEALTHCHECK — it converts an
    # outage into a SILENT one, and it is what a platform probe would have
    # believed.
    body = {"service": "axiom-api", "phase": 18,
            "monitoring": bool(_SENTRY_ON),
            "environment": os.environ.get("AXIOM_ENV", "production"),
            "release": os.environ.get("RAILWAY_GIT_COMMIT_SHA") or None}
    checks, t0 = {}, _time.monotonic()

    # ── the database round-trip ───────────────────────────────────────────
    # ⭐⭐ ON ITS OWN CONNECTION, NEVER THE APP POOL. The probe runs on a
    # schedule against a 15-connection pool shared with the nightly sweeps, and
    # A HEALTHCHECK THAT EXHAUSTS THE POOL IS THE OUTAGE. NullPool means this
    # can never hold a connection the application needed.
    try:
        with _probe_engine().connect() as c:
            c.execute(_sa_text("select 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"unreachable: {type(e).__name__}"

    # ── the pool itself, read from memory — no query, no connection ───────
    # ⭐ A PROBE ON ITS OWN CONNECTION CAN SUCCEED WHILE THE APP POOL IS
    # EXHAUSTED — the database is fine and every user request is timing out.
    # Reporting the pool is what stops that reading as healthy.
    try:
        from .core.db import engine as _app_engine
        pool = _app_engine.pool
        used, cap = pool.checkedout(), pool.size() + pool.overflow()
        checks["pool"] = {"in_use": used, "capacity": cap}
        if cap and used >= cap:
            checks["pool"]["state"] = "saturated"
    except Exception as e:
        checks["pool"] = f"unreadable: {type(e).__name__}"

    body["checks"] = checks
    body["duration_ms"] = round((_time.monotonic() - t0) * 1000, 1)

    unhealthy = (checks.get("database") != "ok"
                 or (isinstance(checks.get("pool"), dict)
                     and checks["pool"].get("state") == "saturated"))
    body["status"] = "unhealthy" if unhealthy else "ok"
    if unhealthy:
        # ⭐ 503, SO A PROBE AND A HUMAN AGREE. A 200 carrying
        # {"status":"unhealthy"} is read as UP by every monitor ever written.
        return _JSONResponse(status_code=503, content=body)
    return body


# ---- Brand assets (Phase 18.4, ADR-021) -------------------------------------
# The logo PNGs must be reachable BY URL so the Lovable frontend (a separate
# deploy that cannot see the backend filesystem) can embed them in the app and
# the generated PDF. Served with long cache and permissive CORS (already set).
import pathlib as _pathlib
from fastapi.responses import FileResponse as _FileResponse, JSONResponse as _JSONResponse
_ASSETS_DIR = _pathlib.Path(__file__).resolve().parent / "assets"
_BRAND_ASSETS = {
    "axiom_white.png": "image/png",   # white knockout — for dark/navy backgrounds
    "axiom_color.png": "image/png",   # full color — for light backgrounds
}


@app.get("/assets/{name}", tags=["platform"])
def brand_asset(name: str):
    """Serve a whitelisted brand asset (the AXIOM logos) by URL."""
    if name not in _BRAND_ASSETS:
        return _JSONResponse(status_code=404, content={"detail": "unknown asset"})
    path = _ASSETS_DIR / name
    if not path.is_file():
        return _JSONResponse(status_code=404, content={"detail": "asset missing on server"})
    return _FileResponse(path, media_type=_BRAND_ASSETS[name],
                         headers={"Cache-Control": "public, max-age=86400"})


@app.get("/assets", tags=["platform"])
def brand_assets_index():
    """List the available brand-asset URLs (for the frontend to discover)."""
    return {"assets": {name: f"/assets/{name}" for name in _BRAND_ASSETS
                       if (_ASSETS_DIR / name).is_file()},
            "usage": {"axiom_white.png": "white logo — use on navy/dark backgrounds",
                      "axiom_color.png": "color logo — use on white/light backgrounds"}}

app.include_router(enterprise_router)
app.include_router(reo_router)
app.include_router(simulation_router)
app.include_router(risk_router)
app.include_router(learning_router)
app.include_router(education_router)
app.include_router(financials_router)
from .modules.billing.router import router as billing_router
app.include_router(billing_router)
app.include_router(metrics_router)
app.include_router(valuation_router)
app.include_router(benchmarks_router)
app.include_router(auth_router)
app.include_router(twin_router)
app.include_router(platform_router)
app.include_router(intelligence_router)

include_accounts(app)

# §7s.1 Stage 3 — Cadence distribution. Bound AFTER include_accounts so it can
# take that module's own get_db and auth dependency rather than re-declaring
# them, which is how two auth paths are born.
from .accounts import get_db as _get_db, get_current_user as _current_user  # noqa: E402
from . import pack_dist as _pack_dist  # noqa: E402
_pack_dist.include(app, _get_db, _current_user)

# B16 — in-app editable assumptions. ⭐ ADMIN-ONLY per §4x: write is bound to
# `require_company_admin`, which demands Membership.role == "admin". A
# DepartmentAuthority grant is a separate table and confers nothing here, so a
# CXO gets 403 — the rule the whole override trail rests on.
from .accounts import require_company_admin as _require_admin  # noqa: E402
from . import assumptions_api as _assumptions  # noqa: E402
_assumptions.include(app, _get_db, _require_admin)

# B12 — client-declared initiative impact. Admin-gated like B16: a declared
# commitment is a company-level statement, not a departmental one.
from . import initiative_impact as _iimpact  # noqa: E402
_iimpact.include(app, _get_db, _require_admin)

# B10/B11 — the declared initiative -> statement-line link. Imported so the model
# registers; the bridge reads it through initiative_lines.attribute().
from . import initiative_lines as _ilines  # noqa: F401,E402
