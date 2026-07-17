"""Sandbox showcase seeding (Phase 11, ADR-010). REQ-SBX-001.

Anonymous visitors browse the reserved 'showcase' tenant: a fully
populated workspace built from the certified reference companies, with a
complete twin story (plan -> valuation -> 2026 actuals -> re-forecast) so
every commercial tab renders in full glory with zero friction. Seeding is
idempotent (skipped once showcase data exists), controllable via
AXIOM_SEED_SHOWCASE, and never blocks startup.
"""
import os

SHOWCASE_TENANT = "showcase"

MERIDIAN_ACTUALS_2026 = {
    "income_statement": {"revenue": 1450.0, "cogs": 855.5, "opex": 290.0,
                         "depreciation_amortization": 72.5,
                         "interest_expense": 24.0},
    "balance_sheet": {"cash": 160.0, "other_current_assets": 319.0,
                      "noncurrent_assets": 877.5,
                      "current_liabilities_ex_debt": 174.0,
                      "short_term_debt": 40.0, "long_term_debt": 400.0,
                      "preferred_equity": 0.0, "minority_interest": 0.0,
                      "total_equity": 742.5},
    "cash_flow": {"capex": 110.0, "net_borrowing": 0.0, "dividends": 0.0},
}

MEMO = (b"Meridian Industries - board strategy memo (showcase example).\n"
        b"We target revenue growth of 7% (0.07) per year over the plan "
        b"period, an EBIT margin of 17% (0.17), and long-run terminal "
        b"growth of 2.5% (0.025).\n")


def _backfill_showcase_oci(db):
    """One-time, idempotent: existing showcase datasets seeded before the OCI
    module have no `oci` block, so the Comprehensive Income statement renders
    all 'not on file'. Patch them in place with the canonical demo drivers so
    the sandbox is fully populated. Runs at startup; safe to run repeatedly."""
    from .refcompanies import meridian, halcyon
    from ..modules.financials import models as fin_models
    from sqlalchemy.orm.attributes import flag_modified
    mer_oci = meridian().get("oci")
    hal_oci = halcyon().get("oci")
    try:
        rows = db.query(fin_models.FinancialDataset)\
                 .filter_by(tenant=SHOWCASE_TENANT).all()
        changed = 0
        for row in rows:
            data = row.data or {}
            if data.get("oci"):
                continue                             # already has OCI
            name = (row.name or "").lower()
            if "halcyon" in name:
                data["oci"] = hal_oci
            else:
                data["oci"] = mer_oci                # Meridian + its children
            row.data = data
            flag_modified(row, "data")               # JSON column dirty flag
            changed += 1
        if changed:
            db.commit()
            import logging
            logging.getLogger("axiom.seed").info(
                "backfilled OCI onto %d showcase dataset(s)", changed)
    except Exception:
        db.rollback()
        import logging
        logging.getLogger("axiom.seed").exception("OCI backfill failed")


def seed_showcase():
    if os.environ.get("AXIOM_SEED_SHOWCASE", "true").strip().lower() in (
            "0", "false", "no", "off"):
        return
    from .db import SessionLocal
    from ..modules.financials import models as fin_models
    from ..modules.valuation import models as val_models
    from ..modules.valuation import engines as val
    from ..modules.twin import engines as twin
    from ..modules.financials import engines as fin
    from .refcompanies import meridian, halcyon, helios

    db = SessionLocal()
    try:
        if db.query(fin_models.FinancialDataset)\
             .filter_by(tenant=SHOWCASE_TENANT).first():
            _backfill_showcase_oci(db)              # keep existing rows current
            _backfill_showcase_shares(db)           # add shares to pre-shares showcase rows
            return                                  # already seeded

        def store(name, data, source, parent_id=None):
            row = fin_models.FinancialDataset(
                tenant=SHOWCASE_TENANT, name=name,
                standard=data["company"]["standard"],
                ownership=data["company"]["ownership"], source=source,
                data=data, validation={"warnings": []},
                parent_dataset_id=parent_id)
            db.add(row); db.flush()
            return row

        def store_run(ds, mode, result, params):
            db.add(val_models.ValuationRun(
                tenant=SHOWCASE_TENANT, dataset_id=ds.id, mode=mode,
                params=params, result=result))

        # -- Meridian: the full twin story arc ---------------------------
        m = meridian()
        m_row = store("Meridian Industries (showcase)", m, "direct")
        store_run(m_row, "proforma", val.run(m, "proforma"),
                  {"assumptions": {}, "monte_carlo": {}})
        child, _report = twin.sync(m, 2026, MERIDIAN_ACTUALS_2026)
        c_row = store("Meridian Industries (showcase) — 2026 actuals",
                      child, "actuals", m_row.id)
        store_run(c_row, "proforma", val.run(child, "proforma"),
                  {"assumptions": {}, "monte_carlo": {}})
        prop = twin.reforecast_proposal(child)
        store("Meridian Industries (showcase) — re-forecast",
              prop["proposed_dataset"], "forecast", c_row.id)

        # -- Halcyon: the private-company, historicals-only path ---------
        h = halcyon()
        h_row = store("Halcyon Components (showcase)", h, "direct")
        store_run(h_row, "auto_forecast", val.run(h, "auto_forecast"),
                  {"assumptions": {}, "monte_carlo": {}})
        fc = fin.auto_forecast(h, {})
        fc.pop("_forecast_provenance", None)
        store("Halcyon Components (showcase) — AXIOM trend forecast",
              fc, "forecast", h_row.id)

        # -- Helios: a deliberately stressed public company, so the Distress
        #    & Liquidity panel genuinely lights up (contrast to Meridian) --
        hel = helios()
        hel_row = store("Helios Freight Systems (showcase — stressed)",
                        hel, "direct")
        store_run(hel_row, "proforma", val.run(hel, "proforma"),
                  {"assumptions": {}, "monte_carlo": {}})

        # -- a showcase document (analysis honestly absent: needs a key
        #    and a signed-in user — that button IS the conversion point) --
        db.add(fin_models.EnterpriseDocument(
            tenant=SHOWCASE_TENANT, dataset_id=m_row.id,
            filename="board_strategy_memo.txt", content_type="text/plain",
            size_bytes=len(MEMO), note="showcase example document",
            data=MEMO, ai_analysis=None))
        db.commit()
    except Exception:
        db.rollback()
        import logging
        logging.getLogger("axiom.seed").exception("showcase seeding failed")
    finally:
        db.close()
