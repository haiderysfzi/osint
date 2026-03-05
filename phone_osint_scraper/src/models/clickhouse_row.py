from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime
import pandas as pd
import json

class ClickHouseRow(BaseModel):
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    phone: str  # E.164 normalized
    owner_name: str  # MANDATORY
    owner_name_confidence: float
    cnic: Optional[str] = None
    passport: Optional[str] = None
    address: Optional[str] = None
    country: str
    companies: List[str] = []
    sources: List[str] = []
    raw_json: str  # JSON string
    pipeline_duration: int  # ms
    status: Literal["success", "partial", "failed"]

    @classmethod
    def to_pandas(cls, rows: List['ClickHouseRow']) -> pd.DataFrame:
        data = []
        for row in rows:
            d = row.model_dump()
            # ClickHouse columns for arrays should be list, which pandas handles fine.
            # But raw_json is already a string here.
            data.append(d)
        return pd.DataFrame(data)
