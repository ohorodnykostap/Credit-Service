from datetime import date
from decimal import Decimal

from sqlalchemy import ForeignKey, String, Numeric, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    registration_date: Mapped[date] = mapped_column(Date, default=date.today)

    credits: Mapped[list["Credit"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Credit(Base):
    __tablename__ = "credits"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    issuance_date: Mapped[date] = mapped_column(Date)
    return_date: Mapped[date] = mapped_column(Date)
    actual_return_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    body: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    percent: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    user: Mapped["User"] = relationship(back_populates="credits")

    payments: Mapped[list["Payment"]] = relationship(
        back_populates="credit",
        cascade="all, delete-orphan"
    )


class Dictionary(Base):
    __tablename__ = "dictionary"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    payments: Mapped[list["Payment"]] = relationship(back_populates="type")
    plans: Mapped[list["Plan"]] = relationship(back_populates="category")


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    period: Mapped[date] = mapped_column(Date)
    sum: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    category_id: Mapped[int] = mapped_column(ForeignKey("dictionary.id"))
    category: Mapped["Dictionary"] = relationship(back_populates="plans")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    sum: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    payment_date: Mapped[date] = mapped_column(Date)

    credit_id: Mapped[int] = mapped_column(ForeignKey("credits.id"))
    type_id: Mapped[int] = mapped_column(ForeignKey("dictionary.id"))

    credit: Mapped["Credit"] = relationship(back_populates="payments")
    type: Mapped["Dictionary"] = relationship(back_populates="payments")
