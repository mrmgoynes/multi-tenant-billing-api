from fastapi import FastAPI

# Initialize the core FastAPI engine application
app = FastAPI(title="Multi-Tenant Billing REST API")

@app.get("/")
def read_root():
    """
    A simple health-check endpoint to verify the API is online.
    """
    return {
        "status": "online",
        "message": "Welcome to the Multi-Tenant Subscription Billing REST API"
    }