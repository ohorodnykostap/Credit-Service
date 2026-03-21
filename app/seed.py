import asyncio
from datetime import date
from decimal import Decimal

import pandas as pd
import numpy as np
from sqlalchemy import insert, select

from app.database import AsyncSessionLocal, engine, Base
from app.models import User, Credit, Payment, Dictionary, Plan


async def seed_data():
    print("Checking and creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created!")

    async with AsyncSessionLocal() as session:
        try:
            def read_df(path: str) -> pd.DataFrame:
                df = pd.read_csv(path, sep=None, engine="python")
                return df.replace({np.nan: None})

            dict_check = await session.execute(select(Dictionary).limit(1))
            if not dict_check.scalar():
                print("Seeding Dictionary...")
                dict_df = read_df("data/dictionary.csv")
                await session.execute(insert(Dictionary), dict_df.to_dict(orient="records"))
                await session.flush()
            else:
                print("Dictionary already seeded, skipping...")

            user_check = await session.execute(select(User).limit(1))
            if not user_check.scalar():
                print("Seeding Users...")
                users_df = read_df("data/users.csv")

                if "registration_date" in users_df.columns:
                    users_df["registration_date"] = pd.to_datetime(
                        users_df["registration_date"],
                        dayfirst=True,   # ❗ ВАЖЛИВО
                        errors="coerce"
                    ).dt.date

                await session.execute(insert(User), users_df.to_dict(orient="records"))
                await session.flush()
            else:
                print("Users already seeded, skipping...")

            credit_check = await session.execute(select(Credit).limit(1))
            if not credit_check.scalar():
                print("Seeding Credits...")
                credits_df = read_df("data/credits.csv")

                for col in ["issuance_date", "return_date", "actual_return_date"]:
                    if col in credits_df.columns:
                        dates = pd.to_datetime(
                            credits_df[col],
                            dayfirst=True,
                            errors="coerce"
                        )
                        credits_df[col] = np.where(dates.notnull(), dates.dt.date, None)

                for col in ["body", "percent"]:
                    if col in credits_df.columns:
                        credits_df[col] = credits_df[col].apply(
                            lambda x: Decimal(str(x)) if x is not None else Decimal("0")
                        )

                await session.execute(insert(Credit), credits_df.to_dict(orient="records"))
                await session.flush()
            else:
                print("Credits already seeded, skipping...")

            payment_check = await session.execute(select(Payment).limit(1))
            if not payment_check.scalar():
                print("Seeding Payments...")
                payments_df = read_df("data/payments.csv")

                if "payment_date" in payments_df.columns:
                    payments_df["payment_date"] = pd.to_datetime(
                        payments_df["payment_date"],
                        dayfirst=True,   # ❗ ВАЖЛИВО (14.01.2020)
                        errors="coerce"
                    ).dt.date

                if "sum" in payments_df.columns:
                    payments_df["sum"] = payments_df["sum"].apply(
                        lambda x: Decimal(str(x)) if x is not None else Decimal("0")
                    )

                await session.execute(insert(Payment), payments_df.to_dict(orient="records"))
                await session.flush()
            else:
                print("Payments already seeded, skipping...")

            plan_check = await session.execute(select(Plan).limit(1))
            if not plan_check.scalar():
                print("Seeding Plans...")
                plans_df = read_df("data/plans.csv")

                if "period" in plans_df.columns:
                    plans_df["period"] = pd.to_datetime(
                        plans_df["period"],
                        dayfirst=True,
                        errors="coerce"
                    ).dt.date

                if "sum" in plans_df.columns:
                    plans_df["sum"] = plans_df["sum"].apply(
                        lambda x: Decimal(str(x)) if x is not None else Decimal("0")
                    )

                if "id" in plans_df.columns:
                    plans_df = plans_df.drop(columns=["id"])

                await session.execute(insert(Plan), plans_df.to_dict(orient="records"))
                await session.flush()
            else:
                print("Plans already seeded, skipping...")

            await session.commit()
            print("Database successfully seeded with test data!")

        except Exception as e:
            await session.rollback()
            print(f"Error during seeding: {e}")
            raise e


if __name__ == "__main__":
    asyncio.run(seed_data())