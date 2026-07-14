from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ValuationRequest(BaseModel):
    dataset_id: int
    mode: str = "proforma"           # proforma | auto_forecast
    assumptions: dict = {}           # terminal_growth, wacc_override, forecast{...}
    monte_carlo: dict = {}           # n_paths, seed, sigma_growth, sigma_margin, risk_aversion


class ValuationRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    dataset_id: int
    mode: str
    params: dict
    result: dict
    created_at: datetime
