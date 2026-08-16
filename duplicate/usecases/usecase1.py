import pandas as pd
import numpy as np
from pathlib import Path
import hashlib
import json
from typing import Any


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output" / "processed"
MASTER_DATASET = DATA_DIR / "chicago_crime_dataset.csv"
EXPECTED_ROWS = 2000
EXPECTED_COLUMNS = 22
REQUIRED_COLUMNS = [
    "id", "case_number", "date", "block", "iucr_code", "primary_type",
    "description", "location_desc", "arrest", "domestic", "beat_num",
    "district_code", "ward_no", "community_code", "fbi_code", "x_coordinate",
    "y_coordinate", "year", "date_of_update", "latitude", "longitude", "location"
]


def _source_hash(path: Path) -> str:
    """Return a content hash used to prove this pipeline did not alter the source CSV."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_data(file_path: Path = MASTER_DATASET) -> pd.DataFrame:
    """Load the locked CSV while preserving leading-zero code values as strings."""
    if not file_path.exists():
        raise FileNotFoundError(f"Use Case 1 source dataset not found: {file_path}")

    df = pd.read_csv(
        file_path,
        dtype={
            "case_number": "string",
            "iucr_code": "string",
            "fbi_code": "string",
        },
    )

    if len(df) != EXPECTED_ROWS or len(df.columns) != EXPECTED_COLUMNS:
        raise ValueError(
            "Locked source baseline mismatch: "
            f"expected {EXPECTED_ROWS} rows and {EXPECTED_COLUMNS} columns; "
            f"received {len(df)} rows and {len(df.columns)} columns."
        )

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    unexpected_columns = [column for column in df.columns if column not in REQUIRED_COLUMNS]
    if missing_columns or unexpected_columns:
        raise ValueError(
            f"Unexpected source schema. Missing: {missing_columns}; unexpected: {unexpected_columns}"
        )
    return df


def inspect_data(df: pd.DataFrame) -> dict[str, Any]:
    """Return serialisable source inspection details without changing the DataFrame."""
    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": list(df.columns),
        "dtypes": {column: str(dtype) for column, dtype in df.dtypes.items()},
        "memory_bytes": int(df.memory_usage(deep=True).sum()),
        "first_10_rows": df.head(10).astype(object).where(pd.notna(df.head(10)), None).to_dict("records"),
    }


def calculate_missingness(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate missingness explicitly with NumPy for every field."""
    missing_count = np.sum(df.isna().to_numpy(), axis=0)
    missing_percentage = (missing_count / len(df)) * 100 if len(df) else np.zeros(len(df.columns))
    return pd.DataFrame(
        {
            "column": df.columns,
            "missing_count": missing_count.astype(int),
            "missing_percentage": np.round(missing_percentage, 2),
        }
    )


def _normalize_text(series: pd.Series) -> pd.Series:
    """Remove only outer whitespace; do not impose an unsupported case transformation."""
    return series.astype("string").str.strip()


def clean_data_for_processing(df: pd.DataFrame) -> pd.DataFrame:
    """Create a processed copy while retaining nulls and source semantics."""
    processed = df.copy()

    # Audit established no case variants; trimming is the only evidence-based text normalization.
    for column in ["primary_type", "description", "location_desc", "fbi_code", "iucr_code"]:
        processed[column] = _normalize_text(processed[column])

    # IUCR is an identifier: preserve the source's four-character representation including leading zeroes.
    processed["iucr_code"] = processed["iucr_code"].str.zfill(4)
    processed["case_number"] = _normalize_text(processed["case_number"])

    # These source fields have whole-number semantics but nulls; nullable integers retain missingness.
    for column in ["beat_num", "district_code", "ward_no", "community_code", "x_coordinate", "y_coordinate"]:
        processed[column] = pd.to_numeric(processed[column], errors="raise").astype("Int64")

    # Source audit verified True/False. Keep booleans as a nullable-aware processing representation.
    for column in ["arrest", "domestic"]:
        values = set(processed[column].dropna().astype(str).unique())
        if not values.issubset({"True", "False"}):
            raise ValueError(f"Unexpected boolean values in {column}: {sorted(values)}")
        processed[column] = processed[column].astype("boolean")

    # Dates are converted only in the processed layer; the source CSV remains unchanged.
    processed["date"] = pd.to_datetime(processed["date"], errors="coerce")
    processed["date_of_update"] = pd.to_datetime(processed["date_of_update"], errors="coerce")
    return processed


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add exactly the required temporal features using the processed `date` column."""
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        raise TypeError("date must be parsed before temporal features are created")
    processed = df.copy()
    processed["Year"] = processed["date"].dt.year.astype("Int64")
    processed["Month"] = processed["date"].dt.month.astype("Int64")
    processed["DayOfWeek"] = processed["date"].dt.day_name().astype("string")
    processed["Hour"] = processed["date"].dt.hour.astype("Int64")
    return processed


def check_basic_anomalies(df: pd.DataFrame) -> dict[str, int]:
    """Report basic data-quality anomalies, reserving statistical outliers for Use Case 3."""
    latitude = df["latitude"]
    longitude = df["longitude"]
    return {
        "invalid_dates": int(df["date"].isna().sum()),
        "invalid_update_dates": int(df["date_of_update"].isna().sum()),
        "date_year_mismatches": int((df["date"].dt.year != df["year"]).sum()),
        "invalid_latitude": int(((latitude < 41) | (latitude > 42.2)).fillna(False).sum()),
        "invalid_longitude": int(((longitude < -88.1) | (longitude > -87.3)).fillna(False).sum()),
        "nonpositive_beat_num": int((df["beat_num"].dropna() <= 0).sum()),
        "nonpositive_district_code": int((df["district_code"].dropna() <= 0).sum()),
        "blank_primary_type": int(df["primary_type"].fillna("").eq("").sum()),
        "blank_description": int(df["description"].fillna("").eq("").sum()),
    }


def validate_processed_data(processed: pd.DataFrame, source_hash_before: str) -> dict[str, Any]:
    """Fail loudly when the locked data-quality baseline is not met."""
    required_features = {"Year", "Month", "DayOfWeek", "Hour"}
    missing_features = sorted(required_features - set(processed.columns))
    missingness = calculate_missingness(processed)
    anomalies = check_basic_anomalies(processed)
    tests = {
        "source_rows_equal_2000": len(processed) == EXPECTED_ROWS,
        "processed_rows_equal_2000": len(processed) == EXPECTED_ROWS,
        "source_hash_unchanged": _source_hash(MASTER_DATASET) == source_hash_before,
        "derived_columns_present": not missing_features,
        "date_successfully_parsed": anomalies["invalid_dates"] == 0,
        "year_matches_date": anomalies["date_year_mismatches"] == 0,
        "month_matches_date": bool((processed["Month"] == processed["date"].dt.month).all()),
        "day_of_week_matches_date": bool((processed["DayOfWeek"] == processed["date"].dt.day_name()).all()),
        "hour_is_valid": bool(processed["Hour"].between(0, 23).all()),
        "no_duplicate_ids": int(processed["id"].duplicated().sum()) == 0,
        "no_duplicate_case_numbers": int(processed["case_number"].duplicated().sum()) == 0,
        "no_columns_over_50_percent_missing": bool((missingness["missing_percentage"] <= 50).all()),
        "iucr_leading_zero_preserved": "0110" in set(processed["iucr_code"].dropna()),
    }
    failed = [name for name, passed in tests.items() if not passed]
    if failed:
        raise ValueError(f"Use Case 1 validation failed: {', '.join(failed)}")
    return {"tests": tests, "anomalies": anomalies, "missingness": missingness}


def save_processed_data(processed: pd.DataFrame, inspection: dict[str, Any], validation: dict[str, Any]) -> dict[str, Path]:
    """Save reproducible, separate processing artifacts; never overwrite source CSVs."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    processed_path = OUTPUT_DIR / "chicago_crime_processed.csv"
    missingness_path = OUTPUT_DIR / "missing_value_summary.csv"
    quality_path = OUTPUT_DIR / "usecase1_data_quality_summary.json"

    processed.to_csv(processed_path, index=False, date_format="%Y-%m-%d %H:%M:%S")
    validation["missingness"].to_csv(missingness_path, index=False)
    quality_summary = {
        "source_dataset": str(MASTER_DATASET.relative_to(BASE_DIR)),
        "processed_dataset": str(processed_path.relative_to(BASE_DIR)),
        "processed_rows": int(len(processed)),
        "processed_columns": list(processed.columns),
        "date_naming_convention": "source/processed incident datetime is `date`; derived fields are `Year`, `Month`, `DayOfWeek`, and `Hour`.",
        "inspection": inspection,
        "anomalies": validation["anomalies"],
        "tests": validation["tests"],
        "columns_over_50_percent_missing": validation["missingness"].loc[
            validation["missingness"]["missing_percentage"] > 50, "column"
        ].tolist(),
    }
    quality_path.write_text(json.dumps(quality_summary, indent=2, default=str), encoding="utf-8")
    return {"processed": processed_path, "missingness": missingness_path, "quality": quality_path}


def run_usecase_1() -> dict[str, Any]:
    """Run the reusable Use Case 1 ingestion, cleaning, feature-engineering, and validation pipeline."""
    source_hash_before = _source_hash(MASTER_DATASET)
    source = load_data()
    inspection = inspect_data(source)
    source_missingness = calculate_missingness(source)
    processed = create_features(clean_data_for_processing(source))
    validation = validate_processed_data(processed, source_hash_before)
    artifacts = save_processed_data(processed, inspection, validation)
    return {
        "inspection": inspection,
        "source_missingness": source_missingness,
        "validation": validation,
        "artifacts": {name: str(path) for name, path in artifacts.items()},
    }


# --------------------------------------------------
# LOAD DATASET
# --------------------------------------------------

def load_dataset(filename):
    file_path = DATA_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return pd.read_csv(file_path)


# --------------------------------------------------
# CLEAN DATA
# --------------------------------------------------

def clean_data(df):

    df = df.copy()

    # Convert date to datetime
    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    # Standardize categorical columns
    categorical_columns = [
        "block",
        "iucr_code",
        "primary_type",
        "description",
        "location_desc",
        "fbi_code"
    ]

    for column in categorical_columns:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
            .str.upper()
        )

    # Handle missing location description
    df["location_desc"] = (
        df["location_desc"]
        .fillna("UNKNOWN")
    )

    # Generate features
    df["year"] = df["date"].dt.year
    df["Month"] = df["date"].dt.month
    df["DayOfWeek"] = df["date"].dt.day_name()

    # Reconstruct missing location using coordinates
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

    # Median imputation for coordinates
    coordinate_columns = [
        "x_coordinate",
        "y_coordinate",
        "latitude",
        "longitude"
    ]

    for column in coordinate_columns:
        median_value = df[column].median()
        df[column] = df[column].fillna(median_value)

    return df


# --------------------------------------------------
# VALIDATE WARDS
# --------------------------------------------------

def validate_ward(df):

    ward_file = DATA_DIR / "chicago_ward_offices.csv"
    dummy_file = DATA_DIR / "chicago_ward_offices_dummy.csv"

    ward_df = pd.concat(
        [
            pd.read_csv(ward_file),
            pd.read_csv(dummy_file)
        ],
        ignore_index=True
    )

    ward_df = ward_df.drop_duplicates(
        subset=["WARD_NO"]
    )

    crime_wards = set(
        df["ward_no"]
        .dropna()
        .unique()
    )

    reference_wards = set(
        ward_df["WARD_NO"]
        .dropna()
        .unique()
    )

    invalid_wards = crime_wards - reference_wards

    return invalid_wards


# --------------------------------------------------
# VALIDATE COMMUNITIES
# --------------------------------------------------

def validate_community(df):

    community_df = load_dataset(
        "chicago_city_community.csv"
    )

    crime_communities = set(
        df["community_code"]
        .dropna()
        .unique()
    )

    reference_communities = set(
        community_df["community_code"]
        .dropna()
        .unique()
    )

    invalid_communities = (
        crime_communities - reference_communities
    )

    return invalid_communities


# --------------------------------------------------
# VALIDATE DISTRICTS
# --------------------------------------------------

def validate_district(df):

    district_df = load_dataset(
        "chicago_district_ps_info.csv"
    )

    crime_districts = set(
        df["district_code"]
        .dropna()
        .unique()
    )

    reference_districts = set(
        district_df["DISTRICT_CODE"]
        .dropna()
        .unique()
    )

    invalid_districts = (
        crime_districts - reference_districts
    )

    return invalid_districts


# --------------------------------------------------
# VALIDATE IUCR CODES
# --------------------------------------------------

def validate_iucr(df):

    iucr_df = load_dataset(
        "iucr_codes.csv"
    )

    crime_iucr = set(
        df["iucr_code"]
        .dropna()
        .astype("string")
        .str.strip()
        .unique()
    )

    reference_iucr = set(
        iucr_df["IUCR_CODE"]
        .dropna()
        .astype("string")
        .str.strip()
        .unique()
    )

    invalid_iucr = crime_iucr - reference_iucr

    return invalid_iucr


# --------------------------------------------------
# VALIDATE POLICE BEATS
# --------------------------------------------------

def validate_beat(df):

    beat_df = load_dataset(
        "chicago_police_beat_info.csv"
    )

    crime_beats = set(
        df["beat_num"]
        .dropna()
        .unique()
    )

    reference_beats = set(
        beat_df["BEAT_NUM"]
        .dropna()
        .unique()
    )

    invalid_beats = crime_beats - reference_beats

    return invalid_beats


# --------------------------------------------------
# DATA MODEL SUMMARY
# --------------------------------------------------
# Describes the master dataset and every dependent
# reference file it joins against, so the relationship
# between chicago_crime_dataset.csv and its lookup
# tables is easy to inspect at a glance.
# --------------------------------------------------

def data_model_summary(df):

    ward_file = DATA_DIR / "chicago_ward_offices.csv"
    dummy_file = DATA_DIR / "chicago_ward_offices_dummy.csv"

    ward_df = pd.concat(
        [
            pd.read_csv(ward_file),
            pd.read_csv(dummy_file)
        ],
        ignore_index=True
    ).drop_duplicates(subset=["WARD_NO"])

    district_df = load_dataset("chicago_district_ps_info.csv")
    community_df = load_dataset("chicago_city_community.csv")
    iucr_df = load_dataset("iucr_codes.csv")
    beat_df = load_dataset("chicago_police_beat_info.csv")

    return [
        {
            "file": "chicago_district_ps_info.csv",
            "role": "District reference",
            "join_key": "district_code → DISTRICT_CODE",
            "rows": int(len(district_df)),
            "columns": int(len(district_df.columns)),
            "invalid_keys": len(validate_district(df))
        },
        {
            "file": "chicago_ward_offices.csv (+ dummy)",
            "role": "Ward reference",
            "join_key": "ward_no → WARD_NO",
            "rows": int(len(ward_df)),
            "columns": int(len(ward_df.columns)),
            "invalid_keys": len(validate_ward(df))
        },
        {
            "file": "iucr_codes.csv",
            "role": "Crime code reference",
            "join_key": "iucr_code → IUCR_CODE",
            "rows": int(len(iucr_df)),
            "columns": int(len(iucr_df.columns)),
            "invalid_keys": len(validate_iucr(df))
        },
        {
            "file": "chicago_city_community.csv",
            "role": "Community area reference",
            "join_key": "community_code → community_code",
            "rows": int(len(community_df)),
            "columns": int(len(community_df.columns)),
            "invalid_keys": len(validate_community(df))
        },
        {
            "file": "chicago_police_beat_info.csv",
            "role": "Police beat reference",
            "join_key": "beat_num → BEAT_NUM",
            "rows": int(len(beat_df)),
            "columns": int(len(beat_df.columns)),
            "invalid_keys": len(validate_beat(df))
        }
    ]


# --------------------------------------------------
# MAIN USE CASE
# --------------------------------------------------

def run_usecase1():

    print("=" * 60)
    print("USE CASE 1 - LOAD AND CLEAN CHICAGO CRIME DATA")
    print("=" * 60)

    # Load
    df = load_dataset(
        "chicago_crime_dataset.csv"
    )

    print("\nOriginal dataset")
    print("Rows:", len(df))
    print("Columns:", len(df.columns))

    # Clean
    df = clean_data(df)

    # Missing-value percentage using NumPy
    missing_percentage = (
        np.sum(df.isnull(), axis=0)
        / len(df)
        * 100
    )

    print("\nMissing-value percentage:")
    print(
        missing_percentage[
            missing_percentage > 0
        ]
    )

    # Duplicate validation
    print("\nDuplicate records:", df.duplicated().sum())
    print(
        "Duplicate IDs:",
        df["id"].duplicated().sum()
    )

    # Date information
    print("\nDate range:")
    print("Minimum:", df["date"].min())
    print("Maximum:", df["date"].max())

    print(
        "Missing dates:",
        df["date"].isna().sum()
    )

    # Crime types
    print(
        "\nUnique crime types:",
        df["primary_type"].nunique()
    )

    # Ward validation
    invalid_wards = validate_ward(df)

    if len(invalid_wards) == 0:
        print(
            "\nWard validation: "
            "All crime ward numbers exist "
            "in the ward reference table."
        )
    else:
        print(
            "\nInvalid wards:",
            sorted(invalid_wards)
        )

    # Community validation
    invalid_communities = validate_community(df)

    if len(invalid_communities) == 0:
        print(
            "Community validation: "
            "All crime community codes exist "
            "in the community reference table."
        )
    else:
        print(
            "Invalid communities:",
            sorted(invalid_communities)
        )

    # District validation
    invalid_districts = validate_district(df)

    if len(invalid_districts) == 0:
        print(
            "District validation: "
            "All crime district codes exist "
            "in the district reference table."
        )
    else:
        print(
            "Invalid districts:",
            sorted(invalid_districts)
        )

    # IUCR validation
    invalid_iucr = validate_iucr(df)

    if len(invalid_iucr) == 0:
        print(
            "IUCR validation: "
            "All crime IUCR codes exist "
            "in the IUCR reference table."
        )
    else:
        print(
            "Invalid IUCR codes:",
            sorted(invalid_iucr)
        )

    # Beat validation
    invalid_beats = validate_beat(df)

    if len(invalid_beats) == 0:
        print(
            "Beat validation: "
            "All crime beat numbers exist "
            "in the beat reference table."
        )
    else:
        print(
            "Invalid beats:",
            sorted(invalid_beats)
        )

    # Final status
    print("\nFINAL")
    print("=" * 60)
    print("Total records:", len(df))
    print("Total columns:", len(df.columns))

    remaining = df.isnull().sum()
    remaining = remaining[remaining > 0]

    print("\nRemaining missing values:")
    print(remaining)

    return df


if __name__ == "__main__":
    result = run_usecase_1()
    print("Use Case 1 completed successfully.")
    print("Artifacts:")
    for name, path in result["artifacts"].items():
        print(f"- {name}: {path}")
