"""Row-level and batch validation for cleaned data."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationRule:
    """A single validation constraint on a field."""

    field: str
    rule_type: str  # required | min_length | max_length | regex | range | enum | unique
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationError:
    """Describes a single validation failure."""

    row_index: int
    field: str
    rule_type: str
    message: str


def validate_row(row: dict[str, Any], rules: list[ValidationRule], row_index: int = 0) -> list[ValidationError]:
    """Validate a single row against a list of rules."""
    errors: list[ValidationError] = []
    for rule in rules:
        value = row.get(rule.field)
        error = _check_rule(value, rule, row_index)
        if error:
            errors.append(error)
    return errors


def validate_batch(
    rows: list[dict[str, Any]],
    rules: list[ValidationRule],
) -> dict[str, Any]:
    """Validate many rows and return an aggregate summary.

    Returns a dict with ``total_rows``, ``passed``, ``failed``,
    ``errors`` (list), and ``by_rule`` breakdown.
    """
    all_errors: list[ValidationError] = []
    failed_indices: set[int] = set()

    unique_tracker: dict[str, set[Any]] = {}
    unique_rules = [r for r in rules if r.rule_type == "unique"]
    for ur in unique_rules:
        unique_tracker[ur.field] = set()

    for idx, row in enumerate(rows):
        row_errors = validate_row(row, [r for r in rules if r.rule_type != "unique"], row_index=idx)

        for ur in unique_rules:
            val = row.get(ur.field)
            if val is not None:
                if val in unique_tracker[ur.field]:
                    row_errors.append(
                        ValidationError(
                            row_index=idx,
                            field=ur.field,
                            rule_type="unique",
                            message=f"Duplicate value '{val}' for field '{ur.field}'",
                        )
                    )
                else:
                    unique_tracker[ur.field].add(val)

        if row_errors:
            failed_indices.add(idx)
        all_errors.extend(row_errors)

    by_rule: dict[str, int] = {}
    for e in all_errors:
        by_rule[e.rule_type] = by_rule.get(e.rule_type, 0) + 1

    return {
        "total_rows": len(rows),
        "passed": len(rows) - len(failed_indices),
        "failed": len(failed_indices),
        "errors": all_errors,
        "by_rule": by_rule,
    }


def _check_rule(value: Any, rule: ValidationRule, row_index: int) -> ValidationError | None:
    """Check a single value against a single rule."""
    if rule.rule_type == "required":
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return ValidationError(row_index, rule.field, "required", f"Field '{rule.field}' is required")

    elif rule.rule_type == "min_length":
        min_len = rule.params.get("min", 0)
        if value is not None and len(str(value)) < min_len:
            return ValidationError(row_index, rule.field, "min_length", f"Field '{rule.field}' must be at least {min_len} chars")

    elif rule.rule_type == "max_length":
        max_len = rule.params.get("max", 255)
        if value is not None and len(str(value)) > max_len:
            return ValidationError(row_index, rule.field, "max_length", f"Field '{rule.field}' must be at most {max_len} chars")

    elif rule.rule_type == "regex":
        pattern = rule.params.get("pattern", "")
        if value is not None and not re.match(pattern, str(value)):
            return ValidationError(row_index, rule.field, "regex", f"Field '{rule.field}' does not match pattern '{pattern}'")

    elif rule.rule_type == "range":
        min_val = rule.params.get("min")
        max_val = rule.params.get("max")
        if value is not None:
            try:
                num = float(value)
                if min_val is not None and num < min_val:
                    return ValidationError(row_index, rule.field, "range", f"Field '{rule.field}' below minimum {min_val}")
                if max_val is not None and num > max_val:
                    return ValidationError(row_index, rule.field, "range", f"Field '{rule.field}' above maximum {max_val}")
            except (ValueError, TypeError):
                return ValidationError(row_index, rule.field, "range", f"Field '{rule.field}' is not numeric")

    elif rule.rule_type == "enum":
        allowed = rule.params.get("values", [])
        if value is not None and value not in allowed:
            return ValidationError(row_index, rule.field, "enum", f"Field '{rule.field}' must be one of {allowed}")

    return None
