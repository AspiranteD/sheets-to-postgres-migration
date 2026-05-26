"""Post-migration reconciliation: counts, checksums, and totals."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReconcileResult:
    """Outcome of a reconciliation check."""

    source_count: int = 0
    target_count: int = 0
    missing: list[Any] = field(default_factory=list)
    extra: list[Any] = field(default_factory=list)
    mismatched: list[dict[str, Any]] = field(default_factory=list)

    @property
    def is_ok(self) -> bool:
        return (
            self.source_count == self.target_count
            and not self.missing
            and not self.extra
            and not self.mismatched
        )


def reconcile_counts(source_rows: list[dict], target_count: int) -> ReconcileResult:
    """Basic count comparison between source and target."""
    return ReconcileResult(
        source_count=len(source_rows),
        target_count=target_count,
    )


def reconcile_checksums(
    source_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    key_column: str,
) -> ReconcileResult:
    """Row-level comparison using content hashes keyed by a unique column."""
    source_map: dict[Any, str] = {}
    for row in source_rows:
        key = row.get(key_column)
        source_map[key] = _row_hash(row)

    target_map: dict[Any, str] = {}
    for row in target_rows:
        key = row.get(key_column)
        target_map[key] = _row_hash(row)

    source_keys = set(source_map.keys())
    target_keys = set(target_map.keys())

    missing = sorted(source_keys - target_keys, key=str)
    extra = sorted(target_keys - source_keys, key=str)

    mismatched: list[dict[str, Any]] = []
    for key in source_keys & target_keys:
        if source_map[key] != target_map[key]:
            mismatched.append({"key": key, "source_hash": source_map[key], "target_hash": target_map[key]})

    return ReconcileResult(
        source_count=len(source_rows),
        target_count=len(target_rows),
        missing=missing,
        extra=extra,
        mismatched=mismatched,
    )


def reconcile_totals(
    source_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    numeric_columns: list[str],
) -> ReconcileResult:
    """Compare sums of numeric columns between source and target."""
    mismatched: list[dict[str, Any]] = []

    for col in numeric_columns:
        source_sum = _safe_sum(source_rows, col)
        target_sum = _safe_sum(target_rows, col)
        if abs(source_sum - target_sum) > 0.01:
            mismatched.append({
                "column": col,
                "source_sum": source_sum,
                "target_sum": target_sum,
                "difference": round(source_sum - target_sum, 2),
            })

    return ReconcileResult(
        source_count=len(source_rows),
        target_count=len(target_rows),
        mismatched=mismatched,
    )


def generate_report(result: ReconcileResult) -> str:
    """Human-readable reconciliation report."""
    lines = [
        "=== Reconciliation Report ===",
        f"Source count: {result.source_count}",
        f"Target count: {result.target_count}",
        f"Status: {'OK' if result.is_ok else 'DISCREPANCIES FOUND'}",
    ]
    if result.missing:
        lines.append(f"Missing in target ({len(result.missing)}): {result.missing[:10]}")
    if result.extra:
        lines.append(f"Extra in target ({len(result.extra)}): {result.extra[:10]}")
    if result.mismatched:
        lines.append(f"Mismatched rows ({len(result.mismatched)}):")
        for m in result.mismatched[:10]:
            lines.append(f"  {m}")
    return "\n".join(lines)


def _row_hash(row: dict[str, Any]) -> str:
    serialized = json.dumps(row, sort_keys=True, default=str)
    return hashlib.md5(serialized.encode()).hexdigest()


def _safe_sum(rows: list[dict[str, Any]], column: str) -> float:
    total = 0.0
    for row in rows:
        val = row.get(column)
        if val is not None:
            try:
                total += float(val)
            except (ValueError, TypeError):
                pass
    return round(total, 2)
