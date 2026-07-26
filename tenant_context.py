from contextvars import ContextVar

# A thread-safe, isolated memory storage cell to hold the active request's target schema name
_tenant_schema_context: ContextVar[str] = ContextVar("tenant_schema", default="public")

def set_tenant_schema(schema_name: str) -> None:
    """
    Sets the database schema destination for the currently executing request thread.
    """
    _tenant_schema_context.set(schema_name)

def get_tenant_schema() -> str:
    """
    Retrieves the database schema destination for the active request thread.
    """
    return _tenant_schema_context.get()

def clear_tenant_schema() -> None:
    """
    Resets the context allocation cell back to the default central public schema.
    """
    _tenant_schema_context.set("public")