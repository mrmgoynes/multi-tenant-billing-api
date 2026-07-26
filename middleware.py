from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from database import SessionLocal
import models
from tenant_context import set_tenant_schema, clear_tenant_schema

class TenantRoutingMiddleware(BaseHTTPMiddleware):
    """
    Enterprise Middleware Layer: Intercepts all incoming API requests, 
    extracts the routing subdomain header, and sets the safe schema context.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. Bypass tenant routing for universal system endpoints (like core root or docs)
        if request.url.path in ["/", "/docs", "/openapi.json", "/favicon.ico"]:
            clear_tenant_schema()
            return await call_next(request)

        # 2. Extract our custom tenant identification string from the incoming HTTP headers
        tenant_subdomain = request.headers.get("X-Tenant-Subdomain")

        # 3. QA Validation Gate: Reject requests instantly if the tracking header is entirely missing
        if not tenant_subdomain:
            clear_tenant_schema()
            return Response(
                content='{"detail": "Missing required isolation control header: X-Tenant-Subdomain"}',
                status_code=status.HTTP_400_BAD_REQUEST,
                media_type="application/json"
            )

        # 4. Connect over Port 5432 to verify this tenant is registered and active
        db = SessionLocal()
        try:
            tenant = db.query(models.Tenant).filter(
                models.Tenant.subdomain == tenant_subdomain.lower(),
                models.Tenant.status == "active"
            ).first()

            # 5. Security Gate: If the client does not exist or is suspended, block access
            if not tenant:
                return Response(
                    content=f'{{"detail": "Access Denied: Invalid or suspended tenant target \'{tenant_subdomain}\'"}}',
                    status_code=status.HTTP_403_FORBIDDEN,
                    media_type="application/json"
                )

            # 6. Success: Mount the matching schema folder name directly into our async memory context
            set_tenant_schema(tenant.tenant_schema)

        finally:
            db.close()

        # 7. Forward the safely isolated request path down to our core endpoint execution loop
        try:
            response = await call_next(request)
            return response
        finally:
            # 8. Crucial Post-Execution Guard: Wipe memory clean after the response finishes to prevent data leaks
            clear_tenant_schema()