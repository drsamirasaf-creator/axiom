from datetime import datetime
from pydantic import BaseModel, ConfigDict

class SolveRequest(BaseModel):
    problem: str
    params: dict = {}
    enterprise_id: int | None = None

class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    problem: str
    params: dict
    result: dict
    enterprise_id: int | None
    created_at: datetime
