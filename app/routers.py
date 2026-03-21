from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.database import get_db
from app.crud import CreditCRUD, PlanCRUD
from app.services import UserCreditsService, PlanService
from app.schemas import (
    UserCreditsResponseSchema,
    PerformanceSchema,
    YearPerformanceResponseSchema
)
from app.exceptions import (
    UserNotFoundError,
    CreditNotFoundError,
    PlanValidationError,
    NoPlansFoundError,
    CreditDataInconsistencyError
)

router = APIRouter(prefix="/credits", tags=["Credits"])


# Dependency injection
async def get_credit_crud(db: AsyncSession = Depends(get_db)):
    return CreditCRUD(db)

async def get_credits_service(credit_crud: CreditCRUD = Depends(get_credit_crud)):
    return UserCreditsService(credit_crud)


@router.get("/user_credits/{user_id}", response_model=UserCreditsResponseSchema)
async def get_user_credits(
    user_id: int,
    service: UserCreditsService = Depends(get_credits_service)
):
    try:
        return await service.get_user_credits_info(user_id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CreditNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CreditDataInconsistencyError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/plans_insert")
async def insert_plans(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files are allowed.")

    crud = PlanCRUD(db)
    service = PlanService(crud)

    try:
        contents = await file.read()
        inserted_count = await service.process_excel_plans(contents)
        return {"status": "success", "message": f"Lines entered: {inserted_count}"}
    except PlanValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except NoPlansFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/plans_performance", response_model=List[PerformanceSchema])
async def get_plans_performance(
    check_date: date,
    db: AsyncSession = Depends(get_db)
):
    crud = PlanCRUD(db)
    service = PlanService(crud)
    return await service.get_plans_performance(check_date)


@router.get("/year_performance", response_model=YearPerformanceResponseSchema)
async def get_year_performance(
    year: int,
    db: AsyncSession = Depends(get_db)
):
    crud = PlanCRUD(db)
    service = PlanService(crud)
    return await service.get_year_performance(year)
