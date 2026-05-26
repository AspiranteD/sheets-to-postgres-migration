"""Column mapping from Google Sheets headers to PostgreSQL column names."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ColumnMapper:
    """Map, rename, split, merge, and coerce columns from sheet to DB schema."""

    def __init__(self, mappings: list[dict[str, Any]]) -> None:
        self._mappings = mappings
        self._simple: dict[str, dict[str, Any]] = {}
        self._splits: list[dict[str, Any]] = []
        self._merges: list[dict[str, Any]] = []

        for m in mappings:
            op = m.get("operation", "rename")
            if op == "split":
                self._splits.append(m)
            elif op == "merge":
                self._merges.append(m)
            else:
                self._simple[m["source"]] = m

    @classmethod
    def from_json(cls, path: str | Path) -> "ColumnMapper":
        """Load mappings from a JSON config file."""
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return cls(data.get("mappings", data))

    def map_row(self, sheet_row: dict[str, Any]) -> dict[str, Any]:
        """Transform a single sheet row dict into a DB row dict."""
        result: dict[str, Any] = {}

        for source, mapping in self._simple.items():
            value = sheet_row.get(source)
            target = mapping.get("target", source)
            db_type = mapping.get("db_type")
            result[target] = _coerce(value, db_type)

        for split in self._splits:
            source = split["source"]
            value = sheet_row.get(source, "")
            separator = split.get("separator", " ")
            targets = split.get("targets", [])
            parts = str(value).split(separator, maxsplit=len(targets) - 1) if value else []
            for i, target in enumerate(targets):
                result[target] = parts[i].strip() if i < len(parts) else None

        for merge in self._merges:
            sources = merge.get("sources", [])
            target = merge.get("target", "")
            separator = merge.get("separator", " ")
            values = [str(sheet_row.get(s, "")) for s in sources if sheet_row.get(s)]
            result[target] = separator.join(values) if values else None

        return result

    @property
    def target_columns(self) -> list[str]:
        """Return the list of all target DB column names."""
        cols: list[str] = []
        for m in self._simple.values():
            cols.append(m.get("target", m["source"]))
        for s in self._splits:
            cols.extend(s.get("targets", []))
        for mg in self._merges:
            cols.append(mg.get("target", ""))
        return cols


def _coerce(value: Any, db_type: str | None) -> Any:
    """Coerce a value to the target DB type."""
    if value is None or db_type is None:
        return value
    db_type = db_type.lower()
    try:
        if db_type in ("integer", "int", "bigint"):
            return int(float(value))
        if db_type in ("float", "double", "numeric", "decimal", "real"):
            return float(value)
        if db_type in ("boolean", "bool"):
            return str(value).lower() in ("true", "1", "yes", "sí", "si")
        if db_type in ("text", "varchar", "char"):
            return str(value)
    except (ValueError, TypeError):
        return None
    return value
