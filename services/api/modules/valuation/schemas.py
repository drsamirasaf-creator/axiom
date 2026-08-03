from datetime import datetime
from pydantic import BaseModel, ConfigDict, model_validator


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE FREE DICT WAS THE MECHANISM, NOT THE TYPO (§7x)
# ═══════════════════════════════════════════════════════════════════════════
# `assumptions: dict` and `monte_carlo: dict` accepted ANY key, dropped the ones
# the engine does not read, and reported nothing. Four fields on the valuation
# page were dead in production for exactly that reason — `wacc` (engine reads
# `wacc_override`), `paths` (`n_paths`), `capex_pct` (`capex_pct_revenue`) and
# `nwc_pct` (`nwc_pct_revenue`) — and the customer's evidence was a button that
# did nothing.
#
# ⭐ A TYPO IS ONE DEFECT; A PAYLOAD THAT SILENTLY DISCARDS WHAT IT DOES NOT
# RECOGNISE IS A DEFECT GENERATOR. Every field added from here on would have the
# same failure available to it. `extra="forbid"` turns the next one into a 422
# on the first press — the §4u-c precedent, used there so a client could not post
# comment text, used here so a client cannot post a field nobody reads.
#
# ⭐ THE NAMES BELOW ARE THE ENGINE'S. They are not a new vocabulary: they are
# what `valuation.engines.run` and `financials.engines.auto_forecast` already
# read, and what every other caller (prescience_decision, sentinel,
# intelligence.assemble_assumptions) already sends.

class _Strict(BaseModel):
    """Forbids unknown keys, and refuses an explicit null.

    ⭐ ABSENCE AND NULL ARE DIFFERENT INPUTS. Every field here is optional
    because the engine supplies its own default when a key is absent — but a
    client that explicitly sends `"terminal_growth": null` has stated something,
    and silently treating that as "not supplied" is the same silence this model
    exists to end. It is refused at the boundary instead.
    """
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _no_explicit_nulls(self):
        nulls = [f for f in self.model_fields_set if getattr(self, f) is None]
        if nulls:
            raise ValueError(
                f"{', '.join(sorted(nulls))}: null is not a value. Omit the "
                f"field to use the engine's default.")
        return self

    def to_engine(self) -> dict:
        """The dict the engine reads. Unset fields are omitted so `.get(k, dflt)`
        still resolves to the engine's own default rather than to None."""
        return self.model_dump(exclude_unset=True)


class ForecastAssumptions(_Strict):
    """`assumptions.forecast` — read by financials.engines.auto_forecast, and
    ONLY in mode='auto_forecast'. Derived from that function's `a.get(...)`
    calls, not from a hand list."""
    horizon: int | None = None
    revenue_growth: float | None = None
    ebit_margin: float | None = None
    da_pct_revenue: float | None = None
    capex_pct_revenue: float | None = None
    nwc_pct_revenue: float | None = None
    interest_expense: float | None = None


class Assumptions(_Strict):
    """Read by valuation.engines.run."""
    terminal_growth: float | None = None
    wacc_override: float | None = None
    forecast: ForecastAssumptions | None = None

    def to_engine(self) -> dict:
        d = super().to_engine()
        if self.forecast is not None:
            d["forecast"] = self.forecast.to_engine()
        return d


class MonteCarlo(_Strict):
    """Read by valuation.engines.run's stochastic block."""
    n_paths: int | None = None
    seed: int | None = None
    sigma_growth: float | None = None
    sigma_margin: float | None = None
    risk_aversion: float | None = None


class ValuationRequest(BaseModel):
    dataset_id: int
    mode: str = "proforma"           # proforma | auto_forecast
    assumptions: Assumptions = Assumptions()
    monte_carlo: MonteCarlo = MonteCarlo()
    # TRANSIENT forecast override — when present, the dataset's historicals are kept
    # and its forecast is REPLACED by this forecast for THIS computation only
    # (nothing is written to the stored dataset). Used to value an EXTENDED client
    # plan (supplied years + an AXIOM-projected tail) as a distinct, clearly-labelled
    # basis without persisting a projection that could later be mistaken for the
    # supplied plan. Shape: {periods:{forecast:[years]}, income_statement, balance_sheet, cash_flow}.
    forecast_override: dict | None = None
    basis_label: str | None = None   # e.g. "my plan (extended to 10y by AXIOM Ensemble)"


class ValuationRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    dataset_id: int
    mode: str
    params: dict
    result: dict
    created_at: datetime
    transient: bool = False   # anonymous sandbox computations are not stored
    # §7v — what produced this run. None on the 421 runs that predate the column,
    # and a consumer must read that as "unrecorded", never as "no overrides".
    provenance: dict | None = None
