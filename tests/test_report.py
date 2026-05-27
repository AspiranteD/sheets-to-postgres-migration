"""Tests for markdown report generation."""
import pytest
from src.report.markdown_report import (
    generate_analysis_report,
    generate_validation_report,
    generate_migration_report,
)


class TestAnalysisReport:
    def test_basic(self):
        sheets = {
            "inventario": {
                "name": "Inventario", "row_count": 100, "col_count": 20,
                "columns": [
                    {"name": "ID", "dtype": "str", "null_count": 0,
                     "null_pct": 0, "sample": "LPN001"},
                ],
            },
        }
        problems = {"Duplicados": ["LPN duplicado: X"]}
        stats = {"total_items": 100}

        report = generate_analysis_report(sheets, problems, stats)
        assert "Analysis Report" in report
        assert "Inventario" in report
        assert "100" in report
        assert "LPN duplicado: X" in report
        assert "total_items" in report

    def test_no_problems(self):
        report = generate_analysis_report(
            {"inv": {"name": "Inv", "row_count": 0, "col_count": 0}},
            {}, {},
        )
        assert "No problems detected" in report

    def test_truncated_problems(self):
        problems = {"Warnings": [f"Warning {i}" for i in range(60)]}
        report = generate_analysis_report({}, problems, {})
        assert "and 10 more" in report

    def test_nested_stats(self):
        stats = {"counts": {"items": 100, "sold": 30}}
        report = generate_analysis_report({}, {}, stats)
        assert "items: 100" in report
        assert "sold: 30" in report


class TestValidationReport:
    def test_basic(self):
        results = {
            "physical_item": {
                "valid": 90, "transformed": 5, "critical": 3, "skipped": 2,
                "errors": [],
            },
        }
        report = generate_validation_report(results)
        assert "Validation Report" in report
        assert "physical_item" in report
        assert "90" in report
        assert "5" in report
        assert "3" in report

    def test_with_errors(self):
        results = {
            "sale": {
                "valid": 10, "transformed": 0, "critical": 2, "skipped": 0,
                "errors": [
                    {"row": 5, "lpn": "LPN001",
                     "messages": ["final_price missing"]},
                ],
            },
        }
        report = generate_validation_report(results)
        assert "Row 5" in report
        assert "LPN001" in report
        assert "final_price missing" in report

    def test_truncated_errors(self):
        errors = [
            {"row": i, "lpn": f"LPN{i}", "messages": ["error"]}
            for i in range(110)
        ]
        results = {"table": {"valid": 0, "transformed": 0, "critical": 110,
                              "skipped": 0, "errors": errors}}
        report = generate_validation_report(results)
        assert "and 10 more" in report

    def test_multiple_tables(self):
        results = {
            "physical_item": {"valid": 100, "transformed": 0, "critical": 0,
                               "skipped": 0, "errors": []},
            "sale": {"valid": 50, "transformed": 0, "critical": 0,
                      "skipped": 0, "errors": []},
        }
        report = generate_validation_report(results)
        assert "physical_item" in report
        assert "sale" in report


class TestMigrationReport:
    def test_dryrun(self):
        results = {
            "physical_item": {
                "total_source": 100, "inserted": 95,
                "skipped": 3, "errors": 2,
            },
        }
        report = generate_migration_report(results, dry_run=True, target="dev")
        assert "DRY-RUN" in report
        assert "DEV" in report
        assert "95" in report

    def test_live(self):
        results = {
            "physical_item": {
                "total_source": 100, "inserted": 100,
                "skipped": 0, "errors": 0,
            },
        }
        report = generate_migration_report(results, dry_run=False, target="prod")
        assert "LIVE EXECUTION" in report
        assert "PROD" in report

    def test_with_error_details(self):
        results = {
            "sale": {
                "total_source": 50, "inserted": 48,
                "skipped": 0, "errors": 2,
                "error_details": ["FK violation on LPN001", "Duplicate sale"],
            },
        }
        report = generate_migration_report(results, dry_run=False, target="dev")
        assert "FK violation" in report
        assert "Duplicate sale" in report

    def test_empty_results(self):
        report = generate_migration_report({}, dry_run=True, target="dev")
        assert "Migration Report" in report
