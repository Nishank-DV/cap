"""Idempotently create the Stage 7 MySQL database, tables, indexes, and views."""

from __future__ import annotations

from pathlib import Path
import re

from mysql_connection import get_connection, mysql_settings


DATABASE_DIR = Path(__file__).resolve().parent


def _statements(path: Path) -> list[str]:
    """Split the project's simple semicolon-terminated SQL files into statements."""
    sql = "\n".join(
        line for line in path.read_text(encoding="utf-8").splitlines()
        if not line.strip().startswith("--")
    )
    return [statement.strip() for statement in sql.split(";") if statement.strip()]


def _run_sql_file(connection, filename: str) -> None:
    cursor = connection.cursor()
    try:
        for statement in _statements(DATABASE_DIR / filename):
            cursor.execute(statement)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def initialize_mysql() -> None:
    """Create only missing objects. Existing rows are never dropped, replaced, or truncated."""
    server_connection = get_connection(include_database=False)
    try:
        database_name = mysql_settings()["database"]
        if not re.fullmatch(r"[A-Za-z0-9_]+", database_name):
            raise ValueError("MYSQL_DATABASE must contain only letters, digits, and underscores.")
        cursor = server_connection.cursor()
        try:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            server_connection.commit()
        finally:
            cursor.close()
    finally:
        server_connection.close()

    connection = get_connection()
    try:
        _run_sql_file(connection, "schema.sql")
        _run_sql_file(connection, "views.sql")
    finally:
        connection.close()


if __name__ == "__main__":
    initialize_mysql()
    print("MySQL schema and views are ready; no existing data was removed.")
