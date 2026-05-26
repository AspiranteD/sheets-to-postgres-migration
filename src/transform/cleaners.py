"""Data cleaning utilities for raw spreadsheet values."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Any

_DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
    "%d.%m.%Y",
    "%B %d, %Y",
    "%b %d, %Y",
    "%d %B %Y",
    "%d %b %Y",
]

_TRUTHY = {"true", "yes", "sí", "si", "1", "verdadero", "t", "y"}
_FALSY = {"false", "no", "0", "falso", "f", "n"}

_LPN_PATTERN = re.compile(r"^LPN[A-Z]{2}\d{6,}$")

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_string(value: Any) -> str | None:
    """Strip whitespace, normalize unicode, remove control characters."""
    if value is None:
        return None
    text = str(value)
    text = unicodedata.normalize("NFC", text)
    text = _CONTROL_CHARS.sub("", text)
    text = text.strip()
    return text if text else None


def clean_price(value: Any) -> float | None:
    """Parse price strings like '29,99 €', '$29.99', '29.99' into float."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = re.sub(r"[€$£¥\s]", "", text)
    if "," in text and "." in text:
        if text.index(",") > text.index("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        return round(float(text), 2)
    except ValueError:
        return None


def clean_date(value: Any) -> datetime | None:
    """Try multiple date formats and return a datetime or None."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def clean_boolean(value: Any) -> bool | None:
    """Convert 'sí'/'no'/'true'/'1' etc. to bool."""
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    if text in _TRUTHY:
        return True
    if text in _FALSY:
        return False
    return None


def normalize_lpn(value: Any) -> str | None:
    """Uppercase and validate LPN format (LPNXX######)."""
    if value is None:
        return None
    text = str(value).strip().upper()
    if not text:
        return None
    if _LPN_PATTERN.match(text):
        return text
    return None


def clean_row(row: dict[str, Any], column_types: dict[str, str]) -> dict[str, Any]:
    """Apply the appropriate cleaner to each column based on its declared type.

    Supported types: ``string``, ``price``, ``date``, ``boolean``, ``lpn``.
    Columns not listed in *column_types* are passed through with
    ``clean_string``.
    """
    cleaners = {
        "string": clean_string,
        "price": clean_price,
        "date": clean_date,
        "boolean": clean_boolean,
        "lpn": normalize_lpn,
    }
    cleaned: dict[str, Any] = {}
    for col, val in row.items():
        col_type = column_types.get(col, "string")
        cleaner = cleaners.get(col_type, clean_string)
        cleaned[col] = cleaner(val)
    return cleaned


def fix_encoding(text: str) -> str:
    """Attempt to fix mojibake from Latin-1 / UTF-8 BOM misreads."""
    if text.startswith("\ufeff"):
        text = text[1:]
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text
