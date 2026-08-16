import sqlite3
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = BASE_DIR / "database"

DB_PATH = DATABASE_DIR / "crime.db"
SCHEMA_PATH = DATABASE_DIR / "schema.sql"
CRIME_CSV = DATA_DIR / "chicago_crime_dataset.csv"


def get_connection():
    """Create and return a SQLite database connection."""
    return sqlite3.connect(DB_PATH)


def create_database():
    """Create the crime table using schema.sql."""
    DATABASE_DIR.mkdir(exist_ok=True)

    connection = get_connection()

    with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
        schema = file.read()

    connection.executescript(schema)
    connection.commit()
    connection.close()


def load_csv_to_database():
    """Load the crime CSV into SQLite if the table is empty."""
    df = pd.read_csv(CRIME_CSV)

    connection = get_connection()

    count = connection.execute(
        "SELECT COUNT(*) FROM crime"
    ).fetchone()[0]

    if count == 0:
        df.to_sql(
            "crime",
            connection,
            if_exists="append",
            index=False
        )
        print(f"{len(df)} crime records inserted into SQLite.")
    else:
        print(f"Database already contains {count} crime records.")

    connection.close()


def initialize_database():
    """Create database and load the initial CSV data."""
    create_database()
    load_csv_to_database()


if __name__ == "__main__":
    initialize_database()