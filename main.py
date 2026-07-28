from fastapi import FastAPI
from router import router as tenant_router
from customer_router import router as customer_router # Add this import
from middleware import TenantRoutingMiddleware

app = FastAPI(title="Multi-Tenant Billing REST API")

app.add_middleware(TenantRoutingMiddleware)

# Register all modular routing engines
app.include_router(tenant_router)
app.include_router(customer_router) # Add this registration

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Welcome to the Multi-Tenant Subscription Billing REST API"
    }
