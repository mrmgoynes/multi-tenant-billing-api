from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import models
from database import get_db
from schemas import PlanCreate, PlanResponse

router = APIRouter(
    prefix="/plans",
    tags=["Subscription Plans"]
)

@router.get("/", response_model=List[PlanResponse], status_code=status.HTTP_200_OK)
def list_subscription_plans(db: Session = Depends(get_db)):
    """
    Multi-Tenant Product Catalog Engine:
    Retrieves the available database subscription plans scoped 
    strictly inside the active tenant's isolated workspace.
    """
    plans = db.query(models.Plan).all()
    return plans

@router.post("/", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_custom_subscription_plan(plan_data: PlanCreate, db: Session = Depends(get_db)):
    """
    Enterprise Content Management:
    Allows tenants to programmatically inject custom proprietary pricing tiers 
    into their independent product table architecture.
    """
    new_plan = models.Plan(
        name=plan_data.name,
        price=plan_data.price,
        billing_cycle=plan_data.billing_cycle
    )
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return new_plan
