from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class EnterpriseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    sector: str = Field(default="", max_length=120)

class SnapshotCreate(BaseModel):
    payload: dict
    note: str = ""

class SnapshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    payload: dict
    note: str
    created_at: datetime

class EnterpriseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    sector: str
    created_at: datetime

class EnterpriseDetail(EnterpriseOut):
    snapshots: list[SnapshotOut] = []
