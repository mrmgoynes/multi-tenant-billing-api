from fastapi import FastAPI
from router import router as tenant_router
from middleware import TenantRoutingMiddleware

app = FastAPI(title="Multi-Tenant Billing REST API")

# Mount our custom dynamic data isolation tracking router middleware
app.add_middleware(TenantRoutingMiddleware)

# Register the modular routing controllers
app.include_router(tenant_router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Welcome to the Multi-Tenant Subscription Billing REST API"
    }