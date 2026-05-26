"""Five-phase migration pipeline orchestrator."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from src.extract.sheets_reader import SheetsReader
from src.transform.cleaners import clean_row
from src.transform.validators import ValidationRule, validate_batch
from src.transform.mappers import ColumnMapper
from src.load.pg_loader import PgLoader
from src.reconcile.reconciler import reconcile_counts, reconcile_checksums


class Phase(Enum):
    EXTRACT = "extract"
    CLEAN = "clean"
    VALIDATE = "validate"
    LOAD = "load"
    RECONCILE = "reconcile"


@dataclass
class PhaseResult:
    phase: Phase
    success: bool
    duration_secs: float
    row_count: int = 0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineConfig:
    spreadsheet_id: str = ""
    sheet_name: str = ""
    credentials_file: str = "credentials.json"
    table_name: str = ""
    column_mappings_path: str = "config/column_mappings.json"
    validation_rules: list[ValidationRule] = field(default_factory=list)
    column_types: dict[str, str] = field(default_factory=dict)
    conflict_columns: list[str] = field(default_factory=list)
    dry_run: bool = False
    fail_threshold: float = 0.05
    pg_dsn: str = ""


class MigrationPipeline:
    """Orchestrates the 5-phase ETL: Extract → Clean → Validate → Load → Reconcile."""

    PHASE_ORDER = [Phase.EXTRACT, Phase.CLEAN, Phase.VALIDATE, Phase.LOAD, Phase.RECONCILE]

    def __init__(
        self,
        reader: SheetsReader | None = None,
        loader: PgLoader | None = None,
        progress_callback: Callable[[Phase, str], None] | None = None,
    ) -> None:
        self._reader = reader
        self._loader = loader
        self._progress = progress_callback
        self._results: list[PhaseResult] = []
        self._raw_data: list[dict[str, Any]] = []
        self._cleaned_data: list[dict[str, Any]] = []
        self._mapped_data: list[dict[str, Any]] = []

    @property
    def results(self) -> list[PhaseResult]:
        return list(self._results)

    def run(self, config: PipelineConfig, resume_from: Phase | None = None) -> list[PhaseResult]:
        """Execute the full pipeline, optionally resuming from a specific phase."""
        self._results = []
        phases = self.PHASE_ORDER

        if resume_from:
            start_idx = phases.index(resume_from)
            phases = phases[start_idx:]

        for phase in phases:
            if config.dry_run and phase == Phase.LOAD:
                self._report(phase, "Skipped (dry-run mode)")
                self._results.append(PhaseResult(phase=phase, success=True, duration_secs=0.0, details={"skipped": True}))
                continue

            start = time.time()
            try:
                result = self._run_phase(phase, config)
                result.duration_secs = round(time.time() - start, 3)
                self._results.append(result)

                if not result.success:
                    self._report(phase, f"Failed: {result.details}")
                    break
            except Exception as exc:
                elapsed = round(time.time() - start, 3)
                self._results.append(PhaseResult(phase=phase, success=False, duration_secs=elapsed, details={"error": str(exc)}))
                self._report(phase, f"Error: {exc}")
                break

        return self._results

    def _run_phase(self, phase: Phase, config: PipelineConfig) -> PhaseResult:
        if phase == Phase.EXTRACT:
            return self._extract(config)
        if phase == Phase.CLEAN:
            return self._clean(config)
        if phase == Phase.VALIDATE:
            return self._validate(config)
        if phase == Phase.LOAD:
            return self._load(config)
        if phase == Phase.RECONCILE:
            return self._reconcile(config)
        raise ValueError(f"Unknown phase: {phase}")

    def _extract(self, config: PipelineConfig) -> PhaseResult:
        self._report(Phase.EXTRACT, "Reading from Google Sheets…")
        reader = self._reader or SheetsReader(
            credentials_file=config.credentials_file,
            spreadsheet_id=config.spreadsheet_id,
        )
        self._raw_data = reader.read_sheet(config.sheet_name)
        return PhaseResult(phase=Phase.EXTRACT, success=True, duration_secs=0, row_count=len(self._raw_data))

    def _clean(self, config: PipelineConfig) -> PhaseResult:
        self._report(Phase.CLEAN, "Cleaning data…")
        self._cleaned_data = [clean_row(row, config.column_types) for row in self._raw_data]
        return PhaseResult(phase=Phase.CLEAN, success=True, duration_secs=0, row_count=len(self._cleaned_data))

    def _validate(self, config: PipelineConfig) -> PhaseResult:
        self._report(Phase.VALIDATE, "Validating data…")
        summary = validate_batch(self._cleaned_data, config.validation_rules)
        fail_rate = summary["failed"] / max(summary["total_rows"], 1)
        success = fail_rate <= config.fail_threshold
        return PhaseResult(
            phase=Phase.VALIDATE,
            success=success,
            duration_secs=0,
            row_count=summary["total_rows"],
            details={"passed": summary["passed"], "failed": summary["failed"], "fail_rate": round(fail_rate, 4)},
        )

    def _load(self, config: PipelineConfig) -> PhaseResult:
        self._report(Phase.LOAD, "Loading into PostgreSQL…")
        mapper = ColumnMapper.from_json(config.column_mappings_path)
        self._mapped_data = [mapper.map_row(row) for row in self._cleaned_data]

        loader = self._loader or PgLoader(dsn=config.pg_dsn)
        if config.conflict_columns:
            counts = loader.load_with_upsert(config.table_name, self._mapped_data, config.conflict_columns)
            return PhaseResult(phase=Phase.LOAD, success=True, duration_secs=0, row_count=counts["inserted"] + counts["updated"], details=counts)
        else:
            inserted = loader.load_batch(config.table_name, self._mapped_data)
            return PhaseResult(phase=Phase.LOAD, success=True, duration_secs=0, row_count=inserted)

    def _reconcile(self, config: PipelineConfig) -> PhaseResult:
        self._report(Phase.RECONCILE, "Reconciling…")
        target_count = len(self._mapped_data) if self._mapped_data else len(self._cleaned_data)
        result = reconcile_counts(self._raw_data, target_count)
        return PhaseResult(
            phase=Phase.RECONCILE,
            success=result.is_ok,
            duration_secs=0,
            row_count=result.source_count,
            details={"source": result.source_count, "target": result.target_count},
        )

    def _report(self, phase: Phase, message: str) -> None:
        if self._progress:
            self._progress(phase, message)
