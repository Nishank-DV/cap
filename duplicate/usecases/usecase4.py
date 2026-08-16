import sqlite3
import pandas as pd
from pathlib import Path


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = BASE_DIR / "database"

DB_PATH = DATABASE_DIR / "crime.db"


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

def get_connection():
    return sqlite3.connect(DB_PATH)


# --------------------------------------------------
# INITIALIZE DATABASE
# --------------------------------------------------

def initialize_database():

    connection = get_connection()

    schema_path = DATABASE_DIR / "schema.sql"

    with open(
        schema_path,
        "r",
        encoding="utf-8"
    ) as file:
        schema = file.read()

    connection.executescript(schema)

    connection.commit()
    connection.close()


# --------------------------------------------------
# LOAD DATA INTO SQLITE
# --------------------------------------------------

def load_data():

    csv_path = DATA_DIR / "chicago_crime_dataset.csv"

    df = pd.read_csv(csv_path)

    connection = get_connection()

    existing_records = connection.execute(
        "SELECT COUNT(*) FROM crime"
    ).fetchone()[0]

    if existing_records == 0:

        df.to_sql(
            "crime",
            connection,
            if_exists="append",
            index=False
        )

        print(
            f"{len(df)} records inserted into SQLite."
        )

    else:

        print(
            f"Database already contains "
            f"{existing_records} records."
        )

    connection.close()


# --------------------------------------------------
# SQL QUERY HELPER
# --------------------------------------------------

def run_query(query):

    connection = get_connection()

    result = pd.read_sql_query(
        query,
        connection
    )

    connection.close()

    return result


# --------------------------------------------------
# TOTAL RECORDS
# --------------------------------------------------

def total_records():

    query = """
    SELECT COUNT(*) AS total_records
    FROM crime;
    """

    return run_query(query)


# --------------------------------------------------
# CRIMES BY YEAR
# --------------------------------------------------

def crimes_by_year():

    query = """
    SELECT
        year,
        COUNT(*) AS crime_count
    FROM crime
    GROUP BY year
    ORDER BY year;
    """

    return run_query(query)


# --------------------------------------------------
# TOP CRIME TYPES
# --------------------------------------------------

def top_crime_types():

    query = """
    SELECT
        primary_type,
        COUNT(*) AS crime_count
    FROM crime
    GROUP BY primary_type
    ORDER BY crime_count DESC
    LIMIT 10;
    """

    return run_query(query)


# --------------------------------------------------
# DISTRICT REPORT
# --------------------------------------------------

def district_report():

    query = """
    SELECT
        district_code,
        COUNT(*) AS crime_count,
        SUM(arrest) AS arrests
    FROM crime
    GROUP BY district_code
    ORDER BY crime_count DESC;
    """

    return run_query(query)


# --------------------------------------------------
# ARREST REPORT
# --------------------------------------------------

def arrest_report():

    query = """
    SELECT
        arrest,
        COUNT(*) AS crime_count
    FROM crime
    GROUP BY arrest
    ORDER BY arrest DESC;
    """

    return run_query(query)


# --------------------------------------------------
# DOMESTIC CRIME REPORT
# --------------------------------------------------

def domestic_report():

    query = """
    SELECT
        domestic,
        COUNT(*) AS crime_count
    FROM crime
    GROUP BY domestic
    ORDER BY domestic DESC;
    """

    return run_query(query)


# --------------------------------------------------
# COMMUNITY REPORT
# --------------------------------------------------

def community_report():

    query = """
    SELECT
        community_code,
        COUNT(*) AS crime_count
    FROM crime
    WHERE community_code IS NOT NULL
    GROUP BY community_code
    ORDER BY crime_count DESC
    LIMIT 10;
    """

    return run_query(query)


# --------------------------------------------------
# MAIN USE CASE
# --------------------------------------------------

def run_usecase4():

    print("=" * 60)
    print("USE CASE 4 - SQLITE DATABASE REPORTING")
    print("=" * 60)

    # Create table
    initialize_database()

    # Load CSV if database is empty
    load_data()

    print("\nTotal Records")
    print(total_records())

    print("\nCrimes by Year")
    print(crimes_by_year())

    print("\nTop Crime Types")
    print(top_crime_types())

    print("\nDistrict Report")
    print(district_report())

    print("\nArrest Report")
    print(arrest_report())

    print("\nDomestic Crime Report")
    print(domestic_report())

    print("\nTop Communities")
    print(community_report())


if __name__ == "__main__":
    run_usecase4()


def reporting_data():
    """SQLite reporting payload used by the Flask UC4 page and PDF download."""
    from database.database import get_connection
    with get_connection() as con:
        yearly = [dict(r) for r in con.execute("SELECT crime_year, crime_count, arrest_count FROM vw_crime_yearly ORDER BY crime_year")]
        top = [dict(r) for r in con.execute("SELECT primary_type, crime_count, ROUND(100.0 * crime_count / (SELECT COUNT(*) FROM crime), 2) AS percentage FROM vw_crime_by_category ORDER BY crime_count DESC LIMIT 5")]
        total = con.execute("SELECT COUNT(*) FROM crime").fetchone()[0]
        types = con.execute("SELECT COUNT(DISTINCT primary_type) FROM crime").fetchone()[0]
    return {"total_records": total, "unique_crime_types": types, "yearly": yearly, "top_categories": top,
            "interpretation": f"The database contains {total:,} incidents across {types} recorded crime categories."}
