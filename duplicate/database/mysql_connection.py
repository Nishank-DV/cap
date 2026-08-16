"""MySQL connection/configuration helpers for the Stage 7 data warehouse."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE = "chicago_crime_analytics"


def _load_dotenv_if_present() -> None:
    """Load simple KEY=VALUE entries from a local .env without overriding env vars."""
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def mysql_settings(include_database: bool = True) -> dict[str, Any]:
    """Return Connector/Python settings without exposing credentials in source."""
    _load_dotenv_if_present()
    settings: dict[str, Any] = {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", ""),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "autocommit": False,
    }
    if include_database:
        settings["database"] = os.getenv("MYSQL_DATABASE", DEFAULT_DATABASE)
    return settings


def get_connection(include_database: bool = True):
    """Open a MySQL Connector/Python connection; import lazily for clear setup errors."""
    try:
        import mysql.connector
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "mysql-connector-python is required. Install requirements.txt before using MySQL tools."
        ) from error
    return mysql.connector.connect(**mysql_settings(include_database))
