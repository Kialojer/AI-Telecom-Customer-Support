"""Synthetic demo snapshots and an optional PostgreSQL adapter."""
import os
import random
from copy import deepcopy

from graph import Customer


DEMO_CUSTOMERS: list[Customer] = [
    {"id": "demo-ana", "name": "Ana", "plan": "Fibra 500 Demo", "interests": ["streaming"],
     "marketing_opt_in": True, "invoice_total": "99,90"},
    {"id": "demo-bruno", "name": "Bruno", "plan": "Movel 20GB Demo", "interests": ["internet"],
     "marketing_opt_in": True, "invoice_total": "59,90"},
    {"id": "demo-carla", "name": "Carla", "plan": "Fibra 300 Demo", "interests": ["internet"],
     "marketing_opt_in": False, "invoice_total": "79,90"},
]

# Reference DDL only; never executed at import or application startup.
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS portfolio_customers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    plan TEXT NOT NULL,
    interests TEXT[] NOT NULL DEFAULT '{}',
    marketing_opt_in BOOLEAN NOT NULL DEFAULT FALSE,
    invoice_total NUMERIC(10,2) NOT NULL CHECK (invoice_total >= 0)
);
"""


def get_random_customer() -> Customer:
    """Pick a synthetic customer once per request, before entering the graph."""
    return deepcopy(random.choice(DEMO_CUSTOMERS))


def load_customer_from_postgres(customer_id: str) -> Customer | None:
    """Optional explicit lookup, outside LangGraph; no random real-user lookup.

    DATABASE_URL must be provided by the caller's environment. This adapter
    is deliberately not wired to the unauthenticated demo HTTP endpoint.
    """
    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row, connect_timeout=5) as conn:
        row = conn.execute(
            "SELECT id, name, plan, interests, marketing_opt_in, invoice_total "
            "FROM portfolio_customers WHERE id = %s", (customer_id,),
        ).fetchone()
    if row is None:
        return None
    row["invoice_total"] = format(row["invoice_total"], ".2f").replace(".", ",")
    return Customer(**row)
