from pydantic import BaseModel, ConfigDict, field_validator
from datetime import date
from typing import List, Union, Optional


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CreditBaseSchema(BaseSchema):
    issuance_date: date
    is_closed: bool
    body: float
    percent: float


class ClosedCreditSchema(CreditBaseSchema):
    actual_return_date: date
    total_payments: Optional[float] = 0.0


class OpenCreditSchema(CreditBaseSchema):
    return_date: date
    overdue_days: int
    body_payments: Optional[float] = 0.0
    percent_payments: Optional[float] = 0.0


class UserCreditsResponseSchema(BaseSchema):
    user_id: int
    credits: List[Union[ClosedCreditSchema, OpenCreditSchema]]


class PerformanceSchema(BaseSchema):
    month: date
    category: str
    plan_sum: float
    actual_sum: float
    performance_percentage: float

    @field_validator("month")
    def validate_month(cls, v: date):
        if v.day != 1:
            raise ValueError("Month must be the first day of the month")
        return v


class YearPerformanceSchema(BaseSchema):
    month_year: str
    issuance_count: int
    issuance_plan: float
    issuance_actual: float
    issuance_performance: float
    payments_count: int
    payments_plan: float
    payments_actual: float
    payments_performance: float
    issuance_year_share: float
    payments_year_share: float


class YearPerformanceResponseSchema(BaseSchema):
    year: int
    data: List[YearPerformanceSchema]
