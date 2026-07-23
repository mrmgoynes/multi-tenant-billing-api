from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas

router = APIRouter(prefix="/tenants", tags=["Tenant Management"])

@router.post("/", response_model=schemas.TenantResponse, status_code=status.HTTP_201_CREATED)
def register_tenant(tenant_data: schemas.TenantCreate, db: Session = Depends(get_db)):
    """
    Onboarding Endpoint: Validates and registers a new corporate tenant entity.
    Verifies subdomain availability before recording any data.
    """
    # 1. Query the database to check if the requested subdomain already exists
    existing_tenant = db.query(models.Tenant).filter(models.Tenant.subdomain == tenant_data.subdomain.lower()).first()
    
    # 2. QA/Backend Logic: If it exists, immediately halt the request and alert the user
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The subdomain '{tenant_data.subdomain}' is already taken. Please choose another."
        )
    
    # 3. If unique, format and prep the tenant schema folder name
    safe_schema_name = f"tenant_{tenant_data.subdomain.lower().replace('-', '_')}"
    
    # 4. Construct the complete database record instance
    new_tenant = models.Tenant(
        company_name=tenant_data.company_name,
        subdomain=tenant_data.subdomain.lower(),
        tenant_schema=safe_schema_name,
        status="active"
    )
    
    # 5. Commit and save the data across Port 5432 into the engine
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant) # Pulls the automatically generated ID back into Python
    
    return new_tenant