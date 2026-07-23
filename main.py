from fastapi import FastAPI
from router import router as tenant_router

app = FastAPI(title="Multi-Tenant Billing REST API")

# Register the modular routing engine
app.include_router(tenant_router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Welcome to the Multi-Tenant Subscription Billing REST API"
    }