"""
Markdown report generation for each migration phase.

Generates structured reports for:
- Phase 1: Extraction & analysis (sheet structure, detected problems)
- Phase 2: Validation (valid/transformed/critical/skipped per table)
- Phase 3: Migration (inserted/skipped/errors per table, dry-run support)
"""
from datetime import datetime
from typing import Any


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def generate_analysis_report(
    sheets_info: dict[str, dict],
    problems: dict[str, list],
    stats: dict[str, Any],
) -> str:
    """
    Generate Phase 1 report (extraction and analysis).

    sheets_info: per-tab info (columns, rows, types, samples)
    problems: detected problems by category
    stats: general statistics
    """
    lines = [
        "# Analysis Report - Google Sheets Migration",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    total_rows = sum(info.get("row_count", 0) for info in sheets_info.values())
    lines.append("## General Summary")
    lines.append("")
    lines.append(f"- **Tabs analyzed:** {len(sheets_info)}")
    lines.append(f"- **Total rows:** {total_rows}")
    lines.append("")

    for sheet_key, info in sheets_info.items():
        lines.append(f"### Tab: {info.get('name', sheet_key)}")
        lines.append(f"- Rows: {info.get('row_count', 0)}")
        lines.append(f"- Columns: {info.get('col_count', 0)}")
        lines.append("")

        columns = info.get("columns", [])
        if columns:
            lines.append("| Column | Type | Nulls | Sample |")
            lines.append("|--------|------|-------|--------|")
            for col in columns:
                lines.append(
                    f"| {col['name']} | {col.get('dtype', '?')} | "
                    f"{col.get('null_count', 0)} ({col.get('null_pct', 0):.0f}%) | "
                    f"{col.get('sample', '')} |"
                )
            lines.append("")

    lines.append("## Detected Problems")
    lines.append("")
    total_problems = sum(len(v) for v in problems.values())
    if total_problems == 0:
        lines.append("No problems detected.")
    else:
        lines.append(f"**Total problems:** {total_problems}")
        lines.append("")
        for category, items in problems.items():
            if items:
                lines.append(f"### {category} ({len(items)})")
                lines.append("")
                for item in items[:50]:
                    lines.append(f"- {item}")
                if len(items) > 50:
                    lines.append(f"- ... and {len(items) - 50} more")
                lines.append("")

    lines.append("## Statistics")
    lines.append("")
    for key, value in stats.items():
        if isinstance(value, dict):
            lines.append(f"### {key}")
            for k, v in value.items():
                lines.append(f"- {k}: {v}")
            lines.append("")
        else:
            lines.append(f"- **{key}:** {value}")

    return "\n".join(lines)


def generate_validation_report(results: dict[str, dict]) -> str:
    """
    Generate Phase 2 report (validation).

    results: per table -> {valid, transformed, critical, skipped, errors}
    """
    lines = [
        "# Validation Report - Google Sheets Migration",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary by Table",
        "",
        "| Table | Valid | Transformed | Critical | Skipped | Total |",
        "|-------|-------|-------------|----------|---------|-------|",
    ]

    for table, data in results.items():
        v = data.get("valid", 0)
        t = data.get("transformed", 0)
        c = data.get("critical", 0)
        s = data.get("skipped", 0)
        total = v + t + c + s
        lines.append(f"| {table} | {v} | {t} | {c} | {s} | {total} |")

    lines.append("")

    for table, data in results.items():
        errors = data.get("errors", [])
        if errors:
            lines.append(f"## Errors: {table} ({len(errors)})")
            lines.append("")
            for err in errors[:100]:
                row_num = err.get("row", "?")
                lpn = err.get("lpn", "?")
                msgs = err.get("messages", [])
                lines.append(f"### Row {row_num} (LPN: {lpn})")
                for msg in msgs:
                    lines.append(f"- {msg}")
                lines.append("")
            if len(errors) > 100:
                lines.append(f"... and {len(errors) - 100} more errors")
            lines.append("")

    return "\n".join(lines)


def generate_migration_report(
    results: dict[str, dict],
    dry_run: bool,
    target: str,
) -> str:
    """
    Generate Phase 3 report (migration).

    results: per table -> {total_source, inserted, skipped, errors, error_details}
    """
    mode = "DRY-RUN (simulation)" if dry_run else "LIVE EXECUTION"

    lines = [
        f"# Migration Report - {mode}",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Target:** {target.upper()}",
        f"**Mode:** {mode}",
        "",
        "## Results by Table",
        "",
        "| Table | Source | Inserted | Skipped | Errors |",
        "|-------|--------|----------|---------|--------|",
    ]

    for table, data in results.items():
        src = data.get("total_source", 0)
        ins = data.get("inserted", 0)
        skip = data.get("skipped", 0)
        errs = data.get("errors", 0)
        lines.append(f"| {table} | {src} | {ins} | {skip} | {errs} |")

    lines.append("")

    for table, data in results.items():
        error_details = data.get("error_details", [])
        if error_details:
            lines.append(f"## Errors: {table}")
            for err in error_details[:50]:
                lines.append(f"- {err}")
            lines.append("")

    return "\n".join(lines)
