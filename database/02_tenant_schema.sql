-- ==============================================================================
-- 1. BASE SCHEMA WORKSPACE DEFINITION
-- Spawns the central blueprint folder namespace used for dynamic tenant cloning
-- ==============================================================================
CREATE SCHEMA IF NOT EXISTS tenant_template;

-- ==============================================================================
-- 2. BLUEPRINT TABLE STRUCTURES
-- Defines the baseline data layout cloned programmatically during tenant onboarding
-- ==============================================================================

-- Core Customer Tracking Table Layout
CREATE TABLE IF NOT EXISTS tenant_template.customers (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Core Financial Subscription Tracking Table Layout
CREATE TABLE IF NOT EXISTS tenant_template.subscriptions (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    plan_id INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    start_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Open database/02_tenant_schema.sql and update the invoices block to look exactly like this:
CREATE TABLE IF NOT EXISTS tenant_template.invoices (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    invoice_number VARCHAR(30) NOT NULL UNIQUE,  -- ADD THIS CRITICAL SEQUENCER COLUMN
    amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'unpaid',
    due_date TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- PHASE 18 ARCHITECTURE: Foundational Subscription Product Tier Layout
CREATE TABLE IF NOT EXISTS tenant_template.plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    billing_cycle VARCHAR(20) DEFAULT 'monthly',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
