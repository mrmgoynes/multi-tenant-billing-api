-- ==============================================================================
-- CENTRAL MASTER REGISTRY
-- Tracks, authenticates, and dynamically routes tenants to their isolated schemas
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.tenants (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    subdomain VARCHAR(50) NOT NULL UNIQUE,
    tenant_schema VARCHAR(60) NOT NULL UNIQUE,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_tenant_status CHECK (status IN ('active', 'suspended'))
);

-- Ensure lookups on subdomains during API routing are highly optimized and efficient
CREATE INDEX IF NOT EXISTS idx_tenants_subdomain ON public.tenants(subdomain);

