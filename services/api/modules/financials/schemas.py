from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DatasetIn(BaseModel):
    name: str
    data: dict                       # canonical dataset (see engines docstring)
    enterprise_id: int | None = None


class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    standard: str
    ownership: str
    source: str
    enterprise_id: int | None
    version: int | None = None
    is_active: bool | None = None
    validation: dict
    created_at: datetime


class DatasetDetailOut(DatasetOut):
    data: dict


class ForecastRequest(BaseModel):
    assumptions: dict = {}
    persist: bool = False
    name: str | None = None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    content_type: str
    size_bytes: int
    note: str
    dataset_id: int | None
    ai_analysis: dict | None
    created_at: datetime
