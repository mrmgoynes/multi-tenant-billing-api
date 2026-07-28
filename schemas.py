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
        from_attributes = True


class CustomerCreate(BaseModel):
    """
    Data validation schema for incoming customer creation requests.
    """
    first_name: str = Field(..., max_length=50, description="The customer's given name")
    last_name: str = Field(..., max_length=50, description="The customer's family name")
    email: str = Field(..., max_length=100, description="The customer's unique email address")

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "Jon",
                "last_name": "Snow",
                "email": "jon.snow@wall.com"
            }
        }

class CustomerResponse(BaseModel):
    """
    Data validation schema for outgoing customer API responses.
    """
    id: int
    first_name: str
    last_name: str
    email: str

    class Config:
        from_attributes = True