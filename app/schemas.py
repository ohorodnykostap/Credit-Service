from pydantic import BaseModel, ConfigDict, field_validator
from datetime import date
from typing import List, Union, Optional


class BaseSchema(BaseModel):
    """Base schema with configuration to allow ORM attribute mapping."""
    model_config = ConfigDict(from_attributes=True)


class CreditBaseSchema(BaseSchema):
    """Base credit schema containing common fields for both open and closed credits."""
    issuance_date: date
    is_closed: bool
    body: float
    percent: float


class ClosedCreditSchema(CreditBaseSchema):
    """Schema for closed credits with actual return date and total payments."""
    actual_return_date: date
    total_payments: Optional[float] = 0.0

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "issuance_date": "2025-01-01",
                "is_closed": True,
                "body": 10000.0,
                "percent": 5.0,
                "actual_return_date": "2025-06-01",
                "total_payments": 10500.0
            }
        }
    )


class OpenCreditSchema(CreditBaseSchema):
    """Schema for open credits with planned return date, overdue days, and partial payments."""
    return_date: date
    overdue_days: int
    body_payments: Optional[float] = 0.0
    percent_payments: Optional[float] = 0.0

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "issuance_date": "2025-02-01",
                "is_closed": False,
                "body": 15000.0,
                "percent": 6.0,
                "return_date": "2025-12-01",
                "overdue_days": 0,
                "body_payments": 2000.0,
                "percent_payments": 500.0
            }
        }
    )


class UserCreditsResponseSchema(BaseSchema):
    """Response schema containing user ID and list of credits (open or closed)."""
    user_id: int
    credits: List[Union[ClosedCreditSchema, OpenCreditSchema]]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 20,
                "credits": [
                    {
                        "issuance_date": "2025-01-01",
                        "is_closed": True,
                        "body": 10000.0,
                        "percent": 5.0,
                        "actual_return_date": "2025-06-01",
                        "total_payments": 10500.0
                    },
                    {
                        "issuance_date": "2025-02-01",
                        "is_closed": False,
                        "body": 15000.0,
                        "percent": 6.0,
                        "return_date": "2025-12-01",
                        "overdue_days": 0,
                        "body_payments": 2000.0,
                        "percent_payments": 500.0
                    }
                ]
            }
        }
    )


class PerformanceSchema(BaseSchema):
    """Schema representing monthly performance of planned vs actual credit issuance/collection."""
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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "month": "2026-01-01",
                "category": "issuance",
                "plan_sum": 150000.0,
                "actual_sum": 140000.0,
                "performance_percentage": 93.3
            }
        }
    )


class YearPerformanceSchema(BaseSchema):
    """Schema representing aggregated yearly performance metrics for issuance and payments."""
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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "month_year": "2026-01",
                "issuance_count": 120,
                "issuance_plan": 150000.0,
                "issuance_actual": 140000.0,
                "issuance_performance": 93.3,
                "payments_count": 80,
                "payments_plan": 80000.0,
                "payments_actual": 75000.0,
                "payments_performance": 93.8,
                "issuance_year_share": 25.0,
                "payments_year_share": 20.0
            }
        }
    )


class YearPerformanceResponseSchema(BaseSchema):
    """Response schema containing yearly aggregated performance data."""
    year: int
    data: List[YearPerformanceSchema]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "year": 2026,
                "data": [
                    {
                        "month_year": "2026-01",
                        "issuance_count": 120,
                        "issuance_plan": 150000.0,
                        "issuance_actual": 140000.0,
                        "issuance_performance": 93.3,
                        "payments_count": 80,
                        "payments_plan": 80000.0,
                        "payments_actual": 75000.0,
                        "payments_performance": 93.8,
                        "issuance_year_share": 25.0,
                        "payments_year_share": 20.0
                    }
                ]
            }
        }
    )
