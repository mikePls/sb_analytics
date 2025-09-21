from datetime import date
from typing import Annotated, List, Optional
from pydantic import BaseModel, Field

class DailyRequest(BaseModel):
    db_password: str = Field(..., min_length=1)
    date: date

class MonthlyRequest(BaseModel):
    db_password: str
    year: Annotated[int, Field(ge=1900, le=2100)]
    month: Annotated[int, Field(ge=1, le=12)]

class DailyKPI(BaseModel):
    day: date
    attendance: Optional[int]
    transactions: Optional[int]
    items_sold: Optional[int]
    total_gross_gbp: Optional[float]
    all_four: Optional[int]
    show_book: Optional[int]
    comments: Optional[str]

class DailyResponse(DailyKPI):
    pass

class MonthlyResponse(BaseModel):
    year: int
    month: int
    rows: List[DailyKPI]
