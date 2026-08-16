from flask import Flask, render_template, request, jsonify
import sqlite3
import sys
import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = BASE_DIR / "database"
DATA_DIR = BASE_DIR / "data"

DB_PATH = DATABASE_DIR / "crime.db"

sys.path.insert(0, str(BASE_DIR))

from usecases.usecase1 import data_model_summary as uc1_data_model_summary


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


# ============================================================
# INITIALIZE SQLITE DATABASE
# ============================================================

def initialize_database():

    print("Creating SQLite database...")

    DATABASE_DIR.mkdir(exist_ok=True)

    csv_path = DATA_DIR / "chicago_crime_dataset.csv"

    if not csv_path.exists():
        print("Crime dataset not found:", csv_path)
        return

    # Load dataset
    df = pd.read_csv(csv_path)

    # --------------------------------------------------------
    # CLEAN DATE COLUMNS
    # --------------------------------------------------------

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    if "date_of_update" in df.columns:
        df["date_of_update"] = pd.to_datetime(
            df["date_of_update"],
            errors="coerce"
        )

    # --------------------------------------------------------
    # CLEAN CATEGORICAL COLUMNS
    # --------------------------------------------------------

    categorical_columns = [
        "block",
        "iucr_code",
        "primary_type",
        "description",
        "location_desc",
        "fbi_code"
    ]

    for column in categorical_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
                .str.upper()
            )

    # --------------------------------------------------------
    # HANDLE MISSING LOCATION DESCRIPTION
    # --------------------------------------------------------

    if "location_desc" in df.columns:

        df["location_desc"] = (
            df["location_desc"]
            .fillna("UNKNOWN")
        )

    # --------------------------------------------------------
    # CREATE FEATURES
    # --------------------------------------------------------

    # The original dataset already has "year",
    # therefore we do NOT create another "Year" column.

    df["Month"] = df["date"].dt.month

    df["DayOfWeek"] = df["date"].dt.day_name()

    # --------------------------------------------------------
    # RECONSTRUCT MISSING LOCATION
    # --------------------------------------------------------

    if all(
        column in df.columns
        for column in [
            "location",
            "latitude",
            "longitude"
        ]
    ):

        mask = (
            df["location"].isna()
            & df["latitude"].notna()
            & df["longitude"].notna()
        )

        df.loc[mask, "location"] = (
            "("
            + df.loc[mask, "latitude"].astype(str)
            + ","
            + df.loc[mask, "longitude"].astype(str)
            + ")"
        )

    # --------------------------------------------------------
    # HANDLE MISSING COORDINATES
    # --------------------------------------------------------

    coordinate_columns = [
        "x_coordinate",
        "y_coordinate",
        "latitude",
        "longitude"
    ]

    for column in coordinate_columns:

        if column in df.columns:

            median_value = df[column].median()

            df[column] = df[column].fillna(
                median_value
            )

    # --------------------------------------------------------
    # CONVERT DATETIME TO SQLITE-SAFE STRINGS
    # --------------------------------------------------------

    df["date"] = df["date"].dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    if "date_of_update" in df.columns:

        df["date_of_update"] = (
            df["date_of_update"]
            .dt.strftime("%Y-%m-%d %H:%M:%S")
        )

    # --------------------------------------------------------
    # CREATE SQLITE DATABASE
    # --------------------------------------------------------

    connection = sqlite3.connect(DB_PATH)

    df.to_sql(
        "crime",
        connection,
        if_exists="replace",
        index=False
    )

    connection.commit()
    connection.close()

    print("SQLite database created successfully.")
    print("Records:", len(df))
    print("Columns:", len(df.columns))


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# ============================================================
# UPLOAD PAGE
# ============================================================

@app.route("/upload")
def upload_page():

    return render_template(
        "upload.html"
    )


# ============================================================
# USE CASE PAGES
# ============================================================

@app.route("/usecase1")
def usecase1():

    return render_template(
        "usecase1.html"
    )


@app.route("/usecase2")
def usecase2():

    return render_template(
        "usecase2.html"
    )


@app.route("/usecase3")
def usecase3():

    return render_template(
        "usecase3.html"
    )


@app.route("/usecase4")
def usecase4():

    return render_template(
        "usecase4.html"
    )


# ============================================================
# REST API - GET CRIMES
# ============================================================

@app.route(
    "/api/crimes",
    methods=["GET"]
)
def get_crimes():

    connection = get_db_connection()

    search = request.args.get(
        "search",
        ""
    ).strip()

    limit = request.args.get(
        "limit",
        100,
        type=int
    )

    offset = request.args.get(
        "offset",
        0,
        type=int
    )

    # Prevent unreasonable values
    limit = max(1, min(limit, 1000))
    offset = max(0, offset)

    if search:

        query = """
        SELECT *
        FROM crime
        WHERE
            CAST(id AS TEXT) LIKE ?
            OR case_number LIKE ?
            OR primary_type LIKE ?
            OR description LIKE ?
            OR block LIKE ?
        ORDER BY id
        LIMIT ? OFFSET ?
        """

        search_value = f"%{search}%"

        rows = connection.execute(
            query,
            (
                search_value,
                search_value,
                search_value,
                search_value,
                search_value,
                limit,
                offset
            )
        ).fetchall()

    else:

        query = """
        SELECT *
        FROM crime
        ORDER BY id
        LIMIT ? OFFSET ?
        """

        rows = connection.execute(
            query,
            (
                limit,
                offset
            )
        ).fetchall()

    total = connection.execute(
        "SELECT COUNT(*) FROM crime"
    ).fetchone()[0]

    connection.close()

    return jsonify({
        "data": [
            dict(row)
            for row in rows
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    })


# ============================================================
# REST API - GET ONE CRIME
# ============================================================

@app.route(
    "/api/crimes/<int:crime_id>",
    methods=["GET"]
)
def get_crime(crime_id):

    connection = get_db_connection()

    row = connection.execute(
        """
        SELECT *
        FROM crime
        WHERE id = ?
        """,
        (crime_id,)
    ).fetchone()

    connection.close()

    if row is None:

        return jsonify({
            "error": "Crime record not found"
        }), 404

    return jsonify(
        dict(row)
    )


# ============================================================
# REST API - CREATE CRIME
# ============================================================

@app.route(
    "/api/crimes",
    methods=["POST"]
)
def create_crime():

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "No JSON data provided"
        }), 400

    required_fields = [
        "id",
        "case_number",
        "date",
        "primary_type"
    ]

    for field in required_fields:

        if field not in data:

            return jsonify({
                "error": f"Missing field: {field}"
            }), 400

    columns = [
        "id",
        "case_number",
        "date",
        "block",
        "iucr_code",
        "primary_type",
        "description",
        "location_desc",
        "arrest",
        "domestic",
        "beat_num",
        "district_code",
        "ward_no",
        "community_code",
        "fbi_code",
        "x_coordinate",
        "y_coordinate",
        "year",
        "date_of_update",
        "latitude",
        "longitude",
        "location",
        "Month",
        "DayOfWeek"
    ]

    values = [
        data.get(column)
        for column in columns
    ]

    placeholders = ", ".join(
        ["?"] * len(columns)
    )

    query = f"""
    INSERT INTO crime
    ({", ".join(columns)})
    VALUES ({placeholders})
    """

    connection = get_db_connection()

    try:

        connection.execute(
            query,
            values
        )

        connection.commit()

    except sqlite3.Error as error:

        connection.close()

        return jsonify({
            "error": str(error)
        }), 400

    connection.close()

    return jsonify({
        "message": "Crime record created successfully"
    }), 201


# ============================================================
# REST API - UPDATE CRIME
# ============================================================

@app.route(
    "/api/crimes/<int:crime_id>",
    methods=["PUT"]
)
def update_crime(crime_id):

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "No JSON data provided"
        }), 400

    allowed_columns = [
        "case_number",
        "date",
        "block",
        "iucr_code",
        "primary_type",
        "description",
        "location_desc",
        "arrest",
        "domestic",
        "beat_num",
        "district_code",
        "ward_no",
        "community_code",
        "fbi_code",
        "x_coordinate",
        "y_coordinate",
        "year",
        "date_of_update",
        "latitude",
        "longitude",
        "location",
        "Month",
        "DayOfWeek"
    ]

    updates = []
    values = []

    for column in allowed_columns:

        if column in data:

            updates.append(
                f'"{column}" = ?'
            )

            values.append(
                data[column]
            )

    if not updates:

        return jsonify({
            "error": "No valid fields to update"
        }), 400

    values.append(
        crime_id
    )

    query = f"""
    UPDATE crime
    SET {", ".join(updates)}
    WHERE id = ?
    """

    connection = get_db_connection()

    try:

        cursor = connection.execute(
            query,
            values
        )

        connection.commit()

    except sqlite3.Error as error:

        connection.close()

        return jsonify({
            "error": str(error)
        }), 400

    if cursor.rowcount == 0:

        connection.close()

        return jsonify({
            "error": "Crime record not found"
        }), 404

    connection.close()

    return jsonify({
        "message": "Crime record updated successfully"
    })


# ============================================================
# REST API - DELETE CRIME
# ============================================================

@app.route(
    "/api/crimes/<int:crime_id>",
    methods=["DELETE"]
)
def delete_crime(crime_id):

    connection = get_db_connection()

    cursor = connection.execute(
        """
        DELETE FROM crime
        WHERE id = ?
        """,
        (crime_id,)
    )

    connection.commit()

    if cursor.rowcount == 0:

        connection.close()

        return jsonify({
            "error": "Crime record not found"
        }), 404

    connection.close()

    return jsonify({
        "message": "Crime record deleted successfully"
    })


# ============================================================
# CSV UPLOAD
# ============================================================

@app.route(
    "/api/upload",
    methods=["POST"]
)
def upload_csv():

    if "file" not in request.files:

        return jsonify({
            "error": "No file uploaded"
        }), 400

    file = request.files["file"]

    if file.filename == "":

        return jsonify({
            "error": "No file selected"
        }), 400

    if not file.filename.lower().endswith(".csv"):

        return jsonify({
            "error": "Only CSV files are allowed"
        }), 400

    try:

        df = pd.read_csv(file)

        required_columns = [
            "id",
            "case_number",
            "date",
            "primary_type"
        ]

        missing_columns = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:

            return jsonify({
                "error": "Missing required columns",
                "columns": missing_columns
            }), 400

        # Clean date columns
        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

        if "date_of_update" in df.columns:

            df["date_of_update"] = pd.to_datetime(
                df["date_of_update"],
                errors="coerce"
            )

        # Create features
        if "Month" not in df.columns:

            df["Month"] = (
                df["date"].dt.month
            )

        if "DayOfWeek" not in df.columns:

            df["DayOfWeek"] = (
                df["date"].dt.day_name()
            )

        # Convert dates for SQLite
        df["date"] = (
            df["date"]
            .dt.strftime("%Y-%m-%d %H:%M:%S")
        )

        if "date_of_update" in df.columns:

            df["date_of_update"] = (
                df["date_of_update"]
                .dt.strftime("%Y-%m-%d %H:%M:%S")
            )

        connection = sqlite3.connect(
            DB_PATH
        )

        df.to_sql(
            "crime",
            connection,
            if_exists="replace",
            index=False
        )

        connection.commit()
        connection.close()

        return jsonify({
            "message": "CSV uploaded successfully",
            "records": len(df),
            "columns": len(df.columns)
        })

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500


# ============================================================
# DASHBOARD STATISTICS
# ============================================================

@app.route(
    "/api/stats",
    methods=["GET"]
)
def get_stats():

    connection = get_db_connection()

    total = connection.execute(
        "SELECT COUNT(*) FROM crime"
    ).fetchone()[0]

    crime_types = connection.execute(
        """
        SELECT COUNT(DISTINCT primary_type)
        FROM crime
        """
    ).fetchone()[0]

    arrests = connection.execute(
        """
        SELECT COALESCE(
            SUM(
                CASE
                    WHEN arrest = 1 THEN 1
                    ELSE 0
                END
            ),
            0
        )
        FROM crime
        """
    ).fetchone()[0]

    domestic = connection.execute(
        """
        SELECT COALESCE(
            SUM(
                CASE
                    WHEN domestic = 1 THEN 1
                    ELSE 0
                END
            ),
            0
        )
        FROM crime
        """
    ).fetchone()[0]

    connection.close()

    return jsonify({
        "total_records": total,
        "unique_crime_types": crime_types,
        "arrests": arrests,
        "domestic_crimes": domestic
    })


# ============================================================
# USE CASE 2 - SUMMARY STATS (charts themselves are static
# matplotlib images generated by usecases/usecase2.py and
# served from /static/charts)
# ============================================================

@app.route(
    "/api/uc2/summary",
    methods=["GET"]
)
def uc2_summary():

    connection = get_db_connection()

    total = connection.execute(
        "SELECT COUNT(*) FROM crime"
    ).fetchone()[0]

    top_crime_row = connection.execute(
        """
        SELECT
            primary_type,
            COUNT(*) AS crime_count
        FROM crime
        GROUP BY primary_type
        ORDER BY crime_count DESC
        LIMIT 1
        """
    ).fetchone()

    arrests = connection.execute(
        """
        SELECT COALESCE(
            SUM(
                CASE
                    WHEN arrest = 1 THEN 1
                    ELSE 0
                END
            ),
            0
        )
        FROM crime
        """
    ).fetchone()[0]

    peak_day_row = connection.execute(
        """
        SELECT
            "DayOfWeek",
            COUNT(*) AS crime_count
        FROM crime
        WHERE "DayOfWeek" IS NOT NULL
        GROUP BY "DayOfWeek"
        ORDER BY crime_count DESC
        LIMIT 1
        """
    ).fetchone()

    connection.close()

    top_crime = (
        top_crime_row["primary_type"]
        if top_crime_row else None
    )

    peak_day = (
        peak_day_row["DayOfWeek"]
        if peak_day_row else None
    )

    arrest_rate = (
        round((arrests / total) * 100, 2)
        if total else 0
    )

    insight = (
        f"{top_crime or 'No data'} is the most frequently "
        f"reported crime, and {peak_day or 'no particular day'} "
        f"sees the highest number of incidents. Roughly "
        f"{arrest_rate}% of all reported crimes resulted in an "
        f"arrest."
    )

    return jsonify({
        "total_records": total,
        "top_crime": top_crime,
        "arrest_rate": arrest_rate,
        "peak_day": peak_day,
        "insight": insight
    })


# ============================================================
# CHART API - CRIMES BY YEAR
# ============================================================

@app.route(
    "/api/charts/yearly",
    methods=["GET"]
)
def yearly_chart():

    connection = get_db_connection()

    rows = connection.execute(
        """
        SELECT
            year,
            COUNT(*) AS crime_count
        FROM crime
        GROUP BY year
        ORDER BY year
        """
    ).fetchall()

    connection.close()

    return jsonify({
        "labels": [
            row["year"]
            for row in rows
        ],
        "values": [
            row["crime_count"]
            for row in rows
        ]
    })


# ============================================================
# CHART API - TOP CRIME TYPES
# ============================================================

@app.route(
    "/api/charts/crime-types",
    methods=["GET"]
)
def crime_type_chart():

    connection = get_db_connection()

    rows = connection.execute(
        """
        SELECT
            primary_type,
            COUNT(*) AS crime_count
        FROM crime
        GROUP BY primary_type
        ORDER BY crime_count DESC
        LIMIT 10
        """
    ).fetchall()

    connection.close()

    return jsonify({
        "labels": [
            row["primary_type"]
            for row in rows
        ],
        "values": [
            row["crime_count"]
            for row in rows
        ]
    })


# ============================================================
# CHART API - ARREST
# ============================================================

@app.route(
    "/api/charts/arrest",
    methods=["GET"]
)
def arrest_chart():

    connection = get_db_connection()

    rows = connection.execute(
        """
        SELECT
            arrest,
            COUNT(*) AS crime_count
        FROM crime
        GROUP BY arrest
        """
    ).fetchall()

    connection.close()

    return jsonify({
        "labels": [
            "Arrest" if row["arrest"] else "No Arrest"
            for row in rows
        ],
        "values": [
            row["crime_count"]
            for row in rows
        ]
    })


# ============================================================
# CHART API - DISTRICT
# ============================================================

@app.route(
    "/api/charts/district",
    methods=["GET"]
)
def district_chart():

    connection = get_db_connection()

    rows = connection.execute(
        """
        SELECT
            district_code,
            COUNT(*) AS crime_count
        FROM crime
        GROUP BY district_code
        ORDER BY crime_count DESC
        """
    ).fetchall()

    connection.close()

    return jsonify({
        "labels": [
            str(row["district_code"])
            for row in rows
        ],
        "values": [
            row["crime_count"]
            for row in rows
        ]
    })


# ============================================================
# USE CASE 1 - LOAD & CLEAN SUMMARY
# ============================================================

@app.route(
    "/api/uc1/summary",
    methods=["GET"]
)
def uc1_summary():

    csv_path = DATA_DIR / "chicago_crime_dataset.csv"

    if not csv_path.exists():
        return jsonify({
            "error": "Dataset not found"
        }), 404

    df = pd.read_csv(csv_path)

    rows, columns = df.shape

    dtypes = {
        column: str(dtype)
        for column, dtype in df.dtypes.items()
    }

    head_preview = df.head(10).astype(str).to_dict(
        orient="records"
    )

    # Missing-value percentage per column (NumPy)
    missing_percentage = (
        (df.isnull().sum() / len(df) * 100)
        .round(2)
    )

    missing_list = [
        {"column": column, "percentage": pct}
        for column, pct in missing_percentage.items()
        if pct > 0
    ]

    high_missing_columns = [
        column
        for column, pct in missing_percentage.items()
        if pct > 50
    ]

    duplicate_records = int(df.duplicated().sum())
    duplicate_ids = int(df["id"].duplicated().sum())

    parsed_dates = pd.to_datetime(
        df["date"], errors="coerce"
    )

    unique_crime_types = int(
        df["primary_type"].nunique()
    )

    # Data model — validates the master dataset against
    # every dependent reference file it joins against.
    try:
        data_model = uc1_data_model_summary(df)
    except Exception as error:
        data_model = []
        print("Data model summary failed:", error)

    return jsonify({
        "rows": int(rows),
        "columns": int(columns),
        "dtypes": dtypes,
        "head_preview": head_preview,
        "missing_values": missing_list,
        "high_missing_columns": high_missing_columns,
        "duplicate_records": duplicate_records,
        "duplicate_ids": duplicate_ids,
        "date_min": str(parsed_dates.min()),
        "date_max": str(parsed_dates.max()),
        "missing_dates": int(parsed_dates.isna().sum()),
        "unique_crime_types": unique_crime_types,
        "data_model": data_model
    })


# ============================================================
# USE CASE 3 - STATISTICAL INSIGHTS SUMMARY
# ============================================================

@app.route(
    "/api/uc3/summary",
    methods=["GET"]
)
def uc3_summary():

    connection = get_db_connection()

    total = connection.execute(
        "SELECT COUNT(*) FROM crime"
    ).fetchone()[0]

    arrests = connection.execute(
        """
        SELECT COALESCE(SUM(
            CASE WHEN arrest = 1 THEN 1 ELSE 0 END
        ), 0)
        FROM crime
        """
    ).fetchone()[0]

    domestic = connection.execute(
        """
        SELECT COALESCE(SUM(
            CASE WHEN domestic = 1 THEN 1 ELSE 0 END
        ), 0)
        FROM crime
        """
    ).fetchone()[0]

    community_rows = connection.execute(
        """
        SELECT
            community_code,
            COUNT(*) AS crime_count
        FROM crime
        WHERE community_code IS NOT NULL
        GROUP BY community_code
        """
    ).fetchall()

    connection.close()

    arrest_rate = round((arrests / total) * 100, 2) if total else 0
    domestic_rate = round((domestic / total) * 100, 2) if total else 0

    counts = np.array([
        row["crime_count"] for row in community_rows
    ])

    if len(counts) > 0:
        mean_crime = float(np.mean(counts))
        std_crime = float(np.std(counts))
        q1 = float(np.percentile(counts, 25))
        q3 = float(np.percentile(counts, 75))
        iqr = q3 - q1
        lower_limit = q1 - (1.5 * iqr)
        upper_limit = q3 + (1.5 * iqr)
        outlier_count = int(
            np.sum(
                (counts < lower_limit) | (counts > upper_limit)
            )
        )
    else:
        mean_crime = std_crime = q1 = q3 = iqr = 0
        lower_limit = upper_limit = 0
        outlier_count = 0

    return jsonify({
        "total_records": total,
        "arrest_rate": arrest_rate,
        "domestic_rate": domestic_rate,
        "community_mean_crime": round(mean_crime, 2),
        "community_std_crime": round(std_crime, 2),
        "community_iqr_lower": round(lower_limit, 2),
        "community_iqr_upper": round(upper_limit, 2),
        "community_outlier_count": outlier_count
    })


# ============================================================
# USE CASE 4 - SQL REPORTING SUMMARY
# ============================================================

@app.route(
    "/api/uc4/summary",
    methods=["GET"]
)
def uc4_summary():

    connection = get_db_connection()

    total = connection.execute(
        "SELECT COUNT(*) FROM crime"
    ).fetchone()[0]

    top5_rows = connection.execute(
        """
        SELECT
            primary_type,
            COUNT(*) AS crime_count
        FROM crime
        GROUP BY primary_type
        ORDER BY crime_count DESC
        LIMIT 5
        """
    ).fetchall()

    yearly_rows = connection.execute(
        """
        SELECT
            year,
            SUM(CASE WHEN arrest = 1 THEN 1 ELSE 0 END) AS arrests,
            COUNT(*) AS total_crimes
        FROM crime
        GROUP BY year
        ORDER BY year
        """
    ).fetchall()

    connection.close()

    top5 = [
        {
            "primary_type": row["primary_type"],
            "crime_count": row["crime_count"],
            "percentage": round(
                (row["crime_count"] / total) * 100, 2
            ) if total else 0
        }
        for row in top5_rows
    ]

    yearly = [
        {
            "year": row["year"],
            "arrests": row["arrests"],
            "total_crimes": row["total_crimes"],
            "arrest_rate": round(
                (row["arrests"] / row["total_crimes"]) * 100, 2
            ) if row["total_crimes"] else 0
        }
        for row in yearly_rows
    ]

    return jsonify({
        "total_records": total,
        "top5_crime_types": top5,
        "arrests_by_year": yearly
    })


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    initialize_database()

    app.run(
        debug=True
    )