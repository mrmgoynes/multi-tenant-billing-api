from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import models
from database import get_db
from tenant_context import get_tenant_schema
from schemas import InvoiceCreate, InvoiceResponse

router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"]
)

@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def generate_customer_invoice(inv_data: InvoiceCreate, db: Session = Depends(get_db)):
    """
    Automated Invoice Generation Engine:
    Validates the customer profile and dynamically calculates sequential 
    invoice tracking numbers isolated per tenant.
    """
    # 1. Verification Gate: Ensure the customer exists in the isolated workspace
    customer = db.query(models.Customer).filter(models.Customer.id == inv_data.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice generation failed: Customer ID '{inv_data.customer_id}' not found."
        )

    # 2. Automated Sequencing Engine: Calculate the next logical sequence count
    # Scoped entirely within the active schema context thanks to our search_path
    invoice_count = db.query(func.count(models.Invoice.id)).scalar() or 0
    next_sequence = invoice_count + 1

    # 3. String Compilation: Extract active tenant prefix to build standard billing numbers
    # e.g., tenant_stark -> STARK -> INV-STARK-0001
    active_schema = get_tenant_schema() # returns 'tenant_subdomain'
    tenant_prefix = active_schema.replace("tenant_", "").upper()
    generated_invoice_num = f"INV-{tenant_prefix}-{next_sequence:04d}"

    # 4. Success Path: Persist financial receivables document
    new_invoice = models.Invoice(
        customer_id=inv_data.customer_id,
        invoice_number=generated_invoice_num,
        amount=inv_data.amount,
        status="unpaid",
        due_date=inv_data.due_date
    )
    db.add(new_invoice)
    db.commit()
    db.refresh(new_invoice)
    return new_invoice
