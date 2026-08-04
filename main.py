# main.py
from fastapi import FastAPI
from middleware import TenantRoutingMiddleware
from router import router as tenant_router
from customer_router import router as customer_router
from plan_router import router as plan_router
from subscription_router import router as subscription_router
from invoice_router import router as invoice_router # Import the new invoicing router
from usage_router import router as usage_router # Import the new usage router

app = FastAPI(title="Multi-Tenant Billing Rest API")

app.add_middleware(TenantRoutingMiddleware)

app.include_router(tenant_router)
app.include_router(customer_router)
app.include_router(plan_router)
app.include_router(subscription_router)
app.include_router(invoice_router)             # Mount the billing accounting layer
app.include_router(usage_router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Welcome to the Multi-Tenant Subscription Billing REST API"
    }
