from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
import models
from database import get_db
# Import explicitly from your schemas file
from schemas import SubscriptionCreate, SubscriptionResponse, SubscriptionUpgradeRequest

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
    customer = db.query(models.Customer).filter(models.Customer.id == sub_data.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer verification failed: ID '{sub_data.customer_id}' not found."
        )

    plan = db.query(models.Plan).filter(models.Plan.id == sub_data.plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan verification failed: ID '{sub_data.plan_id}' not found."
        )

    active_sub = db.query(models.Subscription).filter(
        models.Subscription.customer_id == sub_data.customer_id,
        models.Subscription.status == "active"
    ).first()
    
    if active_sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Aborted: Customer '{sub_data.customer_id}' already possesses an active subscription profile."
        )

    new_sub = models.Subscription(
        customer_id=sub_data.customer_id,
        plan_id=sub_data.plan_id,
        status="active"
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub


@router.put("/{subscription_id}/upgrade", response_model=SubscriptionResponse, status_code=status.HTTP_200_OK)
def upgrade_subscription_tier(
    subscription_id: int, 
    request_data: SubscriptionUpgradeRequest = Body(...), 
    db: Session = Depends(get_db)
):
    """
    Advanced Proration Billing Engine:
    Calculates time elapsed inside a mid-month subscription billing cycle,
    computes credit adjustments, updates contract mappings, and issues localized invoices.
    """
    active_sub = db.query(models.Subscription).filter(
        models.Subscription.id == subscription_id,
        models.Subscription.status == "active"
    ).first()
    
    if not active_sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upgrade failed: Active subscription record ID '{subscription_id}' not found."
        )

    if active_sub.plan_id == request_data.new_plan_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aborted: Target upgrade tier matches the customer's current active subscription plan."
        )

    old_plan = db.query(models.Plan).filter(models.Plan.id == active_sub.plan_id).first()
    new_plan = db.query(models.Plan).filter(models.Plan.id == request_data.new_plan_id).first()
    
    if not new_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upgrade aborted: New target tier plan ID '{request_data.new_plan_id}' does not exist."
        )

    current_time = datetime.now(timezone.utc)
    cycle_start = active_sub.start_date.replace(tzinfo=timezone.utc)
    cycle_end = cycle_start + timedelta(days=30) 

    total_cycle_seconds = (cycle_end - cycle_start).total_seconds()
    elapsed_seconds = (current_time - cycle_start).total_seconds()
    
    if elapsed_seconds < 0: elapsed_seconds = 0
    if elapsed_seconds > total_cycle_seconds: elapsed_seconds = total_cycle_seconds

    usage_ratio = elapsed_seconds / total_cycle_seconds
    remaining_ratio = 1.0 - usage_ratio

    old_plan_credit = float(old_plan.price) * remaining_ratio
    new_plan_cost = float(new_plan.price) * remaining_ratio
    prorated_charge = round(new_plan_cost - old_plan_credit, 2)

    active_sub.status = "canceled"
    active_sub.end_date = current_time

    upgraded_sub = models.Subscription(
        customer_id=active_sub.customer_id,
        plan_id=request_data.new_plan_id,
        status="active",
        start_date=current_time
    )
    db.add(upgraded_sub)
    db.flush() 

    if prorated_charge > 0:
        invoice_count = db.query(func.count(models.Invoice.id)).scalar() or 0
        from tenant_context import get_tenant_schema
        tenant_prefix = get_tenant_schema().replace("tenant_", "").upper()
        generated_invoice_num = f"INV-{tenant_prefix}-{invoice_count + 1:04d}"

        prorated_invoice = models.Invoice(
            customer_id=active_sub.customer_id,
            invoice_number=generated_invoice_num,
            amount=prorated_charge,
            status="unpaid",
            due_date=current_time + timedelta(days=7) 
        )
        db.add(prorated_invoice)

    db.commit()
    db.refresh(upgraded_sub)
    return upgraded_sub
