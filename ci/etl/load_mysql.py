from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


TABLE_KEYS = {
    "pr_ai_metrics": ("repo", "pr_id"),
    "commit_ai_metrics": ("commit_sha",),
    "audit_queue": ("repo", "pr_id"),
    "audit_log": ("id",),
}


def connect():
    import pymysql

    return pymysql.connect(
        host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        user=os.environ.get("MYSQL_USER", "ai_metrics"),
        password=os.environ.get("MYSQL_PASSWORD", "ai_metrics"),
        database=os.environ.get("MYSQL_DATABASE", "ai_metrics"),
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
    )


def upsert_rows(connection: Any, table: str, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    keys = TABLE_KEYS.get(table)
    if not keys:
        raise ValueError(f"unknown table: {table}")
    columns = list(rows[0].keys())
    placeholders = ", ".join(["%s"] * len(columns))
    column_sql = ", ".join(f"`{column}`" for column in columns)
    update_columns = [column for column in columns if column not in keys]
    update_sql = ", ".join(f"`{column}` = VALUES(`{column}`)" for column in update_columns)
    sql = f"INSERT INTO `{table}` ({column_sql}) VALUES ({placeholders})"
    if update_sql:
        sql += f" ON DUPLICATE KEY UPDATE {update_sql}"
    values = [tuple(row.get(column) for column in columns) for row in rows]
    with connection.cursor() as cursor:
        cursor.executemany(sql, values)
    connection.commit()
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Load normalized AI metrics JSON into MySQL.")
    parser.add_argument("--table", required=True, choices=sorted(TABLE_KEYS))
    parser.add_argument("--input", required=True)
    args = parser.parse_args()

    rows = json.loads(Path(args.input).read_text(encoding="utf-8"))
    with connect() as connection:
        count = upsert_rows(connection, args.table, rows)
    print(f"loaded {count} rows into {args.table}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
