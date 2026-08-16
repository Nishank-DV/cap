# Chicago Crime Analytics

> **Current authority (2026-08-16):** The SQLite section below supersedes the historic Stage 7 MySQL narrative retained later in this file as an audit record. MySQL is **NOT** part of the final project architecture. SQLite is the authoritative database.

## Project Audit — Current Baseline

- **Audit date:** 2026-08-16. Verified from files: Flask application, six templates, static assets, SQLite database, data/reference CSVs, Use Cases 1–4 source files, and Stage 8/9 artifacts.
- **Verified completion:** Stage 6.5 has quality reports; Stage 8 has the 2,000-row/26-column processed file; Stage 9 has five non-empty charts and five tables. Previously reported validation counts are not independently treated as current evidence unless reproduced.
- **Application/API:** Flask exposes page routes `/`, `/upload`, `/usecase1`–`/usecase4`; JSON CRUD is `/api/crimes` (GET/POST) and `/api/crimes/<id>` (GET/PUT/DELETE), with reporting/chart endpoints under `/api`.
- **Frontend:** `index`, `upload`, and four use-case templates exist. No redesign was performed.
- **Use cases:** UC1 is ingestion/feature engineering; UC2 is saved analysis/visualisation; UC3 and UC4 files exist, but no new UC3 work was performed in this migration.
- **MySQL audit:** `mysql-connector-python` was removed from requirements. Legacy MySQL-named scripts remain on disk pending permitted deletion, but no Flask/runtime path imports them. Their claims are historical, not current architecture.
- **SQLite status:** `database/crime.db` is authoritative; schema, FK enforcement, explicit loader, controlled legacy migration, and validator are implemented. Legacy `crime_legacy_backup` is intentionally retained after migration.
- **Integrity/API/CRUD:** current validation found 2,000 crimes, no duplicate IDs/case numbers, and no `PRAGMA foreign_key_check` errors. Controlled create/read/update/delete persisted across reconnects and was cleaned up.
- **Known risks/remaining:** the legacy narrative below contains obsolete MySQL claims; physical removal is still required if repository deletion is approved. CSV upload is intentionally retired because replacement would destroy persistence.

## Stage 7 — SQLite Database Architecture & Safe Persistence

MySQL is **NOT** part of the final project architecture. SQLite is the authoritative database.

- **Path:** `database/crime.db`.
- **Tables:** `crime`, `iucr_codes`, `beat`, `district`, `ward`, and `community`. IUCR is TEXT to preserve leading zeroes; ward and community FKs remain nullable.
- **Relationships:** crime references all five dimensions; each SQLite connection enables `PRAGMA foreign_keys = ON`.
- **Initialization:** Flask startup only creates missing schema/views. It never reads a CSV, drops data, replaces a table, or recreates an existing crime table.
- **Loading:** `python database/database.py` is an explicit initial load. It uses `INSERT OR IGNORE` for dimensions and refuses to overwrite a nonempty crime table.
- **Migration:** `python database/migrate_sqlite.py` is explicit and retains `crime_legacy_backup` before converting the legacy unconstrained crime table.
- **Validation:** `python database/validate_sqlite_database.py` checks schema/counts/keys/FKs and runs a temporary CRUD persistence test that removes its own test record.
- **Reporting:** SQLite views `vw_crime_yearly` and `vw_crime_by_category` support yearly counts, top-five category percentages, and yearly arrests.
- **Startup/CRUD safety:** CSV replacement upload is retired with HTTP 409 to prevent accidental data loss. Normal CRUD commits to SQLite and survives application restart.

The remaining Stage 7 text is retained only as a historical record from the previous MySQL-oriented baseline and is not a current claim.

## Functional Integration Audit

- **Use Case 1 — COMPLETE:** `/usecase1` renders a clean “Use Case 1 — Data Ingestion & Cleaning” heading and obtains its quality/validation data from `/api/uc1/summary`.
- **Use Case 2 — COMPLETE:** `/usecase2` now uses the validated Stage 9 output files through project-relative `/outputs/usecase2/...` routes. It exposes trend, category distribution, overall arrest rate, arrest rate by year, heatmap, community areas, most frequent crime, and highest crime month.
- **Use Case 3 — COMPLETE:** `/usecase3` loads `/api/uc3`, which supplies hour intensity, community statistics, IQR outliers, correlation values/matrix, and numerical insights. Its chart/table page uses live payload data rather than Python console output.
- **Use Case 4 — COMPLETE:** `/usecase4` loads live SQLite-derived tables through `/api/uc4/stats` and `/api/uc4/report/...`. `/api/uc4/report/download` returns a generated PDF download.
- **API/CRUD — COMPLETE:** page/API checks returned successful responses; invalid/missing report and crime lookups returned 404. The isolated SQLite CRUD test passed and cleaned up its temporary record.
- **Previous partial-loading risk fixed:** frontend calls to missing UC3 and UC4 endpoints were implemented; UC2’s unrelated old static chart paths were replaced with its validated output paths. Output paths use `BASE_DIR`, not a machine-specific location.
- **Tests performed:** page routes, JSON endpoints, output image route, PDF response, syntax checks, SQLite schema/FK/unique checks, controlled CRUD persistence, source/processed shape checks.
- **Compatibility decision:** existing valid Stage 9 files `crime_by_category.png` and `top_community_areas.png` remain unchanged and are used directly; no cosmetic rename or source/processed-data change was made.

## Final Project Audit & Submission Readiness

### How to run

From the `duplicate` directory, install `requirements.txt` and run `python app/app.py`. The Flask application uses `database/crime.db`; no credentials or MySQL service are required. Source data is `data/chicago_crime_dataset.csv`, processed analysis data is `output/processed/chicago_crime_processed.csv`, and report download is available from Use Case 4.

### Architecture and database

The final architecture is Flask, REST API, HTML/CSS/JavaScript, SQLite, Pandas, NumPy, Matplotlib, Seaborn, and ReportLab. Streamlit is not implemented; Flask is the sole application frontend. SQLite tables are `crime`, `iucr_codes`, `beat`, `district`, `ward`, and `community`, with FK enforcement enabled for every application connection. Application startup does **NOT** replace, delete, or reload the crime table. Explicit loading/migration tools are separate from startup and CRUD changes persist.

MySQL is **NOT** part of the final project architecture. SQLite is the authoritative database. Legacy MySQL-named scripts are retired/historical only; no active Flask runtime path imports them.

### Use cases and UI

- Use Case 1: complete ingestion, cleaning, missingness, feature, and validation presentation.
- Use Case 2: complete Stage 9 trend/category/arrest/heatmap/community analysis with accessible output images.
- Use Case 3: complete hourly intensity, community/IQR outlier, correlation matrix/heatmap, and insight presentation.
- Use Case 4: SQLite yearly/category/arrest reporting and an actual downloadable PDF report.
- Sidebar: Dashboard, Data Management, and consistently labelled Use Case 1–4 navigation with active state.

### Output artifacts

CSV: `crime_count_by_year.csv`, `crime_category_distribution.csv`, `arrest_rate_by_year.csv`, `crime_month_day_heatmap.csv`, and `top_community_areas.csv` in `output/usecase2`.

PNG: `crime_trend_by_year.png`, `top_10_crime_categories.png` (compatibility copy), `arrest_rate_by_year.png`, `crime_month_day_heatmap.png`, and `top_10_community_areas.png` (compatibility copy) in `output/usecase2`.

PDF: `output/insights/chicago_crime_analytics_insights.pdf`; `output/screenshots/frontend_application_screenshots.pdf`; and the generated Use Case 4 download `use_case_4_sqlite_report.pdf`.

The heatmap is calculated by the validated Stage 9 analysis, retained as `crime_month_day_heatmap.csv` and `crime_month_day_heatmap.png`, displayed through `/outputs/usecase2/crime_month_day_heatmap.png`, and remains available after restart.

### Final validation

Final checks passed: source 2,000 × 22; processed 2,000 × 26; SQLite tables/keys/FKs/orphan checks; duplicate checks; controlled create/read/update/delete persistence; two startup safety checks with unchanged counts; all required routes and APIs; UC4 PDF response; five required valid PNG files; heatmap CSV and PNG; Insights PDF; and frontend screenshot PDF.

Source CSV modified: **NO**  
Processed CSV modified: **NO**

## Stage 6.5 — Data Model & Data Quality Lock

### Dataset confirmation

The confirmed assessment dataset is the supplied 2015–2023 Chicago crime dataset. It contains 2,000 rows, 22 columns, and 16 primary crime categories. No source CSV was edited, filtered, or replaced during this stage.

### Profile, missing values, and dates

The master profile found no duplicate rows, IDs, or case numbers; no invalid/missing incident dates; and no date/year mismatches. Eight fields contain documented source nulls, with the largest rate being `location_desc` at 4.70%. **No columns exceeded the >50% missing-value threshold.** The complete data dictionary, samples, types, and profiling results are in [output/data_quality_report.md](output/data_quality_report.md).

### Categorical, numeric, and location quality

Audited categories have no blank strings, leading/trailing whitespace, capitalization variants, or semantic duplicate groups. `arrest` and `domestic` are valid booleans. Numeric key fields are valid non-negative/positive whole-number values where expected; non-null latitude/longitude values fall within a broad Chicago envelope. Missing and incomplete coordinate pairs are retained and documented rather than removed.

### Reference and ward datasets

All six reference files have no full-row duplicates, missing values, or duplicate candidate keys. The 24-row main ward file and 26-row supplemental ward file have compatible schemas, no overlapping ward keys, complete fields, and together provide wards 1–50. All 1,963 non-null crime ward references match that combined set.

### Relationship and key decisions

All non-null supplied crime keys match their candidate parent references: IUCR (24/24 distinct), beat (40/40), district (22/22), ward (50/50), and community (77/77). Proposed keys are `crime.id`, `IUCR_CODE`, `BEAT_NUM`, `DISTRICT_CODE`, `WARD_NO`, and `community_code`; `case_number` is a verified alternate unique key in this extract. `ward_no` and `community_code` should be nullable integer foreign keys in the future physical model.

### Retention and proposed logical model

Source records remain preserved. Transformations—including trimmed/uppercased processing fields, nullable-integer keys, and derived temporal fields—belong only in processing/database layers. The proposed design is `iucr_codes`, `beat`, `district`, `ward`, and `community` one-to-many into `crime`, with indexes on dates, crime type, and relationship keys. Both raw ward imports should be retained with provenance; a derived union can form the `ward` dimension.

### Deliberately postponed / risks

No MySQL migration, schema implementation, views, API integration, frontend redesign, final insights, or PDFs were completed in this stage. Future dataset releases require re-validation of uniqueness, formatting, and relationship coverage. The existing SQLite startup-reset behaviour remains outside this data-model lock.

### Files created or modified

- `README.md` — created because no README existed.
- `output/data_quality_report.md` — human-readable audit.
- `output/data_quality_report.json` — machine-readable summary.

**DATA MODEL STATUS: LOCKED**  
**DATA QUALITY STATUS: LOCKED**

## Stage 7 — MySQL Data Warehouse & Safe Migration

### Database architecture and naming

The new, separate MySQL persistence target is `chicago_crime_analytics`. It uses lower-case singular table names and lower-case snake_case columns: `crime`, `iucr_codes`, `beat`, `district`, `ward`, and `community`. The existing SQLite app remains unchanged during this stage; MySQL is not yet wired into Flask or the frontend.

### Schema, keys, relationships, and indexes

[database/schema.sql](database/schema.sql) defines idempotent InnoDB tables. `crime.id` is the primary key and `case_number` is unique. Dimension primary keys are `iucr_code`, `beat_num`, `district_code`, `ward_no`, and `community_code`. Verified FK candidates are implemented from `crime` to each dimension; `ward_no` and `community_code` remain nullable. Indexes support crime date, primary type, arrest, and every FK column.

### Datatypes and ward provenance

Raw IUCR values include leading-zero codes such as `0110`, so `iucr_code` is `CHAR(4)`, not a numeric field. Case number is `CHAR(8)` based on the verified source, reference/relationship codes use appropriate integer or character types, and geographic values use decimals. `ward` has one record per ward number and a required `source_provenance` of `MAIN` or `SUPPLEMENTAL`; both supplied raw ward CSVs remain unchanged.

### Connection, environment, and initialization safety

[.env.example](.env.example) shows the required `MYSQL_*` settings; no credentials are stored in source. [database/mysql_connection.py](database/mysql_connection.py) reads environment variables (or an untracked local `.env`). [database/init_mysql.py](database/init_mysql.py) only creates missing database objects. It never drops, truncates, replaces, or reloads existing production data during application startup.

### Loading, transactions, and validation

[database/load_mysql_data.py](database/load_mysql_data.py) reads the locked CSV package, preserves nulls and raw source files, creates the 50-row derived ward dimension, and upserts dimensions before crime records. The complete load is transactional: any critical failure rolls back rather than silently skipping records. It reports inserted, updated, and skipped counts.
Parse/load failures include source filename and row number and are written to `output/mysql_load_errors.log`; this log is created only if a load is attempted.

[database/validate_mysql_database.py](database/validate_mysql_database.py) verifies expected counts (including 2,000 crime rows and 50 wards), uniqueness, nullable FK counts, FK-orphan counts, views, and representative reporting queries. Its optional `persistence_test()` inserts a controlled copy of an existing row, reconnects to verify persistence, and removes only the test row.

### Views and reporting queries

[database/views.sql](database/views.sql) defines live MySQL views `vw_crime_yearly` and `vw_crime_by_category`. [database/queries.sql](database/queries.sql) provides data-driven yearly crime counts, top-five categories with percentages, and annual arrest counts.

### SQLite → MySQL migration plan and limitations

OLD: SQLite in `app/app.py`, `database/database.py`, and `usecases/usecase4.py`.  
NEW: independent MySQL schema, loader, views, connector configuration, and validator under `database/`.

The old SQLite implementation was deliberately not deleted or redirected so the existing application is not broken before an integration stage. Its `if_exists="replace"` startup behavior remains a documented SQLite risk and is not used by the MySQL layer.

### Stage 7 verification status

The local environment has no MySQL service, MySQL CLI, Docker runtime, or installed `mysql-connector-python`. Therefore a live connection, schema execution, data load, view/query execution, and mandatory persistence test could not be run here.

- SOURCE CSVs modified: **NO**
- SQLite modified: **NO**
- MySQL implemented: **YES — code and SQL prepared**
- Data loss detected: **NO**
- MYSQL STATUS: **NOT VERIFIED**

Exact blocker: provision a MySQL server, install `mysql-connector-python` from `requirements.txt`, configure non-secret `MYSQL_*` environment values, then run `python database/load_mysql_data.py` and `python database/validate_mysql_database.py` from the `duplicate` directory. Run `persistence_test()` after validation.

### Stage 7 files created or modified

Created: `.env.example`, `.gitignore`, `database/schema.sql`, `database/views.sql`, `database/queries.sql`, `database/mysql_connection.py`, `database/init_mysql.py`, `database/load_mysql_data.py`, and `database/validate_mysql_database.py`.  
Modified: `requirements.txt` and this `README.md`.

## Stage 8 — Use Case 1: Data Ingestion, Cleaning & Feature Engineering

### Objective and source dataset

Use Case 1 is a reusable Pandas/NumPy processing pipeline in [usecases/usecase1.py](usecases/usecase1.py). It loads the locked `data/chicago_crime_dataset.csv` source without editing it, validates the source baseline, creates a separate processed dataset for later use cases, and does not put data-processing logic in `app.py`.

The source baseline was verified at runtime: **2,000 rows**, **22 columns**, 2015–2023. The loader deliberately reads `iucr_code`, `fbi_code`, and `case_number` as strings so code identifiers retain their source representation, including leading-zero IUCR values.

### Loading, inspection, and date processing

`load_data()` checks source path, exact locked row/column counts, and expected schema. `inspect_data()` records column names, dtypes, memory use, and the first ten rows in the data-quality artifact. The source field is named lowercase `date`; in the processed layer it is parsed to datetime, while the raw source CSV remains unchanged. `date_of_update` is also parsed for validation.

The pipeline creates four derived columns only: `Year`, `Month`, `DayOfWeek`, and `Hour`. The existing lowercase source `year` remains retained and is validated against parsed `date`; the new capitalized `Year` follows the required derived-feature naming convention.

### NumPy missingness, cleaning, and code handling

`calculate_missingness()` uses NumPy arrays to calculate missing counts and percentages for every field. No field exceeded 50% missingness, so all fields are preserved. Null location, ward, community, coordinate, and location values remain null in the processed dataset—none are replaced by invented values or fake keys.

Only evidence-based processing occurs: outer whitespace is stripped from selected text categories and codes; no arbitrary case transformation is applied. `iucr_code` is retained as a four-character string (`0110` remains `0110`); code-like nullable numeric fields use Pandas nullable integers. Source `arrest` and `domestic` values were verified as `True`/`False` and are represented as nullable-aware booleans in processing.

### Validation, anomalies, and output artifacts

`validate_processed_data()` verifies source/processed row counts, source-file SHA-256 stability, required derived columns, valid dates, date/year and date-feature consistency, valid hours, duplicate IDs/cases, the >50% rule, and IUCR-leading-zero retention. Basic quality-only anomaly checks found zero invalid dates, invalid broad-range coordinates, non-positive beats/districts, or blank primary-type/description values. Full statistical outlier work remains reserved for Use Case 3.

Created artifacts:

- [output/processed/chicago_crime_processed.csv](output/processed/chicago_crime_processed.csv) — 2,000 rows, 26 columns; the 22 source fields plus `Year`, `Month`, `DayOfWeek`, and `Hour`.
- [output/processed/missing_value_summary.csv](output/processed/missing_value_summary.csv) — NumPy-based missingness results.
- [output/processed/usecase1_data_quality_summary.json](output/processed/usecase1_data_quality_summary.json) — inspection, anomaly, feature, and test evidence.

### Testing performed and results

`run_usecase_1()` was executed successfully. **13/13 tests passed**: source and processed row count, source hash, derived columns, date parsing, year/month/day consistency, hour range, duplicate ID/case checks, missingness threshold, and IUCR leading-zero retention. The processed output contains 10 records with IUCR `0110`.

### Decisions, limitations, and postponed work

Source data is retained unchanged; transformations happen only in the processing layer. The Stage 7 MySQL loader continues to consume the locked raw package, avoiding accidental substitution of a derived CSV before live MySQL validation. No Use Cases 2–4, final CRUD, frontend redesign, final insights, or final PDFs were implemented in this stage.

Files created: `output/processed/chicago_crime_processed.csv`, `output/processed/missing_value_summary.csv`, and `output/processed/usecase1_data_quality_summary.json`.  
Files modified: `usecases/usecase1.py` and this `README.md`.

### FINAL PROJECT REMINDER — MYSQL VERIFICATION

Stage 7 MySQL implementation is prepared but live verification is intentionally postponed because MySQL is not currently provisioned in the development environment.

Before final submission, this MUST be completed:

- install/verify mysql-connector-python;
- provision/start MySQL in the permitted environment;
- configure `.env`;
- initialize MySQL;
- load all datasets;
- validate row counts and foreign keys;
- execute views and reporting queries;
- execute the persistence test;
- verify CRUD persistence; and
- verify application restart does not destroy data.

**USE CASE 1 STATUS: COMPLETE**  
Source CSV modified: **NO**  
Processed dataset created: **YES**  
Tests passed: **13/13**  
MySQL live verification: **NOT PERFORMED**  
README updated: **YES**

## Stage 9 — Use Case 2: Exploratory Analysis & Visualization

### Objective and input dataset

Use Case 2 is implemented in [usecases/usecase2.py](usecases/usecase2.py). It uses only the Stage 8 processed input, [output/processed/chicago_crime_processed.csv](output/processed/chicago_crime_processed.csv), and never modifies that file or the source CSV. Runtime validation confirmed the expected **2,000 rows** and **26 columns** before analysis.

### Analytical approach and data safety

`run_usecase_2()` uses one validated analytical DataFrame for every calculation. It validates parsed dates, `Year`, `Month`, chronological `DayOfWeek`, `Hour`, and understood arrest values. It uses Pandas/NumPy for calculation, Matplotlib for charts, and Seaborn for the month-by-day heatmap. Community analysis excludes null `community_code` values rather than assigning a fake code.

### Metrics and verified results

| Metric | Calculation method | Verified result |
|---|---|---|
| Annual crime trend | `groupby(Year).size()` | Highest: 242 incidents in 2016; lowest: 192 in 2017; 2015-to-2023 change: -4.85%. |
| Category distribution | Valid `primary_type` count / valid category total × 100 | THEFT: 416 incidents, 20.80%. |
| Overall arrest rate | Valid arrest incidents / all incidents × 100 | 596 of 2,000 incidents; 29.80%. This means the percentage of reported crime incidents resulting in an arrest. |
| Annual arrest rate | Annual arrests / annual incidents × 100 | Highest: 33.80% in 2018; lowest: 25.62% in 2016; range: 8.18 percentage points. |
| Highest overall month | `groupby(Month).size()` | Month 10: 190 incidents. |
| Top community area | Non-null `community_code` count | Community Area / Community Code 56: 40 incidents. |

### Graphs

| Graph name | Purpose | Source data | Output path |
|---|---|---|---|
| Crime trend over years | Show reported incident count by year | `Year` | [crime_trend_by_year.png](output/usecase2/crime_trend_by_year.png) |
| Top crime categories | Compare top ten `primary_type` counts | `primary_type` | [crime_by_category.png](output/usecase2/crime_by_category.png) |
| Arrest rate by year | Compare annual percentage of incidents resulting in arrest | `Year`, `arrest` | [arrest_rate_by_year.png](output/usecase2/arrest_rate_by_year.png) |
| Month × day heatmap | Show crime-frequency pattern in chronological calendar order | `Month`, `DayOfWeek` | [crime_month_day_heatmap.png](output/usecase2/crime_month_day_heatmap.png) |
| Top community areas | Compare top ten non-null community codes | `community_code` | [top_community_areas.png](output/usecase2/top_community_areas.png) |

### Analytical tables

- [crime_count_by_year.csv](output/usecase2/crime_count_by_year.csv)
- [crime_category_distribution.csv](output/usecase2/crime_category_distribution.csv)
- [arrest_rate_by_year.csv](output/usecase2/arrest_rate_by_year.csv)
- [crime_month_day_heatmap.csv](output/usecase2/crime_month_day_heatmap.csv)
- [top_community_areas.csv](output/usecase2/top_community_areas.csv)
- [usecase2_summary.json](output/usecase2/usecase2_summary.json)

### Factual observations

- The annual counts vary across the supplied extract; the calculated first-to-last-year change alone does not establish a continuous trend.
- THEFT is the most frequent recorded category in this dataset.
- Annual arrest rates are not identical: the observed maximum-to-minimum range is 8.18 percentage points.
- Month 10 has the highest overall month frequency in this extract.

### Possible business implications

These are investigation prompts, not causal claims or recommendations. The category, community-code, month/day, and annual arrest-rate summaries can help prioritise follow-up questions about data collection, service planning, or resource analysis when combined with context not present in this dataset.

### Testing, decisions, and limitations

**13/13 tests passed.** They reconcile yearly/category/arrest/heatmap/community totals, validate percentages and table sizes, verify all five graphs exist with non-empty files, reject invalid chart values, and confirm the processed input hash is unchanged. Charts were visually checked for readable labels and chronological heatmap ordering.

Created: five PNG graphs, five CSV analytical tables, and `output/usecase2/usecase2_summary.json`.  
Modified: `usecases/usecase2.py` and this `README.md`.

Limitations: category/community results describe only this 2,000-row supplied dataset; no community names were invented or joined. This stage does not make causal conclusions and does not include Use Cases 3/4, dashboard integration, final CRUD, or MySQL verification. Those items remain deliberately postponed.

**USE CASE 2 STATUS: COMPLETE**  
Tests: **13/13 PASSED**  
Graphs: **5/5 GENERATED**  
Tables: **5/5 GENERATED**  
Source CSV modified: **NO**  
Processed CSV modified: **NO**  
MySQL live verification: **NOT PERFORMED**  
README updated: **YES**
