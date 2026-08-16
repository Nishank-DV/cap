import pandas as pd
import numpy as np
from pathlib import Path


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

def load_data():

    file_path = DATA_DIR / "chicago_crime_dataset.csv"

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    return pd.read_csv(file_path)


# --------------------------------------------------
# PREPARE DATA
# --------------------------------------------------

def prepare_data(df):

    df = df.copy()

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df["year"] = df["date"].dt.year
    df["Month"] = df["date"].dt.month
    df["DayOfWeek"] = df["date"].dt.day_name()

    return df


# --------------------------------------------------
# BASIC STATISTICS
# --------------------------------------------------

def crime_statistics(df):

    statistics = {
        "total_crimes": len(df),
        "unique_crime_types": df["primary_type"].nunique(),
        "arrest_count": int(df["arrest"].sum()),
        "domestic_crime_count": int(df["domestic"].sum()),
        "average_latitude": df["latitude"].mean(),
        "average_longitude": df["longitude"].mean()
    }

    return statistics


# --------------------------------------------------
# ARREST RATE
# --------------------------------------------------

def calculate_arrest_rate(df):

    total_crimes = len(df)

    arrests = df["arrest"].sum()

    if total_crimes == 0:
        return 0

    return (arrests / total_crimes) * 100


# --------------------------------------------------
# DOMESTIC CRIME RATE
# --------------------------------------------------

def calculate_domestic_rate(df):

    total_crimes = len(df)

    domestic_crimes = df["domestic"].sum()

    if total_crimes == 0:
        return 0

    return (domestic_crimes / total_crimes) * 100


# --------------------------------------------------
# CRIME TYPE ANALYSIS
# --------------------------------------------------

def crime_type_statistics(df):

    crime_types = (
        df.groupby("primary_type")
        .agg(
            crime_count=("id", "count"),
            arrest_count=("arrest", "sum")
        )
        .sort_values(
            "crime_count",
            ascending=False
        )
    )

    crime_types["arrest_rate"] = (
        crime_types["arrest_count"]
        / crime_types["crime_count"]
        * 100
    )

    return crime_types


# --------------------------------------------------
# YEARLY PATTERN
# --------------------------------------------------

def yearly_pattern(df):

    yearly = (
        df.groupby("year")
        .size()
        .reset_index(name="crime_count")
    )

    yearly["percentage_change"] = (
        yearly["crime_count"]
        .pct_change()
        * 100
    )

    return yearly


# --------------------------------------------------
# DISTRICT ANALYSIS
# --------------------------------------------------

def district_analysis(df):

    districts = (
        df.groupby("district_code")
        .agg(
            crime_count=("id", "count"),
            arrest_count=("arrest", "sum")
        )
        .sort_values(
            "crime_count",
            ascending=False
        )
    )

    districts["arrest_rate"] = (
        districts["arrest_count"]
        / districts["crime_count"]
        * 100
    )

    return districts


# --------------------------------------------------
# OUTLIER DETECTION
# --------------------------------------------------

def detect_outliers(df):

    yearly_counts = (
        df.groupby("year")
        .size()
    )

    q1 = yearly_counts.quantile(0.25)
    q3 = yearly_counts.quantile(0.75)

    iqr = q3 - q1

    lower_limit = q1 - (1.5 * iqr)
    upper_limit = q3 + (1.5 * iqr)

    outliers = yearly_counts[
        (yearly_counts < lower_limit)
        | (yearly_counts > upper_limit)
    ]

    return outliers


# --------------------------------------------------
# CORRELATION ANALYSIS
# --------------------------------------------------

def correlation_analysis(df):

    numeric_columns = [
        "arrest",
        "domestic",
        "beat_num",
        "district_code",
        "ward_no",
        "community_code",
        "x_coordinate",
        "y_coordinate",
        "latitude",
        "longitude"
    ]

    available_columns = [
        column
        for column in numeric_columns
        if column in df.columns
    ]

    return df[available_columns].corr()


# --------------------------------------------------
# MAIN USE CASE
# --------------------------------------------------

def run_usecase3():

    print("=" * 60)
    print("USE CASE 3 - STATISTICAL INSIGHTS & PATTERN DETECTION")
    print("=" * 60)

    df = load_data()
    df = prepare_data(df)

    # Basic statistics
    statistics = crime_statistics(df)

    print("\nBasic Statistics")

    for key, value in statistics.items():
        print(f"{key}: {value}")

    # Rates
    arrest_rate = calculate_arrest_rate(df)
    domestic_rate = calculate_domestic_rate(df)

    print(
        f"\nArrest Rate: {arrest_rate:.2f}%"
    )

    print(
        f"Domestic Crime Rate: {domestic_rate:.2f}%"
    )

    # Crime type analysis
    print("\nCrime Type Statistics")
    print(
        crime_type_statistics(df).head(10)
    )

    # Yearly pattern
    print("\nYearly Pattern")
    print(
        yearly_pattern(df)
    )

    # District analysis
    print("\nDistrict Analysis")
    print(
        district_analysis(df).head(10)
    )

    # Outliers
    print("\nYearly Outliers")
    outliers = detect_outliers(df)

    if len(outliers) == 0:
        print("No yearly outliers detected.")
    else:
        print(outliers)

    # Correlation
    print("\nCorrelation Matrix")
    print(
        correlation_analysis(df)
    )


if __name__ == "__main__":
    run_usecase3()


def application_analysis():
    """Return UC3 analysis for Flask; calculations remain outside the route layer."""
    df = prepare_data(load_data())
    hours = pd.to_datetime(df["date"], errors="coerce").dt.hour.value_counts().sort_index()
    community = df.groupby("community_code").size().dropna().sort_values(ascending=False)
    q1, q3 = community.quantile(.25), community.quantile(.75)
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outliers = community[(community < lower) | (community > upper)]
    numeric = df[["latitude", "longitude", "x_coordinate", "y_coordinate", "ward_no", "community_code"]].apply(pd.to_numeric, errors="coerce")
    corr = numeric.corr().round(3).fillna(0)
    monthly = df.groupby("Month").size().reindex(range(1, 13), fill_value=0)
    district = df.groupby("district_code").size().sort_values(ascending=False)
    arrest_rate = (df.assign(arrest=df["arrest"].astype(int)).groupby("year")["arrest"].mean() * 100).round(2)
    return {
        "total_records": int(len(df)), "unique_crime_types": int(df.primary_type.nunique()),
        "monthly_average": round(float(monthly.mean()), 2), "anomalies": int(len(outliers)),
        "hour_labels": [int(x) for x in hours.index], "hour_values": [int(x) for x in hours.values],
        "community_labels": [str(int(x)) for x in community.head(10).index], "community_values": [int(x) for x in community.head(10).values],
        "outliers": [{"community_code": int(k), "crime_count": int(v)} for k, v in outliers.items()],
        "correlation_labels": list(corr.columns), "correlation_matrix": corr.values.tolist(),
        "correlations": {"latitude_longitude": float(corr.loc["latitude", "longitude"]), "x_y": float(corr.loc["x_coordinate", "y_coordinate"]), "ward_community": float(corr.loc["ward_no", "community_code"])},
        "month_labels": [str(x) for x in monthly.index], "month_values": [int(x) for x in monthly.values],
        "concentration_labels": [str(int(x)) for x in community.head(10).index], "concentration_values": [int(x) for x in community.head(10).values],
        "arrest_rate_labels": [str(int(x)) for x in arrest_rate.index], "arrest_rate_values": [float(x) for x in arrest_rate.values],
        "district_labels": [str(int(x)) for x in district.head(10).index], "district_values": [int(x) for x in district.head(10).values],
        "anomalies_list": [{"category": "Community area", "value": int(v), "expected_range": f"{lower:.1f}–{upper:.1f}", "status": "Potential outlier"} for _, v in outliers.items()],
        "insight": f"Hourly activity peaks at {int(hours.idxmax())}:00. {len(outliers)} community areas fall outside the IQR-based expected range."
    }
