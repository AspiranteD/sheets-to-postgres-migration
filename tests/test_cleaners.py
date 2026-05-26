"""Tests for src.transform.cleaners."""

import pytest
from datetime import datetime
from src.transform.cleaners import (
    clean_string,
    clean_price,
    clean_date,
    clean_boolean,
    normalize_lpn,
    clean_row,
    fix_encoding,
)


class TestCleanString:
    def test_strips_whitespace(self):
        assert clean_string("  hello  ") == "hello"

    def test_removes_control_chars(self):
        assert clean_string("hel\x00lo") == "hello"

    def test_normalizes_unicode(self):
        assert clean_string("café") is not None

    def test_none_returns_none(self):
        assert clean_string(None) is None

    def test_empty_returns_none(self):
        assert clean_string("   ") is None

    def test_non_string_coerced(self):
        assert clean_string(42) == "42"


class TestCleanPrice:
    def test_euro_format(self):
        assert clean_price("29,99 €") == 29.99

    def test_dollar_format(self):
        assert clean_price("$29.99") == 29.99

    def test_plain_float(self):
        assert clean_price("29.99") == 29.99

    def test_comma_decimal(self):
        assert clean_price("1.299,50") == 1299.50

    def test_none_returns_none(self):
        assert clean_price(None) is None

    def test_empty_returns_none(self):
        assert clean_price("") is None

    def test_invalid_returns_none(self):
        assert clean_price("abc") is None


class TestCleanDate:
    def test_iso_format(self):
        result = clean_date("2024-01-15")
        assert result == datetime(2024, 1, 15)

    def test_european_format(self):
        result = clean_date("15/01/2024")
        assert result == datetime(2024, 1, 15)

    def test_dot_format(self):
        result = clean_date("15.01.2024")
        assert result == datetime(2024, 1, 15)

    def test_none_returns_none(self):
        assert clean_date(None) is None

    def test_invalid_returns_none(self):
        assert clean_date("not-a-date") is None

    def test_datetime_passthrough(self):
        dt = datetime(2024, 6, 1)
        assert clean_date(dt) is dt


class TestCleanBoolean:
    def test_true_variants(self):
        for val in ["true", "yes", "sí", "1", "True", "YES", "Sí"]:
            assert clean_boolean(val) is True, f"Expected True for '{val}'"

    def test_false_variants(self):
        for val in ["false", "no", "0", "False", "NO"]:
            assert clean_boolean(val) is False, f"Expected False for '{val}'"

    def test_none_returns_none(self):
        assert clean_boolean(None) is None

    def test_invalid_returns_none(self):
        assert clean_boolean("maybe") is None


class TestNormalizeLpn:
    def test_valid_lpn(self):
        assert normalize_lpn("lpnab123456") == "LPNAB123456"

    def test_invalid_format(self):
        assert normalize_lpn("ABC123") is None

    def test_none_returns_none(self):
        assert normalize_lpn(None) is None

    def test_empty_returns_none(self):
        assert normalize_lpn("") is None


class TestCleanRow:
    def test_applies_type_cleaners(self):
        row = {"name": "  Alice  ", "price": "29,99 €", "active": "sí"}
        types = {"name": "string", "price": "price", "active": "boolean"}
        result = clean_row(row, types)
        assert result["name"] == "Alice"
        assert result["price"] == 29.99
        assert result["active"] is True

    def test_defaults_to_string_cleaner(self):
        row = {"unknown_col": "  test  "}
        result = clean_row(row, {})
        assert result["unknown_col"] == "test"


class TestFixEncoding:
    def test_removes_bom(self):
        result = fix_encoding("\ufeffhello")
        assert "hello" in result

    def test_plain_text_passthrough(self):
        assert fix_encoding("hello") == "hello"
