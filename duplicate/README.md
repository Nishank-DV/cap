# Chicago Crime Analytics Capstone

## 1. Project Overview

This Flask application analyzes a supplied 2,000-record Chicago crime dataset. It provides data-quality processing, Python-generated visualizations, SQLite reporting, CRUD record management, and a downloadable PDF report.

## 2. Technology Stack

Python, Flask, SQLite (`sqlite3`), Pandas, NumPy, Matplotlib, Seaborn, ReportLab, HTML, CSS, and JavaScript.

**MySQL is NOT part of the final project architecture. SQLite is the authoritative database.**

## 3. Dataset

The source is `data/chicago_crime_dataset.csv` with 2,000 records and 22 columns. Use Case 1 produces `output/processed/chicago_crime_processed.csv` with 26 columns, adding `Year`, `Month`, `DayOfWeek`, and `Hour`. Neither protected CSV is modified by the application.

Reference files retained in `data/` are `chicago_district_ps_info.csv`, `chicago_ward_offices.csv`, `iucr_codes.csv`, `chicago_city_community.csv`, and `chicago_police_beat_info.csv`.

## 4. SQLite Database

The authoritative database is `database/crime.db`. It contains `crime`, `iucr_codes`, `beat`, `district`, `ward`, and `community`. Primary keys and foreign keys are enforced on application connections with `PRAGMA foreign_keys = ON`; case numbers are unique. Application startup does not replace, reset, or reload the crime table. Loading is explicit, and CRUD records persist across restarts.

## 5. Use Cases

### Use Case 1

Loads and validates the protected source, parses dates, calculates missing values, cleans categorical fields, preserves IUCR leading zeroes, creates temporal features, and validates duplicates. The page displays the first ten processed rows and missing-value results.

### Use Case 2

Uses one processed analytical DataFrame to generate yearly crime trends, category counts and percentages, arrest outcomes, a Month × DayOfWeek Seaborn heatmap, and top community-area charts. Answers to the trend, category, arrest consistency, and highest-month questions are calculated from the data.

### Use Case 3

Python generates hourly crime intensity, a community-area box plot with mean/Q1/Q3/IQR bounds and outliers, and a calculated geographic/administrative correlation heatmap. Outputs are stored in `output/usecase3/`.

### Use Case 4

SQLite-compatible views and queries provide crime counts per year, top-five crime types with percentages, and arrest counts per year. ReportLab generates the downloadable PDF report from current SQLite results.

## 6. Project Structure

`app/` contains Flask routes and templates; `database/` contains SQLite schema/helpers/validation; `usecases/` contains Python analytics; `data/` contains protected source/reference CSVs; `output/` contains generated tables, charts, and reports.

## 7. Installation (Windows PowerShell)

```powershell
cd duplicate
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 8. Database Initialization

Run `python database\database.py` only when an explicit initial load is required. It is idempotent and refuses to mix data into an already populated crime table. Normal Flask startup only creates missing schema/views.

## 9. Run the Application

From the `duplicate` directory:

```powershell
python app\app.py
```

Open `http://127.0.0.1:5000/`.

## 10. Validation

Run `python database\validate_sqlite_database.py` for schema, row-count, foreign-key, uniqueness, and controlled CRUD persistence checks. Run `python usecases\usecase2.py` to regenerate UC2 outputs and request `/api/uc3` to regenerate UC3 outputs.

## 11. Safety Rules

Startup never replaces tables, deletes records, reloads CSV files, or resets CRUD changes. The source and processed CSVs are protected inputs.

## 12. Limitations

Results describe only this supplied 2,000-record extract and do not establish causal explanations. Community analysis uses actual community codes and does not invent names.
