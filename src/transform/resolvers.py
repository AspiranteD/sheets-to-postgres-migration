"""
Resolvers that map free-text values to database foreign keys.

Each resolver takes a raw text value and a lookup dictionary (DB state)
and returns the resolved FK integer or None.
"""
from typing import Optional, Any

from src.config.mappings import (
    NULL_VALUES, EMPLOYEE_ALIASES, TRUCKLOAD_ALIASES,
    PAYMENT_METHOD_MAP, PAYMENT_STATUS_MAP, PAYMENT_STATUS_DEFAULT,
)


def resolve_employee(persona: Any, employees_map: dict[str, int]) -> Optional[int]:
    """
    Resolve person name to employee_id with alias support.

    Aliases handle cases like multiple people mapping to the same employee
    (e.g., "liu" -> "jose", "gricel" -> "jose").
    """
    if persona is None:
        return None
    s = str(persona).strip().lower()
    if s in NULL_VALUES:
        return None

    resolved = employees_map.get(s)
    if resolved is not None:
        return resolved

    alias = EMPLOYEE_ALIASES.get(s)
    if alias:
        resolved = employees_map.get(alias)
        if resolved is None and alias in ("jose", "josé"):
            other = "josé" if alias == "jose" else "jose"
            resolved = employees_map.get(other)
    return resolved


def resolve_truckload_id(
    id_a2z_text: Any, truckloads_map: dict[str, int]
) -> Optional[int]:
    """Resolve A2Z text ID to numeric truckload id with alias support."""
    if id_a2z_text is None:
        return None
    s = str(id_a2z_text).strip()
    if s.lower() in NULL_VALUES:
        return None
    s = TRUCKLOAD_ALIASES.get(s, s)
    return truckloads_map.get(s)


def resolve_payment_method(
    modo: Any, payment_methods_db: dict[str, int]
) -> Optional[int]:
    """Map payment method text to dim_payment_method.method_id."""
    if modo is None:
        return None
    s = str(modo).strip().lower()
    code = PAYMENT_METHOD_MAP.get(s)
    if code is None:
        return None
    return payment_methods_db.get(code.lower())


def resolve_payment_status(
    estado: Any, payment_statuses_db: dict[str, int]
) -> Optional[int]:
    """Map payment status text to dim_payment_status.status_id."""
    if estado is None:
        code = PAYMENT_STATUS_DEFAULT
    else:
        s = str(estado).strip().lower()
        code = PAYMENT_STATUS_MAP.get(s, PAYMENT_STATUS_DEFAULT)
    return payment_statuses_db.get(code.lower())


def resolve_platform_account(
    cuenta: Any, accounts_map: dict[str, int]
) -> Optional[int]:
    """Resolve account name or numeric ID to platform_account.id."""
    if cuenta is None:
        return None
    s = str(cuenta).strip()
    if s.lower() in NULL_VALUES:
        return None
    try:
        return int(float(s))
    except (ValueError, TypeError):
        pass
    return accounts_map.get(s.lower())
