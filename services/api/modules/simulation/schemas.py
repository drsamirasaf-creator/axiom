from datetime import datetime
from pydantic import BaseModel, ConfigDict

class RunRequest(BaseModel):
    scenario: str
    params: dict = {}
    enterprise_id: int | None = None

class SimRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    scenario: str
    params: dict
    result: dict
    enterprise_id: int | None
    created_at: datetime
