from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models
from database import get_db
from schemas import SubscriptionCreate, SubscriptionResponse

router = APIRouter(
    prefix="/subscriptions",
    tags=["Subscriptions"]
)

@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(sub_data: SubscriptionCreate, db: Session = Depends(get_db)):
    """
    Enterprise Billing Lifecycle Manager:
    Validates account existence and checks for active contracts before 
    binding a customer to a new recurring pricing subscription tier.
    """
    # 1. Verification Gate: Ensure the target customer actually exists in this tenant workspace
    customer = db.query(models.Customer).filter(models.Customer.id == sub_data.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer verification failed: ID '{sub_data.customer_id}' not found."
        )

    # 2. Verification Gate: Ensure the subscription pricing plan exists
    plan = db.query(models.Plan).filter(models.Plan.id == sub_data.plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan verification failed: ID '{sub_data.plan_id}' not found."
        )

    # 3. CRITICAL SAAS CONCURRENCY LOCK: Check for an existing active subscription
    active_sub = db.query(models.Subscription).filter(
        models.Subscription.customer_id == sub_data.customer_id,
        models.Subscription.status == "active"
    ).first()
    
    if active_sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Aborted: Customer '{sub_data.customer_id}' already possesses an active subscription profile."
        )

    # 4. Success Path: Provision the new contract layer
    new_sub = models.Subscription(
        customer_id=sub_data.customer_id,
        plan_id=sub_data.plan_id,
        status="active"
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub
