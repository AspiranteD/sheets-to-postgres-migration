"""Tests for src.pipeline.orchestrator."""

import json
import pytest
from unittest.mock import MagicMock, patch
from src.pipeline.orchestrator import MigrationPipeline, PipelineConfig, Phase, PhaseResult


def _make_config(tmp_path, dry_run=False, rules=None, conflict_columns=None):
    mappings_file = tmp_path / "mappings.json"
    mappings_file.write_text(json.dumps({
        "mappings": [
            {"source": "name", "target": "name", "operation": "rename", "db_type": "text"},
            {"source": "price", "target": "price", "operation": "rename", "db_type": "numeric"},
        ]
    }), encoding="utf-8")

    return PipelineConfig(
        spreadsheet_id="test-id",
        sheet_name="Sheet1",
        table_name="products",
        column_mappings_path=str(mappings_file),
        validation_rules=rules or [],
        column_types={"name": "string", "price": "price"},
        conflict_columns=conflict_columns or [],
        dry_run=dry_run,
        pg_dsn="postgresql://test:test@localhost/test",
    )


class TestMigrationPipeline:
    def test_full_run(self, tmp_path):
        mock_reader = MagicMock()
        mock_reader.read_sheet.return_value = [
            {"name": "Widget", "price": "29.99"},
            {"name": "Gadget", "price": "49.99"},
        ]
        mock_loader = MagicMock()
        mock_loader.load_batch.return_value = 2

        config = _make_config(tmp_path)
        pipeline = MigrationPipeline(reader=mock_reader, loader=mock_loader)
        results = pipeline.run(config)

        assert len(results) == 5
        assert all(r.success for r in results)

    def test_dry_run_skips_load(self, tmp_path):
        mock_reader = MagicMock()
        mock_reader.read_sheet.return_value = [{"name": "A", "price": "10"}]
        mock_loader = MagicMock()

        config = _make_config(tmp_path, dry_run=True)
        pipeline = MigrationPipeline(reader=mock_reader, loader=mock_loader)
        results = pipeline.run(config)

        load_result = [r for r in results if r.phase == Phase.LOAD][0]
        assert load_result.details.get("skipped") is True
        mock_loader.load_batch.assert_not_called()

    def test_validation_failure_stops_pipeline(self, tmp_path):
        from src.transform.validators import ValidationRule

        mock_reader = MagicMock()
        mock_reader.read_sheet.return_value = [
            {"name": None, "price": "10"},
            {"name": None, "price": "20"},
        ]

        rules = [ValidationRule(field="name", rule_type="required")]
        config = _make_config(tmp_path, rules=rules)
        config.fail_threshold = 0.0

        pipeline = MigrationPipeline(reader=mock_reader)
        results = pipeline.run(config)

        validate_result = [r for r in results if r.phase == Phase.VALIDATE][0]
        assert not validate_result.success
        assert len(results) == 3  # stops after VALIDATE

    def test_resume_from_phase(self, tmp_path):
        mock_reader = MagicMock()
        mock_reader.read_sheet.return_value = [{"name": "A", "price": "10"}]
        mock_loader = MagicMock()
        mock_loader.load_batch.return_value = 1

        config = _make_config(tmp_path)
        pipeline = MigrationPipeline(reader=mock_reader, loader=mock_loader)
        pipeline._raw_data = [{"name": "A", "price": "10"}]
        pipeline._cleaned_data = [{"name": "A", "price": 10.0}]

        results = pipeline.run(config, resume_from=Phase.LOAD)
        phases = [r.phase for r in results]
        assert Phase.EXTRACT not in phases
        assert Phase.LOAD in phases

    def test_upsert_mode(self, tmp_path):
        mock_reader = MagicMock()
        mock_reader.read_sheet.return_value = [{"name": "A", "price": "10"}]
        mock_loader = MagicMock()
        mock_loader.load_with_upsert.return_value = {"inserted": 1, "updated": 0}

        config = _make_config(tmp_path, conflict_columns=["name"])
        pipeline = MigrationPipeline(reader=mock_reader, loader=mock_loader)
        results = pipeline.run(config)

        load_result = [r for r in results if r.phase == Phase.LOAD][0]
        assert load_result.success
        mock_loader.load_with_upsert.assert_called_once()

    def test_progress_callback(self, tmp_path):
        mock_reader = MagicMock()
        mock_reader.read_sheet.return_value = [{"name": "A", "price": "10"}]
        mock_loader = MagicMock()
        mock_loader.load_batch.return_value = 1

        callback = MagicMock()
        config = _make_config(tmp_path)
        pipeline = MigrationPipeline(reader=mock_reader, loader=mock_loader, progress_callback=callback)
        pipeline.run(config)

        assert callback.call_count > 0

    def test_extract_error_stops_pipeline(self, tmp_path):
        mock_reader = MagicMock()
        mock_reader.read_sheet.side_effect = Exception("API Error")

        config = _make_config(tmp_path)
        pipeline = MigrationPipeline(reader=mock_reader)
        results = pipeline.run(config)

        assert len(results) == 1
        assert not results[0].success
        assert "API Error" in results[0].details["error"]

    def test_results_property(self, tmp_path):
        pipeline = MigrationPipeline()
        assert pipeline.results == []
