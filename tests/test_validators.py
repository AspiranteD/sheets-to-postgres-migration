"""Tests for row validators."""
import pytest
from src.validate.row_validators import (
    validate_physical_item, validate_listing, validate_sale,
    validate_cash_transaction, validate_incident,
    RowStatus, VALIDATORS,
)


# ─── validate_physical_item ───────────────────────────────────────────

class TestValidatePhysicalItem:
    def test_valid(self):
        row = {"lpn": "LPN001", "asin": "B08XYZ", "condition_id": 1,
               "purchase_price": 50.0}
        assert validate_physical_item(row, {}) == []

    def test_empty_lpn(self):
        row = {"lpn": "", "asin": "B08XYZ", "condition_id": 1}
        errors = validate_physical_item(row, {})
        assert any("LPN" in e for e in errors)

    def test_none_lpn(self):
        row = {"asin": "B08XYZ", "condition_id": 1}
        errors = validate_physical_item(row, {})
        assert any("LPN" in e for e in errors)

    def test_duplicate_lpn(self):
        row = {"lpn": "LPN001", "asin": "B08XYZ", "condition_id": 1}
        ctx = {"existing_lpns": {"LPN001"}}
        errors = validate_physical_item(row, ctx)
        assert any("ya existe" in e for e in errors)

    def test_empty_asin(self):
        row = {"lpn": "LPN001", "asin": "", "condition_id": 1}
        errors = validate_physical_item(row, {})
        assert any("ASIN" in e for e in errors)

    def test_invalid_condition(self):
        row = {"lpn": "LPN001", "asin": "X", "condition_id": 99}
        errors = validate_physical_item(row, {})
        assert any("condition_id" in e for e in errors)

    def test_none_condition(self):
        row = {"lpn": "LPN001", "asin": "X", "condition_id": None}
        errors = validate_physical_item(row, {})
        assert any("condition_id" in e for e in errors)

    def test_non_numeric_price(self):
        row = {"lpn": "LPN001", "asin": "X", "condition_id": 1,
               "purchase_price": "abc"}
        errors = validate_physical_item(row, {})
        assert any("purchase_price" in e for e in errors)

    def test_non_numeric_weight(self):
        row = {"lpn": "LPN001", "asin": "X", "condition_id": 1,
               "weight_kg": "heavy"}
        errors = validate_physical_item(row, {})
        assert any("weight_kg" in e for e in errors)

    def test_unresolved_truckload(self):
        row = {"lpn": "LPN001", "asin": "X", "condition_id": 1,
               "_id_a2z_raw": "A2Z-999", "id_a2z": None}
        errors = validate_physical_item(row, {})
        assert any("A2Z" in e for e in errors)

    def test_all_valid_conditions(self):
        for cid in range(1, 6):
            row = {"lpn": "X", "asin": "Y", "condition_id": cid}
            assert validate_physical_item(row, {}) == []


# ─── validate_listing ────────────────────────────────────────────────

class TestValidateListing:
    def test_valid(self):
        row = {"lpn": "LPN001", "title": "Product", "listing_price": 99.0}
        assert validate_listing(row, {}) == []

    def test_empty_lpn(self):
        row = {"lpn": "", "title": "X"}
        errors = validate_listing(row, {})
        assert any("LPN" in e for e in errors)

    def test_empty_title(self):
        row = {"lpn": "X", "title": ""}
        errors = validate_listing(row, {})
        assert any("titulo" in e for e in errors)

    def test_non_numeric_price(self):
        row = {"lpn": "X", "title": "Y", "listing_price": "abc"}
        errors = validate_listing(row, {})
        assert any("listing_price" in e for e in errors)


# ─── validate_sale ───────────────────────────────────────────────────

class TestValidateSale:
    def test_valid(self):
        row = {"lpn": "LPN001", "final_price": 100.0}
        assert validate_sale(row, {}) == []

    def test_empty_lpn(self):
        row = {"lpn": "", "final_price": 100.0}
        errors = validate_sale(row, {})
        assert any("LPN" in e for e in errors)

    def test_none_price(self):
        row = {"lpn": "X", "final_price": None}
        errors = validate_sale(row, {})
        assert any("final_price" in e for e in errors)

    def test_non_numeric_price(self):
        row = {"lpn": "X", "final_price": "abc"}
        errors = validate_sale(row, {})
        assert any("final_price" in e for e in errors)


# ─── validate_cash_transaction ───────────────────────────────────────

class TestValidateCashTransaction:
    def _valid_row(self):
        return {
            "transaction_type": "INGRESO", "amount": 50.0,
            "employee_id": 1, "payment_method_id": 1,
            "payment_status_id": 1, "transaction_date": "2024-01-01",
        }

    def test_valid(self):
        assert validate_cash_transaction(self._valid_row(), {}) == []

    def test_invalid_type(self):
        row = self._valid_row()
        row["transaction_type"] = "GASTO"
        errors = validate_cash_transaction(row, {})
        assert any("transaction_type" in e for e in errors)

    def test_none_amount(self):
        row = self._valid_row()
        row["amount"] = None
        errors = validate_cash_transaction(row, {})
        assert any("amount" in e for e in errors)

    def test_none_employee(self):
        row = self._valid_row()
        row["employee_id"] = None
        row["_employee_name_raw"] = "John"
        errors = validate_cash_transaction(row, {})
        assert any("employee_id" in e for e in errors)

    def test_none_payment_method(self):
        row = self._valid_row()
        row["payment_method_id"] = None
        row["_payment_method_raw"] = "crypto"
        errors = validate_cash_transaction(row, {})
        assert any("payment_method_id" in e for e in errors)

    def test_none_payment_status(self):
        row = self._valid_row()
        row["payment_status_id"] = None
        errors = validate_cash_transaction(row, {})
        assert any("payment_status_id" in e for e in errors)

    def test_none_date(self):
        row = self._valid_row()
        row["transaction_date"] = None
        errors = validate_cash_transaction(row, {})
        assert any("transaction_date" in e for e in errors)


# ─── validate_incident ──────────────────────────────────────────────

class TestValidateIncident:
    def _valid_row(self):
        return {
            "sale_id": 1, "incident_type": "RECLAMACION",
            "status": "ABIERTA", "buyer_problem_description": "Item broken",
        }

    def test_valid(self):
        assert validate_incident(self._valid_row(), {}) == []

    def test_none_sale_id(self):
        row = self._valid_row()
        row["sale_id"] = None
        row["lpn"] = "LPN001"
        errors = validate_incident(row, {})
        assert any("sale_id" in e for e in errors)

    def test_invalid_type(self):
        row = self._valid_row()
        row["incident_type"] = "INVALID"
        errors = validate_incident(row, {})
        assert any("incident_type" in e for e in errors)

    def test_invalid_status(self):
        row = self._valid_row()
        row["status"] = "INVALID"
        errors = validate_incident(row, {})
        assert any("status" in e for e in errors)

    def test_empty_description(self):
        row = self._valid_row()
        row["buyer_problem_description"] = ""
        errors = validate_incident(row, {})
        assert any("buyer_problem_description" in e for e in errors)

    def test_all_valid_types(self):
        valid_types = {
            "DEVOLUCION_COMPLETA", "DEVOLUCION_PARCIAL", "RECLAMACION",
            "DISPUTA_PLATAFORMA", "ERROR_ENVIO", "PRODUCTO_DEFECTUOSO", "OTRO",
        }
        for t in valid_types:
            row = self._valid_row()
            row["incident_type"] = t
            errs = [e for e in validate_incident(row, {}) if "incident_type" in e]
            assert errs == [], f"Type {t} should be valid"


# ─── VALIDATORS dict ────────────────────────────────────────────────

def test_validators_dict_keys():
    assert set(VALIDATORS.keys()) == {
        "physical_item", "listing", "sale", "cash_transaction", "incident",
    }


def test_row_status_constants():
    assert RowStatus.VALID == "VALIDA"
    assert RowStatus.CRITICAL == "ERROR_CRITICO"
    assert RowStatus.SKIP == "OMITIR"
