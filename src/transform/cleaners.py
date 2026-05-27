"""
Data cleaning and transformation functions.

Converts raw Google Sheets values to the format expected by PostgreSQL,
handling currency symbols, European/American number formats, date parsing
with multiple format support, weight units, and null value normalization.
"""
import re
import unicodedata
from datetime import datetime, date
from typing import Optional, Any

from src.config.mappings import (
    NULL_VALUES, FEATURES_NULL_VALUES,
    CONDITION_MAP, CONDITION_DEFAULT,
    PAYMENT_STATUS_MAP, PAYMENT_STATUS_DEFAULT,
    INCIDENT_STATUS_MAP, INCIDENT_STATUS_DEFAULT,
    INCIDENT_TYPE_MAP, INCIDENT_TYPE_DEFAULT,
    RESOLUTION_TYPE_KEYWORDS,
    TRANSACTION_TYPE_MAP,
)


def clean_null(value: Any) -> Optional[str]:
    """Convert values representing NULL to None."""
    if value is None:
        return None
    s = str(value).strip()
    if s.lower() in NULL_VALUES:
        return None
    return s


def clean_null_features(value: Any) -> Optional[str]:
    """Like clean_null but also treats 'SIN CARACTERISTICAS' as NULL."""
    if value is None:
        return None
    s = str(value).strip()
    if s.lower() in FEATURES_NULL_VALUES:
        return None
    return s


def clean_price(value: Any) -> Optional[float]:
    """
    Clean a price value removing currency symbols and converting to float.

    Handles both European (1.234,56) and American (1,234.56) formats.
    Examples: '45.00 EUR' -> 45.0, '1.234,56' -> 1234.56, '' -> None
    """
    if value is None:
        return None
    s = str(value).strip()
    if s.lower() in NULL_VALUES:
        return None

    s = s.replace("€", "").replace("EUR", "").replace("$", "").strip()
    if not s:
        return None

    if "," in s and "." in s:
        if s.rindex(",") > s.rindex("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s and "." not in s:
        s = s.replace(",", ".")

    try:
        return float(s)
    except ValueError:
        return None


def clean_weight(value: Any) -> Optional[float]:
    """Convert weight to float. '2' -> 2.0, '1.5kg' -> 1.5."""
    if value is None:
        return None
    s = str(value).strip().lower()
    if s in NULL_VALUES:
        return None
    s = s.replace("kg", "").replace("g", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def map_condition(estado: Any) -> int:
    """Map ESTADO text to condition_id from dim_condition."""
    if estado is None:
        return CONDITION_DEFAULT
    s = str(estado).strip().lower()
    if s in NULL_VALUES:
        return CONDITION_DEFAULT
    return CONDITION_MAP.get(s, CONDITION_DEFAULT)


def map_available(vendido: Any) -> bool:
    """Convert VENDIDO? to available (inverted logic: sold=True means available=False)."""
    if vendido is None:
        return True
    s = str(vendido).strip().upper()
    return s not in ("TRUE", "SI", "SÍ", "YES", "1", "VERDADERO")


def _normalize_text(s: str) -> str:
    """Strip accents and whitespace for fuzzy comparison."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return "".join(s.lower().split())


def map_do_not_list(excepciones: Any) -> bool:
    """True if Excepciones indicates 'No se anuncia' (accent/space insensitive)."""
    if excepciones is None:
        return False
    raw = str(excepciones).strip()
    if not raw or raw.lower() in NULL_VALUES:
        return False
    return _normalize_text(raw) == _normalize_text("No se anuncia")


def map_transaction_type(tipo: Any) -> Optional[str]:
    """Map transaction type to valid CHECK constraint value."""
    if tipo is None:
        return None
    s = str(tipo).strip().lower()
    return TRANSACTION_TYPE_MAP.get(s)


def map_incident_status(estado: Any) -> str:
    """Map incident status text to valid status code."""
    if estado is None:
        return INCIDENT_STATUS_DEFAULT
    s = str(estado).strip().lower()
    return INCIDENT_STATUS_MAP.get(s, INCIDENT_STATUS_DEFAULT)


def parse_incident_action(action: Any) -> dict:
    """
    Parse 'QUE HAY QUE HACER' column:
    - If numeric: discount_amount = abs(number), type = RECLAMACION
    - If text: map to incident_type
    """
    result = {
        "incident_type": INCIDENT_TYPE_DEFAULT,
        "discount_amount": 0.0,
        "refund_amount": 0.0,
    }
    if action is None:
        return result
    s = str(action).strip()
    if s.lower() in NULL_VALUES:
        return result

    cleaned = s.replace("€", "").replace("EUR", "").replace(",", ".").strip()
    try:
        amount = float(cleaned)
        result["discount_amount"] = abs(amount)
        return result
    except ValueError:
        pass

    s_lower = s.lower()
    for key, value in INCIDENT_TYPE_MAP.items():
        if key in s_lower:
            result["incident_type"] = value
            if "completa" in s_lower:
                result["incident_type"] = "DEVOLUCION_COMPLETA"
            return result

    return result


def infer_resolution_type(solucion: Any) -> Optional[str]:
    """Infer resolution_type from solution text using keyword matching."""
    if solucion is None:
        return None
    s = str(solucion).strip().lower()
    if s in NULL_VALUES:
        return None
    for keyword, resolution in RESOLUTION_TYPE_KEYWORDS.items():
        if keyword in s:
            return resolution
    return None


def parse_date(value: Any) -> Optional[date]:
    """
    Parse a date in multiple formats with sanity check (year 2020-2030).

    Supports: YYYY-MM-DD, DD/MM/YYYY, DD/MM/YY, MM/DD/YYYY, etc.
    """
    if value is None:
        return None
    s = str(value).strip()
    if s.lower() in NULL_VALUES:
        return None

    formats = [
        "%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y",
        "%m/%d/%Y", "%m/%d/%y", "%d-%m-%Y",
        "%d-%m-%y", "%Y/%m/%d",
    ]
    for fmt in formats:
        try:
            parsed = datetime.strptime(s, fmt).date()
            if 2020 <= parsed.year <= 2030:
                return parsed
        except ValueError:
            continue
    return None


def resolve_listing_price(precio_revisado: Any, pvp: Any) -> Optional[float]:
    """PRECIO REVISADO takes priority, fallback to PVP."""
    price = clean_price(precio_revisado)
    if price is not None:
        return price
    return clean_price(pvp)
