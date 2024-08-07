from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class ModelConfig: 
    arbitrary_types_allowed = True

class StatementType(str, Enum):
    INCOME_STATEMENT = "INCOME_STATEMENT"
    BALANCE_SHEET = "BALANCE_SHEET"
    CASHFLOW_STATEMENT = "CASHFLOW_STATEMENT"
    
class StatementTimeFrame(str, Enum):
    YEARLY = "yearly"
    QUARTERLY = "quarterly"

class Statement(BaseModel):
    _id: ObjectId = None
    stock_id: ObjectId
    ticker: str = None
    statement_type: StatementType
    year: int = None
    quarter: int = None
    time_frame: StatementTimeFrame = None
    data: any = None
    statement_date: datetime = None
    date: datetime = None

    class Config(ModelConfig):
        pass
