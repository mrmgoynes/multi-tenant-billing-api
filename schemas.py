from pydantic import BaseModel, Field, ConfigDict, EmailStr

class TenantCreate(BaseModel):
    company_name: str = Field(..., max_length=100)
    subdomain: str = Field(..., max_length=50)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "company_name": "Acme Corporations",
                "subdomain": "acme"
            }
        }
    )

class TenantResponse(BaseModel):
    id: int
    company_name: str
    subdomain: str
    tenant_schema: str
    status: str

    model_config = ConfigDict(from_attributes=True)

class CustomerCreate(BaseModel):
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    email: EmailStr = Field(..., max_length=100)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "Jon",
                "last_name": "Snow",
                "email": "jon.snow@wall.com"
            }
        }
    )

class CustomerResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str

    model_config = ConfigDict(from_attributes=True)