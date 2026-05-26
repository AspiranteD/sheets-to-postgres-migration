"""Tests for src.transform.mappers."""

import json
import pytest
from unittest.mock import patch, mock_open
from src.transform.mappers import ColumnMapper


SAMPLE_MAPPINGS = [
    {"source": "Nombre", "target": "name", "operation": "rename", "db_type": "text"},
    {"source": "Precio", "target": "price", "operation": "rename", "db_type": "numeric"},
    {"source": "Activo", "target": "is_active", "operation": "rename", "db_type": "boolean"},
    {"source": "Cantidad", "target": "quantity", "operation": "rename", "db_type": "integer"},
]


class TestColumnMapper:
    def test_simple_rename(self):
        mapper = ColumnMapper(SAMPLE_MAPPINGS)
        row = {"Nombre": "Widget", "Precio": "29.99", "Activo": "true", "Cantidad": "5"}
        result = mapper.map_row(row)
        assert result["name"] == "Widget"
        assert result["price"] == 29.99
        assert result["is_active"] is True
        assert result["quantity"] == 5

    def test_split_operation(self):
        mappings = [
            {"source": "full_name", "operation": "split", "separator": " ", "targets": ["first_name", "last_name"]},
        ]
        mapper = ColumnMapper(mappings)
        result = mapper.map_row({"full_name": "John Doe"})
        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"

    def test_merge_operation(self):
        mappings = [
            {"sources": ["street", "city", "country"], "operation": "merge", "target": "address", "separator": ", "},
        ]
        mapper = ColumnMapper(mappings)
        result = mapper.map_row({"street": "Main St", "city": "Madrid", "country": "Spain"})
        assert result["address"] == "Main St, Madrid, Spain"

    def test_missing_source_column(self):
        mapper = ColumnMapper(SAMPLE_MAPPINGS)
        result = mapper.map_row({"Nombre": "Widget"})
        assert result["name"] == "Widget"
        assert result["price"] is None

    def test_type_coercion_integer(self):
        mappings = [{"source": "count", "target": "count", "operation": "rename", "db_type": "integer"}]
        mapper = ColumnMapper(mappings)
        result = mapper.map_row({"count": "42.7"})
        assert result["count"] == 42

    def test_type_coercion_invalid(self):
        mappings = [{"source": "count", "target": "count", "operation": "rename", "db_type": "integer"}]
        mapper = ColumnMapper(mappings)
        result = mapper.map_row({"count": "abc"})
        assert result["count"] is None

    def test_target_columns(self):
        mapper = ColumnMapper(SAMPLE_MAPPINGS)
        cols = mapper.target_columns
        assert "name" in cols
        assert "price" in cols

    def test_from_json(self, tmp_path):
        config = {"mappings": SAMPLE_MAPPINGS}
        config_file = tmp_path / "mappings.json"
        config_file.write_text(json.dumps(config), encoding="utf-8")
        mapper = ColumnMapper.from_json(str(config_file))
        result = mapper.map_row({"Nombre": "Test", "Precio": "10", "Activo": "false", "Cantidad": "1"})
        assert result["name"] == "Test"

    def test_split_missing_value(self):
        mappings = [
            {"source": "full_name", "operation": "split", "separator": " ", "targets": ["first", "last"]},
        ]
        mapper = ColumnMapper(mappings)
        result = mapper.map_row({"full_name": ""})
        assert result["first"] is None

    def test_merge_partial_values(self):
        mappings = [
            {"sources": ["a", "b", "c"], "operation": "merge", "target": "combined", "separator": "-"},
        ]
        mapper = ColumnMapper(mappings)
        result = mapper.map_row({"a": "X", "b": None, "c": "Z"})
        assert result["combined"] == "X-Z"
