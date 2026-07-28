from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from database import SessionLocal
import models
from tenant_context import set_tenant_schema, clear_tenant_schema

class TenantRoutingMiddleware(BaseHTTPMiddleware):
    """
    Enterprise Middleware Layer:
    Intercepts incoming API calls, extracts the subdomain header, 
    authenticates the tenant, and configures dynamic path routing.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        
        # 1. ARCHITECTURE UPGRADE: Exempt universal routes AND the onboarding directory path
        if (
            request.url.path in ["/", "/docs", "/openapi.json", "/favicon.ico"] 
            or request.url.path.startswith("/tenants")
        ):
            clear_tenant_schema()
            return await call_next(request)

        # 2. Extract client isolation headers for tenant-specific sub-resources
        tenant_subdomain = request.headers.get("X-Tenant-Subdomain")

        # 3. QA Validation Gate: Block requests trying to hit resources without identification
        if not tenant_subdomain:
            clear_tenant_schema()
            return Response(
                content='{"detail": "Missing required isolation control header: X-Tenant-Subdomain"}',
                status_code=status.HTTP_400_BAD_REQUEST,
                media_type="application/json"
            )

        # 4. Process secure tenant routing
        db = SessionLocal()
        try:
            tenant = db.query(models.Tenant).filter(
                models.Tenant.subdomain == tenant_subdomain.lower(),
                models.Tenant.status == "active"
            ).first()

            # CRITICAL SECURITY RULE: If no active record exists, halt execution immediately!
            # This prevents queries from executing against the fallback 'public' schema.
            if not tenant:
                return Response(
                    content=f'{{"detail": "Access Denied: Invalid, inactive, or suspended tenant target \'{tenant_subdomain}\'"}}',
                    status_code=status.HTTP_403_FORBIDDEN,
                    media_type="application/json"
                )
                
            # Bind the valid schema string to the thread-safe ContextVar
            set_tenant_schema(tenant.tenant_schema)
            
        finally:
            db.close()

        # 5. Route Execution: Process the endpoint under the isolated schema envelope
        try:
            response = await call_next(request)
            return response
        finally:
            # Always scrub memory registers clear when the request cycle completes
            clear_tenant_schema()
