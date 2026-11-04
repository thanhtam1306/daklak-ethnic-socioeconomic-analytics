"""
Core Data & Semantic Layer Modules
"""
from .db import get_db_connection, execute_query, test_connection
from .sql_guardrails import validate_and_sanitize_sql, SQLSecurityError
from .catalog import METRIC_CATALOG, BUDGET_STANDARDS, DISTRICT_ALIASES, ETHNIC_GROUPS, VIEWS_CATALOG

__all__ = [
    "get_db_connection",
    "execute_query",
    "test_connection",
    "validate_and_sanitize_sql",
    "SQLSecurityError",
    "METRIC_CATALOG",
    "BUDGET_STANDARDS",
    "DISTRICT_ALIASES",
    "ETHNIC_GROUPS",
    "VIEWS_CATALOG",
]
