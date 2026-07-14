from datetime import datetime
from pydantic import BaseModel, ConfigDict

class AnalysisRequest(BaseModel):
    analysis: str
    params: dict = {}
    enterprise_id: int | None = None

class RiskRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    analysis: str
    params: dict
    result: dict
    enterprise_id: int | None
    created_at: datetime
