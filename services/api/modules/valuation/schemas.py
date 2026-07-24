from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ValuationRequest(BaseModel):
    dataset_id: int
    mode: str = "proforma"           # proforma | auto_forecast
    assumptions: dict = {}           # terminal_growth, wacc_override, forecast{...}
    monte_carlo: dict = {}           # n_paths, seed, sigma_growth, sigma_margin, risk_aversion
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
