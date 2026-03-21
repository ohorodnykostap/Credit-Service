from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select, insert, func
from datetime import date
from typing import List, Optional, Tuple

from app.models import Credit, User, Plan, Dictionary, Payment
from app.exceptions import UserNotFoundError, NoPlansFoundError


class CreditCRUD:
    """CRUD operations for the Credit entity."""

    def __init__(self, db: AsyncSession):
        """
        Initialize CreditCRUD with a database session.
        :param db: AsyncSession instance for database operations
        """
        self.db = db

    async def get_user_credits(self, user_id: int) -> List[Credit]:
        """
        Retrieve all credits for a given user by ID.
        Raises UserNotFoundError if the user does not exist.
        :param user_id: ID of the user
        :return: List of Credit objects
        """
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
    """CRUD operations for the Plan entity."""

    def __init__(self, db: AsyncSession):
        """
        Initialize PlanCRUD with a database session.
        :param db: AsyncSession instance for database operations
        """
        self.db = db

    async def get_plan_by_period_and_category(self, period: date, category_id: int) -> Optional[Plan]:
        """
        Retrieve a plan by period and category.
        :param period: Date representing the plan period
        :param category_id: Category ID (issuance or payments)
        :return: Plan object or None
        """
        query = select(Plan).where(
            Plan.period == period,
            Plan.category_id == category_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_category_id_by_name(self, name: str) -> Optional[int]:
        """
        Retrieve category ID by its name.
        :param name: Category name (case-insensitive)
        :return: Category ID or None
        """
        query = select(Dictionary.id).where(Dictionary.name == name.lower().strip())
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_plans_batch(self, plans_data: List[dict]) -> int:
        """
        Insert multiple plans into the database.
        Raises NoPlansFoundError if the list is empty.
        :param plans_data: List of plan dictionaries
        :return: Number of inserted plans
        """
        if not plans_data:
            raise NoPlansFoundError()

        query = insert(Plan).values(plans_data)
        await self.db.execute(query)
        await self.db.commit()

        return len(plans_data)

    async def get_actual_issuances(self, start_date: date, end_date: date) -> float:
        """
        Calculate total actual credit issuances between two dates.
        :param start_date: Start date
        :param end_date: End date
        :return: Sum of credit bodies
        """
        query = select(func.sum(Credit.body)).where(
            Credit.issuance_date >= start_date,
            Credit.issuance_date <= end_date
        )
        result = await self.db.execute(query)
        return result.scalar() or 0.0

    async def get_actual_payments(self, start_date: date, end_date: date) -> float:
        """
        Calculate total actual payments between two dates.
        :param start_date: Start date
        :param end_date: End date
        :return: Sum of payments
        """
        query = select(func.sum(Payment.sum)).where(
            Payment.payment_date >= start_date,
            Payment.payment_date <= end_date
        )
        result = await self.db.execute(query)
        return result.scalar() or 0.0

    async def get_plans_for_month(self, plan_month: date) -> List[Plan]:
        """
        Retrieve all plans for a specific month.
        :param plan_month: Date representing the month
        :return: List of Plan objects
        """
        query = select(Plan).where(Plan.period == plan_month)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_plans_with_categories_for_month(self, plan_month: date) -> List[Tuple[Plan, str]]:
        """
        Retrieve plans with category names for a specific month.
        :param plan_month: Date representing the month
        :return: List of tuples (Plan, category name)
        """
        query = (
            select(Plan, Dictionary.name)
            .join(Dictionary, Plan.category_id == Dictionary.id)
            .where(Plan.period == plan_month)
        )
        result = await self.db.execute(query)
        return result.all()

    async def get_year_actual_totals(self, year: int) -> Tuple[float, float]:
        """
        Calculate total issuances and payments for a given year.
        :param year: Year to calculate totals
        :return: Tuple (issuance_total, payments_total)
        """
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
        """
        Retrieve monthly statistics for issuances and payments in a given year.
        :param year: Year to calculate stats
        :return: Tuple (issuance_stats, payment_stats)
        """
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

    async def get_year_plans(self, year: int) -> List[Tuple[Plan, str]]:
        """
        Retrieve all plans with categories for a given year.
        :param year: Year to retrieve plans
        :return: List of tuples (Plan, category name)
        """
        query = (
            select(Plan, Dictionary.name)
            .join(Dictionary, Plan.category_id == Dictionary.id)
            .where(func.extract("year", Plan.period) == year)
        )
        result = await self.db.execute(query)
        return result.all()
