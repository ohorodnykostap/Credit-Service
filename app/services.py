from datetime import date
import pandas as pd
import io
from app.crud import CreditCRUD, PlanCRUD
from app.schemas import UserCreditsResponseSchema, OpenCreditSchema, ClosedCreditSchema
from app.exceptions import (
    PlanValidationError,
    NoPlansFoundError,
    UserNotFoundError,
)


class UserCreditsService:
    """Service layer for handling user credit operations."""
    def __init__(self, crud: CreditCRUD):
        self.crud = crud

    async def get_user_credits_info(self, user_id: int) -> UserCreditsResponseSchema:
        """
        Retrieve credit information for a specific user.
        Builds a response schema with open or closed credits.
        Raises UserNotFoundError if the user does not exist.
        :param user_id: ID of the user
        :return: UserCreditsResponseSchema containing credit details
        """
        credits_db = await self.crud.get_user_credits(user_id)

        if not credits_db:
            raise UserNotFoundError(user_id)

        result_list = []

        for credit in credits_db:
            is_closed = credit.actual_return_date is not None

            body_payments = sum(p.sum for p in credit.payments if p.type_id == 1)
            percent_payments = sum(p.sum for p in credit.payments if p.type_id == 2)
            total_payments = sum(p.sum for p in credit.payments)

            if is_closed:
                credit_data = ClosedCreditSchema(
                    issuance_date=credit.issuance_date,
                    is_closed=True,
                    body=float(credit.body),
                    percent=float(credit.percent),
                    actual_return_date=credit.actual_return_date,
                    total_payments=float(total_payments)
                )
            else:
                overdue_days = 0
                if date.today() > credit.return_date:
                    overdue_days = (date.today() - credit.return_date).days

                credit_data = OpenCreditSchema(
                    issuance_date=credit.issuance_date,
                    is_closed=False,
                    body=float(credit.body),
                    percent=float(credit.percent),
                    return_date=credit.return_date,
                    overdue_days=overdue_days,
                    body_payments=float(body_payments),
                    percent_payments=float(percent_payments)
                )

            result_list.append(credit_data)

        return UserCreditsResponseSchema(user_id=user_id, credits=result_list)


class PlanService:
    """Service layer for handling credit plan operations."""
    def __init__(self, crud: PlanCRUD):
        self.crud = crud

    async def process_excel_plans(self, file_contents: bytes):
        """
        Process an Excel file containing credit plans.
        Validates data, checks for duplicates, and inserts plans into the database.
        Raises PlanValidationError for invalid data.
        :param file_contents: Raw bytes of the Excel file
        :return: Number of inserted plans
        """
        try:
            df = pd.read_excel(io.BytesIO(file_contents))
        except Exception:
            raise PlanValidationError("The Excel file could not be read.")

        df.columns = [c.lower() for c in df.columns]
        required_columns = {"period", "category", "sum"}

        if not required_columns.issubset(set(df.columns)):
            raise PlanValidationError(f"Missing required columns. Expected: {required_columns}")

        plans_to_insert = []

        for index, row in df.iterrows():
            if pd.isna(row["sum"]):
                raise PlanValidationError(f"Line {index + 2}: The amount cannot be empty.")

            try:
                current_sum = float(row["sum"])
            except (ValueError, TypeError):
                raise PlanValidationError(f"Line {index + 2}: The sum must be a number (found: '{row['sum']}')")

            if current_sum < 0:
                raise PlanValidationError(f"Line {index + 2}: The sum cannot be negative.")

            plan_date_raw = pd.to_datetime(row["period"], errors='coerce')
            if pd.isna(plan_date_raw):
                raise PlanValidationError(f"Line {index + 2}: Invalid date format in 'period'.")

            plan_date = plan_date_raw.date()
            if plan_date.day != 1:
                raise PlanValidationError(f"Line {index + 2}: Date {plan_date} must be the first day of the month.")

            category_name = str(row["category"]).strip()
            category_id = await self.crud.get_category_id_by_name(category_name)
            if not category_id:
                raise PlanValidationError(f"Line {index + 2}: Category '{category_name}' is not found in the dictionary.")

            existing = await self.crud.get_plan_by_period_and_category(plan_date, category_id)
            if existing:
                raise PlanValidationError(
                    f"Line {index + 2}: A plan for {plan_date} and category '{category_name}' already exists in the database."
                )

            plans_to_insert.append({
                "period": plan_date,
                "category_id": category_id,
                "sum": float(row["sum"])
            })

        try:
            return await self.crud.create_plans_batch(plans_to_insert)
        except NoPlansFoundError:
            raise NoPlansFoundError("There are no plans to insert.")

    async def get_plans_performance(self, check_date: date):
        """
        Retrieve performance data for plans in a given month.
        Compares planned vs actual values for issuance and payments.
        :param check_date: Date within the month to check
        :return: List of performance reports
        """
        start_of_month = check_date.replace(day=1)
        plans = await self.crud.get_plans_with_categories_for_month(start_of_month)

        if not plans:
            return []

        report = []
        for plan_obj, category_name in plans:
            actual_sum = 0.0
            if category_name == "видача":
                actual_sum = await self.crud.get_actual_issuances(start_of_month, check_date)
            elif category_name == "збір":
                actual_sum = await self.crud.get_actual_payments(start_of_month, check_date)

            plan_sum_float = float(plan_obj.sum)
            actual_sum_float = float(actual_sum)

            performance = 0.0
            if plan_sum_float > 0:
                performance = (actual_sum_float / plan_sum_float) * 100

            report.append({
                "month": start_of_month,
                "category": category_name,
                "plan_sum": plan_sum_float,
                "actual_sum": actual_sum_float,
                "performance_percentage": round(performance, 2)
            })

        return report

    async def get_year_performance(self, year: int):
        """
        Retrieve yearly performance data for issuance and payments.
        Aggregates monthly statistics and calculates shares and performance percentages.
        :param year: Year to analyze
        :return: Dictionary containing year and monthly performance data
        """
        res_iss_year, res_pay_year = await self.crud.get_year_actual_totals(year)
        total_iss_year = float(res_iss_year or 0)
        total_pay_year = float(res_pay_year or 0)

        monthly_issuances, monthly_payments = await self.crud.get_monthly_stats(year)

        iss_map = {int(m): {"count": c, "sum": float(s or 0)} for m, c, s in monthly_issuances}
        pay_map = {int(m): {"count": c, "sum": float(s or 0)} for m, c, s in monthly_payments}

        plans = await self.crud.get_year_plans(year)
        plan_map = {}
        for p_obj, cat_name in plans:
            m = p_obj.period.month
            if m not in plan_map:
                plan_map[m] = {}
            plan_map[m][cat_name] = float(p_obj.sum or 0)

        result_data = []
        for month in range(1, 13):
            month_date = date(year, month, 1)

            i_plan = plan_map.get(month, {}).get("видача", 0.0)
            i_fact = float(iss_map.get(month, {}).get("sum", 0.0))
            i_perf = (i_fact / i_plan * 100) if i_plan > 0 else 0.0
            i_share = (i_fact / total_iss_year * 100) if total_iss_year > 0 else 0.0

            p_plan = plan_map.get(month, {}).get("збір", 0.0)
            p_fact = float(pay_map.get(month, {}).get("sum", 0.0))
            p_perf = (p_fact / p_plan * 100) if p_plan > 0 else 0.0
            p_share = (p_fact / total_pay_year * 100) if total_pay_year > 0 else 0.0

            result_data.append({
                "month_year": month_date.strftime("%m.%Y"),
                "issuance_count": iss_map.get(month, {}).get("count", 0),
                "issuance_plan": i_plan,
                "issuance_actual": i_fact,
                "issuance_performance": round(i_perf, 2),
                "payments_count": pay_map.get(month, {}).get("count", 0),
                "payments_plan": p_plan,
                "payments_actual": p_fact,
                "payments_performance": round(p_perf, 2),
                "issuance_year_share": round(i_share, 2),
                "payments_year_share": round(p_share, 2)
            })

        return {"year": year, "data": result_data}
