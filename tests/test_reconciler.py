"""Tests for src.reconcile.reconciler."""

import pytest
from src.reconcile.reconciler import (
    ReconcileResult,
    reconcile_counts,
    reconcile_checksums,
    reconcile_totals,
    generate_report,
)


class TestReconcileCounts:
    def test_matching_counts(self):
        rows = [{"id": 1}, {"id": 2}, {"id": 3}]
        result = reconcile_counts(rows, 3)
        assert result.source_count == 3
        assert result.target_count == 3
        assert result.is_ok

    def test_mismatched_counts(self):
        rows = [{"id": 1}, {"id": 2}]
        result = reconcile_counts(rows, 3)
        assert result.source_count == 2
        assert result.target_count == 3
        assert not result.is_ok


class TestReconcileChecksums:
    def test_identical_data(self):
        source = [{"id": "A", "val": 1}, {"id": "B", "val": 2}]
        target = [{"id": "A", "val": 1}, {"id": "B", "val": 2}]
        result = reconcile_checksums(source, target, "id")
        assert result.is_ok
        assert len(result.missing) == 0
        assert len(result.extra) == 0

    def test_missing_in_target(self):
        source = [{"id": "A", "val": 1}, {"id": "B", "val": 2}]
        target = [{"id": "A", "val": 1}]
        result = reconcile_checksums(source, target, "id")
        assert not result.is_ok
        assert "B" in result.missing

    def test_extra_in_target(self):
        source = [{"id": "A", "val": 1}]
        target = [{"id": "A", "val": 1}, {"id": "C", "val": 3}]
        result = reconcile_checksums(source, target, "id")
        assert "C" in result.extra

    def test_mismatched_values(self):
        source = [{"id": "A", "val": 1}]
        target = [{"id": "A", "val": 999}]
        result = reconcile_checksums(source, target, "id")
        assert len(result.mismatched) == 1
        assert result.mismatched[0]["key"] == "A"


class TestReconcileTotals:
    def test_matching_sums(self):
        source = [{"price": 10.0}, {"price": 20.0}]
        target = [{"price": 10.0}, {"price": 20.0}]
        result = reconcile_totals(source, target, ["price"])
        assert result.is_ok

    def test_mismatched_sums(self):
        source = [{"price": 10.0}, {"price": 20.0}]
        target = [{"price": 10.0}, {"price": 25.0}]
        result = reconcile_totals(source, target, ["price"])
        assert not result.is_ok
        assert len(result.mismatched) == 1
        assert result.mismatched[0]["column"] == "price"

    def test_multiple_columns(self):
        source = [{"a": 100, "b": 200}]
        target = [{"a": 100, "b": 200}]
        result = reconcile_totals(source, target, ["a", "b"])
        assert result.is_ok


class TestReconcileResult:
    def test_is_ok_true(self):
        r = ReconcileResult(source_count=5, target_count=5)
        assert r.is_ok

    def test_is_ok_false_counts(self):
        r = ReconcileResult(source_count=5, target_count=4)
        assert not r.is_ok

    def test_is_ok_false_missing(self):
        r = ReconcileResult(source_count=5, target_count=5, missing=["X"])
        assert not r.is_ok


class TestGenerateReport:
    def test_ok_report(self):
        r = ReconcileResult(source_count=100, target_count=100)
        report = generate_report(r)
        assert "OK" in report
        assert "100" in report

    def test_discrepancy_report(self):
        r = ReconcileResult(source_count=100, target_count=95, missing=["a", "b"])
        report = generate_report(r)
        assert "DISCREPANCIES" in report
        assert "Missing" in report
