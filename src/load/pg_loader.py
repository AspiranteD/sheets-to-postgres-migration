"""PostgreSQL batch loader with upsert support."""

from __future__ import annotations

from typing import Any, Callable

import psycopg2
import psycopg2.extras


class PgLoader:
    """Batch insert / upsert rows into PostgreSQL."""

    def __init__(
        self,
        dsn: str | None = None,
        connection: Any | None = None,
        batch_size: int = 100,
    ) -> None:
        self.batch_size = batch_size
        self._conn = connection
        self._dsn = dsn

    def _get_connection(self) -> Any:
        if self._conn is None:
            self._conn = psycopg2.connect(self._dsn)
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def load_batch(
        self,
        table: str,
        rows: list[dict[str, Any]],
        progress_callback: Callable[[int], None] | None = None,
    ) -> int:
        """Insert rows in batches. Returns total inserted count."""
        if not rows:
            return 0

        conn = self._get_connection()
        columns = list(rows[0].keys())
        total_inserted = 0

        try:
            with conn.cursor() as cur:
                for start in range(0, len(rows), self.batch_size):
                    batch = rows[start : start + self.batch_size]
                    values_list = [tuple(row.get(c) for c in columns) for row in batch]
                    placeholders = ", ".join(["%s"] * len(columns))
                    cols_str = ", ".join(columns)
                    query = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders})"
                    cur.executemany(query, values_list)
                    total_inserted += len(batch)
                    if progress_callback:
                        progress_callback(total_inserted)
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        return total_inserted

    def load_with_upsert(
        self,
        table: str,
        rows: list[dict[str, Any]],
        conflict_columns: list[str],
        progress_callback: Callable[[int], None] | None = None,
    ) -> dict[str, int]:
        """Insert with ON CONFLICT UPDATE. Returns counts of inserted and updated rows."""
        if not rows:
            return {"inserted": 0, "updated": 0}

        conn = self._get_connection()
        columns = list(rows[0].keys())
        update_cols = [c for c in columns if c not in conflict_columns]
        total_inserted = 0
        total_updated = 0

        try:
            with conn.cursor() as cur:
                for start in range(0, len(rows), self.batch_size):
                    batch = rows[start : start + self.batch_size]

                    for row in batch:
                        values = tuple(row.get(c) for c in columns)
                        placeholders = ", ".join(["%s"] * len(columns))
                        cols_str = ", ".join(columns)
                        conflict_str = ", ".join(conflict_columns)
                        update_str = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)

                        query = (
                            f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders}) "
                            f"ON CONFLICT ({conflict_str}) DO UPDATE SET {update_str} "
                            f"RETURNING (xmax = 0) AS inserted"
                        )
                        cur.execute(query, values)
                        result = cur.fetchone()
                        if result and result[0]:
                            total_inserted += 1
                        else:
                            total_updated += 1

                    if progress_callback:
                        progress_callback(total_inserted + total_updated)

            conn.commit()
        except Exception:
            conn.rollback()
            raise

        return {"inserted": total_inserted, "updated": total_updated}
