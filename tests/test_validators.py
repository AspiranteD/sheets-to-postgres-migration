"""Tests for src.transform.validators."""

import pytest
from src.transform.validators import (
    ValidationRule,
    ValidationError,
    validate_row,
    validate_batch,
)


class TestValidateRow:
    def test_required_passes(self):
        rule = ValidationRule(field="name", rule_type="required")
        errors = validate_row({"name": "Alice"}, [rule])
        assert len(errors) == 0

    def test_required_fails_none(self):
        rule = ValidationRule(field="name", rule_type="required")
        errors = validate_row({"name": None}, [rule])
        assert len(errors) == 1
        assert errors[0].rule_type == "required"

    def test_required_fails_empty(self):
        rule = ValidationRule(field="name", rule_type="required")
        errors = validate_row({"name": "  "}, [rule])
        assert len(errors) == 1

    def test_min_length_passes(self):
        rule = ValidationRule(field="name", rule_type="min_length", params={"min": 3})
        errors = validate_row({"name": "Alice"}, [rule])
        assert len(errors) == 0

    def test_min_length_fails(self):
        rule = ValidationRule(field="name", rule_type="min_length", params={"min": 10})
        errors = validate_row({"name": "Al"}, [rule])
        assert len(errors) == 1

    def test_max_length_passes(self):
        rule = ValidationRule(field="name", rule_type="max_length", params={"max": 10})
        errors = validate_row({"name": "Alice"}, [rule])
        assert len(errors) == 0

    def test_max_length_fails(self):
        rule = ValidationRule(field="name", rule_type="max_length", params={"max": 3})
        errors = validate_row({"name": "Alice"}, [rule])
        assert len(errors) == 1

    def test_regex_passes(self):
        rule = ValidationRule(field="code", rule_type="regex", params={"pattern": r"^[A-Z]{3}\d{3}$"})
        errors = validate_row({"code": "ABC123"}, [rule])
        assert len(errors) == 0

    def test_regex_fails(self):
        rule = ValidationRule(field="code", rule_type="regex", params={"pattern": r"^[A-Z]{3}\d{3}$"})
        errors = validate_row({"code": "abc"}, [rule])
        assert len(errors) == 1

    def test_range_passes(self):
        rule = ValidationRule(field="price", rule_type="range", params={"min": 0, "max": 100})
        errors = validate_row({"price": 50}, [rule])
        assert len(errors) == 0

    def test_range_fails_below(self):
        rule = ValidationRule(field="price", rule_type="range", params={"min": 10, "max": 100})
        errors = validate_row({"price": 5}, [rule])
        assert len(errors) == 1

    def test_range_fails_above(self):
        rule = ValidationRule(field="price", rule_type="range", params={"min": 0, "max": 100})
        errors = validate_row({"price": 150}, [rule])
        assert len(errors) == 1

    def test_enum_passes(self):
        rule = ValidationRule(field="status", rule_type="enum", params={"values": ["active", "inactive"]})
        errors = validate_row({"status": "active"}, [rule])
        assert len(errors) == 0

    def test_enum_fails(self):
        rule = ValidationRule(field="status", rule_type="enum", params={"values": ["active", "inactive"]})
        errors = validate_row({"status": "deleted"}, [rule])
        assert len(errors) == 1

    def test_none_skips_non_required(self):
        rule = ValidationRule(field="name", rule_type="min_length", params={"min": 3})
        errors = validate_row({"name": None}, [rule])
        assert len(errors) == 0


class TestValidateBatch:
    def test_all_pass(self):
        rules = [ValidationRule(field="name", rule_type="required")]
        rows = [{"name": "Alice"}, {"name": "Bob"}]
        result = validate_batch(rows, rules)
        assert result["total_rows"] == 2
        assert result["passed"] == 2
        assert result["failed"] == 0

    def test_some_fail(self):
        rules = [ValidationRule(field="name", rule_type="required")]
        rows = [{"name": "Alice"}, {"name": None}, {"name": "Carol"}]
        result = validate_batch(rows, rules)
        assert result["total_rows"] == 3
        assert result["passed"] == 2
        assert result["failed"] == 1

    def test_unique_check(self):
        rules = [ValidationRule(field="id", rule_type="unique")]
        rows = [{"id": "A"}, {"id": "B"}, {"id": "A"}]
        result = validate_batch(rows, rules)
        assert result["failed"] == 1
        assert result["by_rule"]["unique"] == 1

    def test_by_rule_breakdown(self):
        rules = [
            ValidationRule(field="name", rule_type="required"),
            ValidationRule(field="age", rule_type="range", params={"min": 0, "max": 150}),
        ]
        rows = [{"name": None, "age": 200}]
        result = validate_batch(rows, rules)
        assert "required" in result["by_rule"]
        assert "range" in result["by_rule"]
