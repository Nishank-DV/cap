import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import hashlib
import json
from typing import Any


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHART_DIR = BASE_DIR / "app" / "static" / "charts"
PROCESSED_DATASET = BASE_DIR / "output" / "processed" / "chicago_crime_processed.csv"
EDA_OUTPUT_DIR = BASE_DIR / "output" / "usecase2"
EXPECTED_ROWS = 2000
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTH_ORDER = list(range(1, 13))
REQUIRED_ANALYTICAL_COLUMNS = ["date", "Year", "Month", "DayOfWeek", "Hour", "primary_type", "arrest", "community_code"]

CHART_DIR.mkdir(parents=True, exist_ok=True)


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_processed_data(file_path: Path = PROCESSED_DATASET) -> pd.DataFrame:
    """Load the Stage 8 processed dataset without modifying it."""
    if not file_path.exists():
        raise FileNotFoundError(
            f"Use Case 2 requires the Stage 8 processed dataset: {file_path}"
        )
    df = pd.read_csv(
        file_path,
        dtype={"case_number": "string", "iucr_code": "string", "fbi_code": "string"},
    )
    missing = [column for column in REQUIRED_ANALYTICAL_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Processed dataset is missing required columns: {missing}")
    if len(df) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} processed rows; found {len(df)}")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def prepare_analytical_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and create analytical-only representations needed by every UC2 metric."""
    analytical = df.copy()
    if analytical["date"].isna().any():
        raise ValueError("Processed dataset contains unparseable incident dates.")
    if not analytical["Year"].between(2015, 2023).all():
        raise ValueError("Processed dataset contains invalid Year values.")
    if not analytical["Month"].between(1, 12).all():
        raise ValueError("Processed dataset contains Month values outside 1–12.")
    if not analytical["DayOfWeek"].isin(DAY_ORDER).all():
        raise ValueError("Processed dataset contains unexpected DayOfWeek values.")
    if not analytical["Hour"].between(0, 23).all():
        raise ValueError("Processed dataset contains invalid Hour values.")

    value_map = {True: True, False: False, 1: True, 0: False, "True": True, "False": False, "1": True, "0": False}
    normalized_arrest = analytical["arrest"].map(value_map)
    if normalized_arrest.isna().any():
        unexpected = sorted(analytical.loc[normalized_arrest.isna(), "arrest"].astype(str).unique())
        raise ValueError(f"Unexpected arrest values: {unexpected}")
    analytical["_arrest_boolean"] = normalized_arrest.astype(bool)
    return analytical


def get_crime_counts_by_year(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("Year", as_index=False)
        .size()
        .rename(columns={"size": "crime_count"})
        .sort_values("Year")
    )


def get_category_distribution(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    valid = df.loc[df["primary_type"].notna() & df["primary_type"].astype("string").str.strip().ne("")]
    total_valid = len(valid)
    distribution = (
        valid.groupby("primary_type", as_index=False)
        .size()
        .rename(columns={"size": "crime_count"})
        .sort_values(["crime_count", "primary_type"], ascending=[False, True])
    )
    distribution["percentage_of_valid_records"] = distribution["crime_count"] / total_valid * 100
    return distribution, distribution.head(10).copy()


def calculate_arrest_rate(df: pd.DataFrame) -> dict[str, float | int]:
    total = len(df)
    arrested = int(df["_arrest_boolean"].sum())
    return {
        "total_incidents": total,
        "arrested_incidents": arrested,
        "not_arrested_incidents": total - arrested,
        "arrest_rate_percentage": float(arrested / total * 100) if total else 0.0,
    }


def get_arrest_rate_by_year(df: pd.DataFrame) -> pd.DataFrame:
    annual = (
        df.groupby("Year", as_index=False)
        .agg(total_incidents=("id", "size"), arrests=("_arrest_boolean", "sum"))
        .sort_values("Year")
    )
    annual["arrests"] = annual["arrests"].astype(int)
    annual["arrest_rate_percentage"] = annual["arrests"] / annual["total_incidents"] * 100
    return annual


def get_month_day_heatmap(df: pd.DataFrame) -> pd.DataFrame:
    return pd.crosstab(df["Month"], df["DayOfWeek"]).reindex(index=MONTH_ORDER, columns=DAY_ORDER, fill_value=0)


def get_top_communities(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    valid = df.loc[df["community_code"].notna()].copy()
    valid["community_code"] = valid["community_code"].astype("Int64")
    all_counts = (
        valid.groupby("community_code", as_index=False)
        .size()
        .rename(columns={"size": "crime_count"})
        .sort_values(["crime_count", "community_code"], ascending=[False, True])
    )
    return all_counts, all_counts.head(10).copy()


def _save_figure(figure: plt.Figure, filename: str) -> Path:
    EDA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = EDA_OUTPUT_DIR / filename
    figure.tight_layout()
    figure.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(figure)
    return path


def plot_crime_trend(yearly: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(yearly["Year"], yearly["crime_count"], marker="o", linewidth=2, color="#315a8b")
    ax.set(title="Reported Crime Incidents by Year", xlabel="Year", ylabel="Number of reported incidents")
    ax.set_xticks(yearly["Year"])
    ax.grid(axis="y", alpha=0.25)
    return _save_figure(fig, "crime_trend_by_year.png")


def plot_top_categories(top_categories: pd.DataFrame) -> Path:
    chart = top_categories.sort_values("crime_count")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(chart["primary_type"], chart["crime_count"], color="#527d55")
    ax.set(title="Top 10 Reported Crime Categories", xlabel="Number of reported incidents", ylabel="Primary crime category")
    return _save_figure(fig, "crime_by_category.png")


def plot_arrest_rate_by_year(annual: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(annual["Year"], annual["arrest_rate_percentage"], marker="o", linewidth=2, color="#a34d44")
    ax.set(title="Arrest Rate by Year", xlabel="Year", ylabel="Arrest rate (% of reported incidents)")
    ax.set_xticks(annual["Year"])
    ax.grid(axis="y", alpha=0.25)
    return _save_figure(fig, "arrest_rate_by_year.png")


def plot_month_day_heatmap(heatmap: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(11, 7))
    sns.heatmap(heatmap, annot=True, fmt="d", cmap="Blues", linewidths=0.4, ax=ax)
    ax.set(title="Reported Crime Frequency by Month and Day of Week", xlabel="Day of week", ylabel="Month")
    return _save_figure(fig, "crime_month_day_heatmap.png")


def plot_top_communities(top_communities: pd.DataFrame) -> Path:
    chart = top_communities.sort_values("crime_count")
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(chart["community_code"].astype(str), chart["crime_count"], color="#7b5aa6")
    ax.set(title="Top 10 Community Areas by Reported Crime", xlabel="Number of reported incidents", ylabel="Community Area / Community Code")
    return _save_figure(fig, "top_community_areas.png")


def _factual_insights(yearly: pd.DataFrame, categories: pd.DataFrame, annual_arrest: pd.DataFrame, heatmap: pd.DataFrame, communities: pd.DataFrame, arrest: dict[str, float | int]) -> dict[str, str]:
    first, last = yearly.iloc[0], yearly.iloc[-1]
    trend_change = (last["crime_count"] - first["crime_count"]) / first["crime_count"] * 100
    highest_month = heatmap.sum(axis=1).idxmax()
    highest_month_count = int(heatmap.sum(axis=1).max())
    highest_arrest = annual_arrest.loc[annual_arrest["arrest_rate_percentage"].idxmax()]
    lowest_arrest = annual_arrest.loc[annual_arrest["arrest_rate_percentage"].idxmin()]
    top_category = categories.iloc[0]
    top_community = communities.iloc[0]
    return {
        "crime_trend": f"The highest annual incident count was {int(yearly['crime_count'].max())} in {int(yearly.loc[yearly['crime_count'].idxmax(), 'Year'])}; the lowest was {int(yearly['crime_count'].min())} in {int(yearly.loc[yearly['crime_count'].idxmin(), 'Year'])}. The first-to-last-year change is {trend_change:.2f}%.",
        "category_distribution": f"{top_category['primary_type']} is the most frequent category with {int(top_category['crime_count'])} incidents ({top_category['percentage_of_valid_records']:.2f}% of valid category records).",
        "overall_arrest_rate": f"{arrest['arrest_rate_percentage']:.2f}% of reported crime incidents resulted in an arrest ({arrest['arrested_incidents']} of {arrest['total_incidents']}).",
        "arrest_rate_by_year": f"The highest annual arrest rate was {highest_arrest['arrest_rate_percentage']:.2f}% in {int(highest_arrest['Year'])}; the lowest was {lowest_arrest['arrest_rate_percentage']:.2f}% in {int(lowest_arrest['Year'])}, a range of {highest_arrest['arrest_rate_percentage'] - lowest_arrest['arrest_rate_percentage']:.2f} percentage points.",
        "month_day_heatmap": f"Overall month {int(highest_month)} has the highest reported incident frequency with {highest_month_count} incidents.",
        "community_areas": f"Community Area / Community Code {int(top_community['community_code'])} has the highest reported incident count among non-null community codes ({int(top_community['crime_count'])}).",
    }


def validate_eda_results(df: pd.DataFrame, yearly: pd.DataFrame, categories: pd.DataFrame, arrest: dict[str, float | int], annual_arrest: pd.DataFrame, heatmap: pd.DataFrame, all_communities: pd.DataFrame, top_categories: pd.DataFrame, top_communities: pd.DataFrame, graph_paths: dict[str, Path], processed_hash: str) -> dict[str, bool]:
    """Explicit reconciliation checks prevent silently corrupted analytical output."""
    numeric_tables = [yearly["crime_count"], categories["crime_count"], categories["percentage_of_valid_records"], annual_arrest["total_incidents"], annual_arrest["arrests"], annual_arrest["arrest_rate_percentage"], heatmap.to_numpy().ravel(), all_communities["crime_count"]]
    tests = {
        "input_dataset_exists": PROCESSED_DATASET.exists(),
        "input_has_2000_rows": len(df) == EXPECTED_ROWS,
        "year_counts_reconcile": int(yearly["crime_count"].sum()) == len(df),
        "category_counts_reconcile": int(categories["crime_count"].sum()) == int(df["primary_type"].notna().sum()),
        "category_percentages_approximately_100": bool(np.isclose(categories["percentage_of_valid_records"].sum(), 100.0)),
        "arrest_counts_reconcile": int(arrest["arrested_incidents"] + arrest["not_arrested_incidents"]) == int(arrest["total_incidents"]),
        "annual_arrests_reconcile": int(annual_arrest["arrests"].sum()) == int(arrest["arrested_incidents"]),
        "heatmap_total_reconciles": int(heatmap.to_numpy().sum()) == int(df[["Month", "DayOfWeek"]].dropna().shape[0]),
        "community_counts_reconcile": int(all_communities["crime_count"].sum()) == int(df["community_code"].notna().sum()),
        "top_tables_have_at_most_10_rows": len(top_categories) <= 10 and len(top_communities) <= 10,
        "all_expected_graphs_exist": all(path.exists() and path.stat().st_size > 0 for path in graph_paths.values()),
        "no_nan_or_invalid_chart_values": all(np.isfinite(np.asarray(values, dtype=float)).all() for values in numeric_tables),
        "processed_dataset_unchanged": _file_hash(PROCESSED_DATASET) == processed_hash,
    }
    failed = [name for name, passed in tests.items() if not passed]
    if failed:
        raise ValueError(f"Use Case 2 validation failed: {', '.join(failed)}")
    return tests


def run_usecase_2() -> dict[str, Any]:
    """Run the complete, reproducible exploratory analysis from Stage 8 output."""
    processed_hash = _file_hash(PROCESSED_DATASET)
    analytical = prepare_analytical_dataframe(load_processed_data())
    yearly = get_crime_counts_by_year(analytical)
    categories, top_categories = get_category_distribution(analytical)
    arrest = calculate_arrest_rate(analytical)
    annual_arrest = get_arrest_rate_by_year(analytical)
    heatmap = get_month_day_heatmap(analytical)
    all_communities, top_communities = get_top_communities(analytical)

    EDA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    table_paths = {
        "yearly": EDA_OUTPUT_DIR / "crime_count_by_year.csv",
        "categories": EDA_OUTPUT_DIR / "crime_category_distribution.csv",
        "annual_arrest": EDA_OUTPUT_DIR / "arrest_rate_by_year.csv",
        "month_day": EDA_OUTPUT_DIR / "crime_month_day_heatmap.csv",
        "communities": EDA_OUTPUT_DIR / "top_community_areas.csv",
    }
    yearly.to_csv(table_paths["yearly"], index=False)
    categories.to_csv(table_paths["categories"], index=False)
    annual_arrest.to_csv(table_paths["annual_arrest"], index=False)
    heatmap.to_csv(table_paths["month_day"])
    top_communities.to_csv(table_paths["communities"], index=False)

    graph_paths = {
        "crime_trend": plot_crime_trend(yearly),
        "category_distribution": plot_top_categories(top_categories),
        "arrest_rate_by_year": plot_arrest_rate_by_year(annual_arrest),
        "month_day_heatmap": plot_month_day_heatmap(heatmap),
        "community_areas": plot_top_communities(top_communities),
    }
    tests = validate_eda_results(analytical, yearly, categories, arrest, annual_arrest, heatmap, all_communities, top_categories, top_communities, graph_paths, processed_hash)
    insights = _factual_insights(yearly, categories, annual_arrest, heatmap, top_communities, arrest)
    summary_path = EDA_OUTPUT_DIR / "usecase2_summary.json"
    summary_path.write_text(json.dumps({"arrest_metric": arrest, "insights": insights, "tests": tests, "graphs": {name: str(path.relative_to(BASE_DIR)) for name, path in graph_paths.items()}, "tables": {name: str(path.relative_to(BASE_DIR)) for name, path in table_paths.items()}}, indent=2), encoding="utf-8")
    return {"arrest": arrest, "insights": insights, "tests": tests, "graph_paths": graph_paths, "table_paths": table_paths, "summary_path": summary_path}


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
# CRIME TREND BY YEAR
# --------------------------------------------------

def crime_trend_by_year(df):

    yearly_crimes = (
        df.groupby("year")
        .size()
        .reset_index(name="crime_count")
    )

    plt.figure(figsize=(10, 6))

    plt.plot(
        yearly_crimes["year"],
        yearly_crimes["crime_count"],
        marker="o"
    )

    plt.title("Crime Trend by Year")
    plt.xlabel("Year")
    plt.ylabel("Number of Crimes")
    plt.xticks(yearly_crimes["year"])

    plt.tight_layout()

    plt.savefig(
        CHART_DIR / "crime_trend.png",
        dpi=300
    )

    plt.close()

    return yearly_crimes


# --------------------------------------------------
# TOP CRIME TYPES
# --------------------------------------------------

def top_crime_types(df):

    top_crimes = (
        df["primary_type"]
        .value_counts()
        .head(10)
        .sort_values()
    )

    plt.figure(figsize=(10, 6))

    top_crimes.plot(
        kind="barh"
    )

    plt.title("Top 10 Crime Types")
    plt.xlabel("Number of Crimes")
    plt.ylabel("Crime Type")

    plt.tight_layout()

    plt.savefig(
        CHART_DIR / "top_crime_types.png",
        dpi=300
    )

    plt.close()

    return top_crimes


# --------------------------------------------------
# ARREST ANALYSIS
# --------------------------------------------------

def arrest_analysis(df):

    arrest_counts = (
        df["arrest"]
        .value_counts()
    )

    plt.figure(figsize=(8, 6))

    arrest_counts.plot(
        kind="bar"
    )

    plt.title("Arrest Distribution")
    plt.xlabel("Arrest")
    plt.ylabel("Number of Crimes")

    plt.xticks(
        [0, 1],
        ["No Arrest", "Arrest"]
    )

    plt.tight_layout()

    plt.savefig(
        CHART_DIR / "arrest_distribution.png",
        dpi=300
    )

    plt.close()

    return arrest_counts


# --------------------------------------------------
# CRIMES BY DAY OF WEEK
# --------------------------------------------------

def crimes_by_day(df):

    days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday"
    ]

    day_counts = (
        df["DayOfWeek"]
        .value_counts()
        .reindex(days)
    )

    plt.figure(figsize=(10, 6))

    day_counts.plot(
        kind="bar"
    )

    plt.title("Crimes by Day of Week")
    plt.xlabel("Day")
    plt.ylabel("Number of Crimes")

    plt.xticks(rotation=30)

    plt.tight_layout()

    plt.savefig(
        CHART_DIR / "crimes_by_day.png",
        dpi=300
    )

    plt.close()

    return day_counts


# --------------------------------------------------
# MONTHLY CRIME DISTRIBUTION
# --------------------------------------------------

def crimes_by_month(df):

    month_counts = (
        df.groupby("Month")
        .size()
    )

    plt.figure(figsize=(10, 6))

    month_counts.plot(
        kind="bar"
    )

    plt.title("Crime Distribution by Month")
    plt.xlabel("Month")
    plt.ylabel("Number of Crimes")

    plt.xticks(
        range(12),
        [
            "Jan", "Feb", "Mar", "Apr",
            "May", "Jun", "Jul", "Aug",
            "Sep", "Oct", "Nov", "Dec"
        ],
        rotation=30
    )

    plt.tight_layout()

    plt.savefig(
        CHART_DIR / "crimes_by_month.png",
        dpi=300
    )

    plt.close()

    return month_counts


# --------------------------------------------------
# MAIN USE CASE
# --------------------------------------------------

def run_usecase2():

    print("=" * 60)
    print("USE CASE 2 - EXPLORATORY ANALYSIS & VISUALIZATION")
    print("=" * 60)

    df = load_data()
    df = prepare_data(df)

    yearly = crime_trend_by_year(df)
    top_crimes = top_crime_types(df)
    arrests = arrest_analysis(df)
    days = crimes_by_day(df)
    months = crimes_by_month(df)

    print("\nCrime trend by year:")
    print(yearly)

    print("\nTop 10 crime types:")
    print(top_crimes.sort_values(ascending=False))

    print("\nArrest distribution:")
    print(arrests)

    print("\nCrimes by day:")
    print(days)

    print("\nCrimes by month:")
    print(months)

    print("\nCharts saved to:")
    print(CHART_DIR)


if __name__ == "__main__":
    result = run_usecase_2()
    print("Use Case 2 completed successfully.")
    print(f"Tests: {sum(result['tests'].values())}/{len(result['tests'])} passed")
    print("Artifacts:")
    for name, path in {**result["table_paths"], **result["graph_paths"]}.items():
        print(f"- {name}: {path}")
