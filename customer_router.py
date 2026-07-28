from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas

router = APIRouter(prefix="/customers", tags=["Customer Management"])

@router.post("/", response_model=schemas.CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(customer_data: schemas.CustomerCreate, db: Session = Depends(get_db)):
    """
    Tenant Resource Endpoint: Creates a customer record securely 
    within the isolated schema folder of the active tenant.
    """
    # Check if a customer with this email already exists within THIS tenant's schema folder
    existing_customer = db.query(models.Customer).filter(models.Customer.email == customer_data.email.lower()).first()
    
    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A customer with email '{customer_data.email}' already exists for this tenant."
        )
    
    new_customer = models.Customer(
        first_name=customer_data.first_name,
        last_name=customer_data.last_name,
        email=customer_data.email.lower()
    )
    
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer

@router.get("/", response_model=list[schemas.CustomerResponse])
def list_customers(db: Session = Depends(get_db)):
    """
    Tenant Resource Endpoint: Retrieves all customer records 
    exclusively housed within the active tenant's schema folder.
    """
    return db.query(models.Customer).all()