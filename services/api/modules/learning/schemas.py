from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ExperimentRequest(BaseModel):
    experiment: str
    params: dict = {}
    enterprise_id: int | None = None

class LearningRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    experiment: str
    params: dict
    result: dict
    enterprise_id: int | None
    created_at: datetime
