from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from tenant_management import create_tenant_infrastructure

router = APIRouter(prefix="/tenants", tags=["Tenant Management"])

@router.post("/", response_model=schemas.TenantResponse, status_code=status.HTTP_201_CREATED)
def register_tenant(tenant_data: schemas.TenantCreate, db: Session = Depends(get_db)):
    """
    Onboarding Endpoint: Validates the payload, ensures subdomain uniqueness, 
    records the master entity, and dynamically provisions an isolated database schema.
    """
    # 1. Query the database to check if the requested subdomain already exists
    existing_tenant = db.query(models.Tenant).filter(models.Tenant.subdomain == tenant_data.subdomain.lower()).first()
    
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The subdomain '{tenant_data.subdomain}' is already taken. Please choose another."
        )
    
    # 2. Format a safe, standard name for the new PostgreSQL schema folder
    safe_schema_name = f"tenant_{tenant_data.subdomain.lower().replace('-', '_')}"
    
    # 3. Construct and commit the master registration record in the public directory
    new_tenant = models.Tenant(
        company_name=tenant_data.company_name,
        subdomain=tenant_data.subdomain.lower(),
        tenant_schema=safe_schema_name,
        status="active"
    )
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)
    
    # 4. SYSTEM AUTOMATION: Dynamically spawn the tenant's isolated filing cabinet
    try:
        create_tenant_infrastructure(db, safe_schema_name)
    except RuntimeError as error:
        # If the infrastructure generation fails, drop the public record to maintain transactional consistency
        db.delete(new_tenant)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"System failed to provision secure database environment: {str(error)}"
        )
    
    return new_tenant