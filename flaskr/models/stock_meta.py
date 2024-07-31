from bson import ObjectId
from pydantic import BaseModel, Field, ValidationError, root_validator
from typing import Optional, Union
from datetime import datetime
from enum import Enum


class ModelConfig:
    arbitrary_types_allowed = True


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if v is None:
            return None
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema):
        schema.update(type="string")
        return schema


class StockMeta(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    stock_id: Optional[Union[ObjectId, str]] = Field(None)
    ticker: Optional[str] = None
    yearly: Optional[any] = None
    quarterly: Optional[any] = None
    date: Optional[datetime] = None

    class Config(ModelConfig):
        json_encoders = {ObjectId: str}
