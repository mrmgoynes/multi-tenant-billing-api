from fastapi import FastAPI
from middleware import TenantRoutingMiddleware
from router import router as tenant_router
from customer_router import router as customer_router
from plan_router import router as plan_router # 1. Import the new router

app = FastAPI(title="Multi-Tenant Billing Rest API")

# Mount your enterprise security middleware layer
app.add_middleware(TenantRoutingMiddleware)

# 2. Register your routing matrices cleanly
app.include_router(tenant_router)
app.include_router(customer_router)
app.include_router(plan_router)          # Include the new plans endpoint

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Welcome to the Multi-Tenant Subscription Billing REST API"
    }
