"""Tests for FK resolvers."""
import pytest
from src.transform.resolvers import (
    resolve_employee, resolve_truckload_id,
    resolve_payment_method, resolve_payment_status,
    resolve_platform_account,
)


EMPLOYEES = {"jose": 1, "maría": 2, "otro": 3}
TRUCKLOADS = {"A2Z-001": 10, "REG": 20}
PAYMENT_METHODS = {"efectivo": 1, "bizum": 2, "plataforma": 3}
PAYMENT_STATUSES = {"pagado": 1, "pendiente": 2}
ACCOUNTS = {"tienda1": 1, "tienda2": 2}


# ─── resolve_employee ─────────────────────────────────────────────────

class TestResolveEmployee:
    def test_direct(self):
        assert resolve_employee("jose", EMPLOYEES) == 1

    def test_alias_liu(self):
        assert resolve_employee("liu", EMPLOYEES) == 1

    def test_alias_gricel(self):
        assert resolve_employee("gricel", EMPLOYEES) == 1

    def test_alias_david(self):
        assert resolve_employee("david", EMPLOYEES) == 3

    def test_none(self):
        assert resolve_employee(None, EMPLOYEES) is None

    def test_empty(self):
        assert resolve_employee("", EMPLOYEES) is None

    def test_not_found(self):
        assert resolve_employee("unknown_person", EMPLOYEES) is None

    def test_case_insensitive(self):
        assert resolve_employee("Jose", EMPLOYEES) == 1

    def test_dash_null(self):
        assert resolve_employee("-", EMPLOYEES) is None


# ─── resolve_truckload_id ─────────────────────────────────────────────

class TestResolveTruckloadId:
    def test_direct(self):
        assert resolve_truckload_id("A2Z-001", TRUCKLOADS) == 10

    def test_alias(self):
        assert resolve_truckload_id("reg-paolita", TRUCKLOADS) == 20

    def test_none(self):
        assert resolve_truckload_id(None, TRUCKLOADS) is None

    def test_empty(self):
        assert resolve_truckload_id("", TRUCKLOADS) is None

    def test_not_found(self):
        assert resolve_truckload_id("NONEXISTENT", TRUCKLOADS) is None


# ─── resolve_payment_method ───────────────────────────────────────────

class TestResolvePaymentMethod:
    def test_efectivo(self):
        assert resolve_payment_method("efectivo", PAYMENT_METHODS) == 1

    def test_bizum(self):
        assert resolve_payment_method("bizum", PAYMENT_METHODS) == 2

    def test_wallapop_maps_to_plataforma(self):
        assert resolve_payment_method("wallapop", PAYMENT_METHODS) == 3

    def test_none(self):
        assert resolve_payment_method(None, PAYMENT_METHODS) is None

    def test_unknown(self):
        assert resolve_payment_method("crypto", PAYMENT_METHODS) is None

    def test_case_insensitive(self):
        assert resolve_payment_method("BIZUM", PAYMENT_METHODS) == 2


# ─── resolve_payment_status ──────────────────────────────────────────

class TestResolvePaymentStatus:
    def test_pagado(self):
        assert resolve_payment_status("pagado", PAYMENT_STATUSES) == 1

    def test_pendiente(self):
        assert resolve_payment_status("pendiente", PAYMENT_STATUSES) == 2

    def test_none_defaults_pagado(self):
        assert resolve_payment_status(None, PAYMENT_STATUSES) == 1

    def test_unknown_defaults_pagado(self):
        assert resolve_payment_status("xyz", PAYMENT_STATUSES) == 1


# ─── resolve_platform_account ────────────────────────────────────────

class TestResolvePlatformAccount:
    def test_by_name(self):
        assert resolve_platform_account("tienda1", ACCOUNTS) == 1

    def test_by_numeric_id(self):
        assert resolve_platform_account("5", {}) == 5

    def test_by_float_id(self):
        assert resolve_platform_account("3.0", {}) == 3

    def test_none(self):
        assert resolve_platform_account(None, ACCOUNTS) is None

    def test_empty(self):
        assert resolve_platform_account("", ACCOUNTS) is None

    def test_not_found(self):
        assert resolve_platform_account("unknown", ACCOUNTS) is None

    def test_case_insensitive(self):
        assert resolve_platform_account("Tienda1", ACCOUNTS) == 1
