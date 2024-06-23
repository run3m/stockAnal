from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ModelConfig:
    arbitrary_types_allowed = True


class WarrenFetchStatus(BaseModel):
    _id: ObjectId = None
    stock_id: ObjectId
    income_statement_fetched: bool = False
    balance_sheet_fetched: bool = False
    cashflow_statement_fetched: bool = False
    full_fetched: bool = False
    date: datetime = None

    class Config(ModelConfig):
        pass
