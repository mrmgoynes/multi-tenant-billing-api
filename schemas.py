from pydantic import BaseModel, Field

class TenantCreate(BaseModel):
    """
    Data validation schema for incoming tenant registration requests.
    """
    company_name: str = Field(..., max_length=100, description="The legal name of the client company")
    subdomain: str = Field(..., max_length=50, description="The unique web access prefix")

    class Config:
        json_schema_extra = {
            "example": {
                "company_name": "Acme Corporations",
                "subdomain": "acme"
            }
        }

class TenantResponse(BaseModel):
    """
    Data validation schema for outgoing API responses.
    """
    id: int
    company_name: str
    subdomain: str
    tenant_schema: str
    status: str

    class Config:
        from_attributes = True # Allows Pydantic to read raw SQLAlchemy database models