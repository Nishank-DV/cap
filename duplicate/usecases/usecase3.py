"""Use Case 3: Python-generated statistical analysis."""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DATASET = BASE_DIR / "output" / "processed" / "chicago_crime_processed.csv"
OUTPUT_DIR = BASE_DIR / "output" / "usecase3"
EXPECTED_ROWS = 2000


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


def generate_outputs():
    """Calculate UC3 results from processed data and create the required PNG files."""
    df = pd.read_csv(PROCESSED_DATASET)
    if len(df) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} processed rows, found {len(df)}")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if df["date"].isna().any():
        raise ValueError("The processed dataset contains invalid dates.")

    df["Hour"] = df["date"].dt.hour
    df["Year"] = df["date"].dt.year
    df["Month"] = df["date"].dt.month
    hourly_counts = df.groupby("Hour").size().reindex(range(24), fill_value=0)
    community = df.loc[df["community_code"].notna()].copy()
    community["community_code"] = pd.to_numeric(community["community_code"], errors="coerce")
    community_counts = community.dropna(subset=["community_code"]).groupby("community_code").size().sort_index()
    q1 = float(community_counts.quantile(0.25))
    q3 = float(community_counts.quantile(0.75))
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    outliers = community_counts[(community_counts < lower_bound) | (community_counts > upper_bound)]
    numeric_columns = ["Year", "Month", "Hour", "arrest", "domestic", "latitude", "longitude", "x_coordinate", "y_coordinate", "ward_no", "community_code"]
    numeric = df[numeric_columns].apply(pd.to_numeric, errors="coerce")
    correlations = numeric.corr()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.plot(hourly_counts.index, hourly_counts.values, marker="o", linewidth=2, color="#315a8b")
    axis.set(title="Crime Intensity by Time", xlabel="Hour of day", ylabel="Crime count")
    axis.set_xticks(range(24)); axis.grid(axis="y", alpha=0.25)
    figure.tight_layout(); figure.savefig(OUTPUT_DIR / "crime_intensity_by_hour.png", dpi=200); plt.close(figure)

    figure, axis = plt.subplots(figsize=(9, 5))
    axis.boxplot(community_counts.values, vert=False, tick_labels=["Community areas"])
    axis.set(title="Community Area Outliers", xlabel="Crime count per community area")
    figure.tight_layout(); figure.savefig(OUTPUT_DIR / "community_area_outliers.png", dpi=200); plt.close(figure)

    figure, axis = plt.subplots(figsize=(9, 7))
    sns.heatmap(correlations, annot=True, fmt=".2f", cmap="coolwarm", center=0, square=True, ax=axis)
    axis.set_title("Correlation Analysis")
    figure.tight_layout(); figure.savefig(OUTPUT_DIR / "correlation_heatmap.png", dpi=200); plt.close(figure)

    table = community_counts.rename("crime_count").reset_index()
    table["is_iqr_outlier"] = table["community_code"].isin(outliers.index)
    table.to_csv(OUTPUT_DIR / "community_area_outliers.csv", index=False)
    pd.DataFrame([{"mean": community_counts.mean(), "q1": q1, "q3": q3, "iqr": iqr, "lower_bound": lower_bound, "upper_bound": upper_bound}]).to_csv(OUTPUT_DIR / "community_area_iqr_summary.csv", index=False)

    paths = [OUTPUT_DIR / "crime_intensity_by_hour.png", OUTPUT_DIR / "community_area_outliers.png", OUTPUT_DIR / "correlation_heatmap.png"]
    tests = {"input_has_2000_rows": len(df) == EXPECTED_ROWS,
             "hourly_counts_reconcile": int(hourly_counts.sum()) == len(df),
             "community_counts_reconcile": int(community_counts.sum()) == int(df["community_code"].notna().sum()),
             "iqr_values_are_valid": all(np.isfinite(value) for value in [q1, q3, iqr, lower_bound, upper_bound]),
             "correlations_are_calculated": bool(correlations.notna().to_numpy().any()),
             "pngs_exist": all(path.exists() and path.stat().st_size > 0 for path in paths)}
    if not all(tests.values()):
        raise ValueError("UC3 validation failed")
    return q1, q3, iqr, lower_bound, upper_bound, community_counts.mean(), outliers, tests


def application_analysis():
    """Return UC3 analysis for Flask; calculations remain outside the route layer."""
    q1, q3, iqr, lower_bound, upper_bound, mean, outliers, tests = generate_outputs()
    return {
        "mean": round(float(mean), 2), "q1": round(q1, 2), "q3": round(q3, 2),
        "iqr": round(iqr, 2), "lower_bound": round(lower_bound, 2), "upper_bound": round(upper_bound, 2),
        "outliers": [{"community_code": int(code), "crime_count": int(count)} for code, count in outliers.items()],
        "tests": tests,
    }

    # Retained below temporarily from the original implementation; unreachable.
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
