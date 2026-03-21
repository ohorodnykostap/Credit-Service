from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select, insert, func
from datetime import date
from app.models import Credit, User, Plan, Dictionary, Payment
from app.exceptions import UserNotFoundError, NoPlansFoundError


class CreditCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_credits(self, user_id: int):
        user_query = await self.db.execute(select(User).where(User.id == user_id))
        user = user_query.scalar_one_or_none()

        if not user:
            raise UserNotFoundError(user_id)

        query = (
            select(Credit)
            .where(Credit.user_id == user_id)
            .options(joinedload(Credit.payments))
        )
        result = await self.db.execute(query)
        return result.scalars().unique().all()


class PlanCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_plan_by_period_and_category(self, period: date, category_id: int):
        query = select(Plan).where(
            Plan.period == period,
            Plan.category_id == category_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_category_id_by_name(self, name: str):
        query = select(Dictionary.id).where(Dictionary.name == name.lower().strip())
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_plans_batch(self, plans_data: list[dict]):

        if not plans_data:
            raise NoPlansFoundError()

        query = insert(Plan).values(plans_data)
        await self.db.execute(query)
        await self.db.commit()

        return len(plans_data)

    async def get_actual_issuances(self, start_date: date, end_date: date):
        query = select(func.sum(Credit.body)).where(
            Credit.issuance_date >= start_date,
            Credit.issuance_date <= end_date
        )
        result = await self.db.execute(query)
        return result.scalar() or 0.0

    async def get_actual_payments(self, start_date: date, end_date: date):
        query = select(func.sum(Payment.sum)).where(
            Payment.payment_date >= start_date,
            Payment.payment_date <= end_date
        )
        result = await self.db.execute(query)
        return result.scalar() or 0.0

    async def get_plans_for_month(self, plan_month: date):
        query = select(Plan).where(Plan.period == plan_month)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_plans_with_categories_for_month(self, plan_month: date):
        query = (
            select(Plan, Dictionary.name)
            .join(Dictionary, Plan.category_id == Dictionary.id)
            .where(Plan.period == plan_month)
        )
        result = await self.db.execute(query)
        return result.all()

    async def get_year_actual_totals(self, year: int):
        issuance_query = select(func.sum(Credit.body)).where(
            func.extract("year", Credit.issuance_date) == year
        )
        payments_query = select(func.sum(Payment.sum)).where(
            func.extract("year", Payment.payment_date) == year
        )

        iss_res = await self.db.execute(issuance_query)
        pay_res = await self.db.execute(payments_query)

        return (iss_res.scalar() or 0.0, pay_res.scalar() or 0.0)

    async def get_monthly_stats(self, year: int):
        iss_query = (
            select(
                func.extract("month", Credit.issuance_date).label("month"),
                func.count(Credit.id).label("count"),
                func.sum(Credit.body).label("sum")
            )
            .where(func.extract("year", Credit.issuance_date) == year)
            .group_by("month")
        )

        pay_query = (
            select(
                func.extract("month", Payment.payment_date).label("month"),
                func.count(Payment.id).label("count"),
                func.sum(Payment.sum).label("sum")
            )
            .where(func.extract("year", Payment.payment_date) == year)
            .group_by("month")
        )

        iss_res = await self.db.execute(iss_query)
        pay_res = await self.db.execute(pay_query)

        return iss_res.all(), pay_res.all()

    async def get_year_plans(self, year: int):
        query = (
            select(Plan, Dictionary.name)
            .join(Dictionary, Plan.category_id == Dictionary.id)
            .where(func.extract("year", Plan.period) == year)
        )
        result = await self.db.execute(query)
        return result.all()
