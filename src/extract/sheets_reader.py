"""Google Sheets API v4 reader with pagination and rate limiting."""

from __future__ import annotations

import os
import time
from typing import Any, Callable

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


_DEFAULT_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
_MAX_ROWS_PER_REQUEST = 1000
_RATE_LIMIT_REQUESTS = 100
_RATE_LIMIT_WINDOW_SECS = 100


class SheetsReader:
    """Read data from Google Sheets with automatic pagination and rate limiting."""

    def __init__(
        self,
        credentials_file: str | None = None,
        spreadsheet_id: str | None = None,
        scopes: list[str] | None = None,
        page_size: int = _MAX_ROWS_PER_REQUEST,
    ) -> None:
        self.credentials_file = credentials_file or os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
        self.spreadsheet_id = spreadsheet_id or os.getenv("SPREADSHEET_ID", "")
        self.scopes = scopes or _DEFAULT_SCOPES
        self.page_size = page_size

        self._request_timestamps: list[float] = []
        self._service: Any | None = None

    def _get_service(self) -> Any:
        if self._service is None:
            creds = Credentials.from_service_account_file(self.credentials_file, scopes=self.scopes)
            self._service = build("sheets", "v4", credentials=creds)
        return self._service

    def _set_service(self, service: Any) -> None:
        """Inject a pre-built service (useful for testing)."""
        self._service = service

    def _rate_limit(self) -> None:
        """Block until the request can proceed within the quota window."""
        now = time.time()
        self._request_timestamps = [t for t in self._request_timestamps if now - t < _RATE_LIMIT_WINDOW_SECS]
        if len(self._request_timestamps) >= _RATE_LIMIT_REQUESTS:
            sleep_for = _RATE_LIMIT_WINDOW_SECS - (now - self._request_timestamps[0])
            if sleep_for > 0:
                time.sleep(sleep_for)
        self._request_timestamps.append(time.time())

    def _fetch_range(self, range_notation: str) -> list[list[str]]:
        """Fetch a single range from the spreadsheet."""
        self._rate_limit()
        service = self._get_service()
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=self.spreadsheet_id, range=range_notation)
            .execute()
        )
        return result.get("values", [])

    def read_sheet(
        self,
        sheet_name: str,
        has_header: bool = True,
        progress_callback: Callable[[int], None] | None = None,
    ) -> list[dict[str, str]]:
        """Read an entire sheet, paginating automatically for large datasets.

        Returns a list of dicts keyed by header values (or ``col_0 .. col_N``
        when *has_header* is ``False``).
        """
        all_rows: list[list[str]] = []
        offset = 1
        while True:
            end = offset + self.page_size - 1
            range_notation = f"{sheet_name}!A{offset}:{_col_letter(100)}{end}"
            chunk = self._fetch_range(range_notation)
            if not chunk:
                break
            all_rows.extend(chunk)
            if progress_callback:
                progress_callback(len(all_rows))
            if len(chunk) < self.page_size:
                break
            offset += self.page_size

        if not all_rows:
            return []

        if has_header:
            headers = all_rows[0]
            data_rows = all_rows[1:]
        else:
            max_cols = max(len(r) for r in all_rows)
            headers = [f"col_{i}" for i in range(max_cols)]
            data_rows = all_rows

        return [_row_to_dict(headers, row) for row in data_rows]

    def read_range(self, range_notation: str, has_header: bool = True) -> list[dict[str, str]]:
        """Read a specific A1-notation range and return list of dicts."""
        rows = self._fetch_range(range_notation)
        if not rows:
            return []
        if has_header:
            headers = rows[0]
            data_rows = rows[1:]
        else:
            max_cols = max(len(r) for r in rows)
            headers = [f"col_{i}" for i in range(max_cols)]
            data_rows = rows
        return [_row_to_dict(headers, row) for row in data_rows]


def _row_to_dict(headers: list[str], row: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for i, header in enumerate(headers):
        result[header] = row[i] if i < len(row) else ""
    return result


def _col_letter(n: int) -> str:
    """Convert 1-based column number to A1-notation letter (A, B, … Z, AA, …)."""
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result
