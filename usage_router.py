from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
import models
from database import get_db
from schemas import UsageRecordCreate, UsageResponse

router = APIRouter(
    prefix="/usage",
    tags=["Usage Metering"]
)

@router.post("/", response_model=UsageResponse, status_code=status.HTTP_201_CREATED)
def record_customer_usage(usage_data: UsageRecordCreate, db: Session = Depends(get_db)):
    """
    High-Frequency Metering Endpoint:
    Ingests and records a safe consumption ledger row for an isolated tenant customer.
    """
    # 1. Verification Gate: Ensure the target customer exists in the isolated workspace
    customer = db.query(models.Customer).filter(models.Customer.id == usage_data.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usage logging failed: Customer ID '{usage_data.customer_id}' not found."
        )

    # 2. Success Path: Persist metric ingestion event row
    new_record = models.UsageRecord(
        customer_id=usage_data.customer_id,
        metric_name=usage_data.metric_name,
        quantity=usage_data.quantity
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record


@router.get("/summary/{customer_id}/{metric_name}", status_code=status.HTTP_200_OK)
def get_customer_usage_summary(customer_id: int, metric_name: str, db: Session = Depends(get_db)):
    """
    Reporting & Analytics Engine:
    Aggregates and calculates the complete sum quantity of a given metric 
    consumed by a customer profile within the active tenant schema.
    """
    # 1. Calculate aggregated sum cleanly via a native database summary query
    total_usage = db.query(func.sum(models.UsageRecord.quantity)).filter(
        models.UsageRecord.customer_id == customer_id,
        models.UsageRecord.metric_name == metric_name
    ).scalar() or 0

    return {
        "customer_id": customer_id,
        "metric_name": metric_name,
        "total_consumed": total_usage
    }
