# Enterprise Multi-Tenant SaaS Billing Engine (FastAPI & PostgreSQL)

An enterprise-grade, highly resilient multi-tenant SaaS billing platform built with **FastAPI** and **PostgreSQL (Docker)**. This system features dynamic database schema routing to prevent cross-tenant data leaks and a robust **10-case automated test suite** covering happy paths, boundary validations, security injections, and asynchronous background accounting workers.

---

## 🛠 Architectural Blueprint & Core Tech Stack

- **Framework:** FastAPI (Python 3.14+)
- **Database Engine:** PostgreSQL 16 (Alpine Containerization)
- **Object-Relational Mapper (ORM):** SQLAlchemy 2.0 (Dynamic Search Path Execution)
- **Data Ingestion Validation:** Pydantic v2 (Input Sanitization & Output Masking)
- **Automated Testing Ecosystem:** Pytest 9.0 (Dynamic Lifecycle Sandbox Management)
- **Secret & Config Management:** Python-Dotenv (`.env` Security Separation)

```text
                       ┌────────────────────────┐
                       │   Inbound API Request   │
                       └───────────┬────────────┘
                                   │ (X-Tenant-Subdomain: 'stark')
                                   ▼
                       ┌────────────────────────┐
                       │ TenantRoutingMiddleware│
                       └───────────┬────────────┘
                                   │ (Verifies Tenant Context)
                                   ▼
                       ┌────────────────────────┐
                       │  database.py (get_db)  │
                       └───────────┬────────────┘
                                   │ (Executes: SET search_path TO "tenant_stark")
                                   ▼
                ┌──────────────────────────────────────┐
                │   PostgreSQL Engine (Inside Docker)  │
                │ ┌──────────────────┐ ┌─────────────┐ │
                │ │ public.tenants   │ │tenant_stark │ │
                │ │ (Master Registry)│ │(Customers)  │ │
                │ └──────────────────┘ └─────────────┘ │
                └──────────────────────────────────────┘
```

---

## 🔒 Multi-Tenant Data Isolation Strategy (Security Matrix)

This application implements a **Logical Schema-Per-Tenant** pattern to isolate database transactions completely. 
1. **The Gateway Handshake:** When an API request hits the server, a custom ASGI `TenantRoutingMiddleware` intercepts the payload and parses the `X-Tenant-Subdomain` header.
2. **Dynamic Context-Switching:** Your database dependency engine executes a real-time `SET search_path TO "tenant_<subdomain>", public;` query over **Port 5432**.
3. **The Secure Vault:** All subsequent table operations (`customers`, `plans`, `invoices`, `usage_records`) are dynamically restricted to that tenant's dedicated namespace folder. Data leaks are physically impossible because tenants cannot view adjacent schemas.

---

## 📊 Comprehensive 10-Case SDET & QA Automation Test Matrix

The project features a defensive automated regression suite built using an advanced SDET mindset. Every execution relies on dynamic teardown fixtures that clear generated database schema namespaces, ensuring a clean, unpolluted sandbox environment.

### 🟢 Happy Path & Structural Verification
- **Test 1: Cross-Tenant Data Isolation** — Confirms data written into Tenant A (`tenant_stark`) is completely invisible and locked away from queries executing under Tenant B (`tenant_lannister`).
- **Test 2: Automatic Infrastructure Plan Seeding** — Verifies that whenever a new tenant is onboarded, our automation script clones the master blueprint layout and seeds base subscription metrics (`Basic`, `Pro`, `Enterprise`) into the new table container.

### 🔴 Defensive Input Validation & Boundary Testing (Negative Paths)
- **Test 3: Malformed Email Interception** — Forces a malformed email payload (`"sam.tarly@citadel"`) to pass through the schema gate and asserts that Pydantic drops it with a `422 Unprocessable Entity` before it touches the database.
- **Test 4: String Length Boundary Violation** — Submits an input name string exceeding `max_length=50` characters, validating that the API actively safeguards itself from database truncation vulnerabilities.

### 🛡️ Security Gateways & Access Control
- **Test 5: Missing Security Control Header** — Attempts to make modifications to data resources without passing the `X-Tenant-Subdomain` header. Confirms the middleware blocks anonymous traffic with a `400 Bad Request`.
- **Test 6: Unauthorized Tenant Routing Bypass** — Dispatches a valid payload with a non-existent subdomain header (`"white_walkers"`). Asserts that the system drops execution instantly with a `403 Forbidden` response.

### 💼 Business Logic & Financial Accounting Operations
- **Test 7: Cross-Tenant Unique Identity Isolation** — Confirms that if a customer registers an email in Tenant A, it does not lock out or conflict with a separate Tenant B registering the identical email address within their isolated table workspace.
- **Test 8: Automated Invoice Sequencing** — Generates consecutive customer invoices within a workspace and asserts that tracking counters automatically generate sequential strings (`INV-STARK-0001` ➔ `INV-STARK-0002`).
- **Test 9: Advanced Mid-Cycle Prorated Billing** — Triggers a mid-month upgrade request from the Basic to Pro plan, verifying that the proration engine cancels the old subscription and automatically generates a precisely balanced adjustment invoice row.
- **Test 10: Cross-Schema Midnight Billing Cron Loop** — Executes a background worker task that cycles through all tenants, aggregates unbilled telemetry usage metrics, and compiles a single composite renewal invoice completely automatically.

---

## 🚀 Local Ingestion & Deployment Script

1. **Clone the project repository and create your local environment variables:**
   ```bash
   git clone <your-repository-url>
   cd multi_tenant_billing
   ```
2. **Secure Your Environment Properties:**
   Create a local `.env` file in the root directory:
   ```env
   DATABASE_URL=postgresql+psycopg://admin:SecretPassword123@localhost:5432/billing_system
   ```
3. **Spin Up Containerized Infrastructure:**
   ```bash
   docker compose up -d
   ```
4. **Initialize Your Virtual Environment & Dependencies:**
   ```bash
   python -m venv .venv
   source .venv/Scripts/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
5. **Execute the Complete Automation Test Suite:**
   ```bash
   pytest -v -W=ignore
   ```
