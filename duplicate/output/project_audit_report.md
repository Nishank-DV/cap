# Project Audit Report — Current Baseline

Audit date: 2026-08-16

## VERIFIED FROM FILES

- Flask app has six page routes, JSON crime CRUD routes, reporting/chart endpoints, six templates, CSS and JS.
- The original app rebuilt `crime` from CSV using table replacement at startup and upload; this was a persistence/data-loss risk.
- SQLite database was migrated explicitly to `crime`, `iucr_codes`, `beat`, `district`, `ward`, and `community`. Legacy contents remain in `crime_legacy_backup`.
- Current validation: crime 2,000; IUCR 117; beat 198; district 22; ward 50; community 77; duplicate IDs 0; duplicate case numbers 0; FK errors 0.
- The source CSV remains 2,000 rows/22 columns. Processed CSV exists with 2,000 rows/26 columns.
- Stage 9 has five PNG outputs and five CSV output tables. Filenames use `crime_by_category.png` and `top_community_areas.png`, not the two differently named files in the request.
- UC1, UC2, UC3, UC4 source files exist. UC3 was not changed or reimplemented.
- Requirements no longer has a MySQL connector. Existing MySQL-named scripts are not imported by the Flask app.

## PREVIOUSLY REPORTED BUT NOT CURRENTLY VERIFIED

- Historical README claims that Stage 8 and Stage 9 each passed 13/13 checks.
- Historic MySQL schema/loader/validator readiness claims. MySQL is retired and not authoritative.
- Any claim about a live MySQL server or credentials.

## Current architecture and safety

`database/database.py` opens FK-enabled SQLite connections and initializes only missing objects. `database/migrate_sqlite.py` is an explicit, backup-retaining migration. `database/validate_sqlite_database.py` performs schema, key, orphan/FK, and temporary CRUD persistence checks. Flask does not automatically load CSV data; its replacement upload endpoint is retired.

## Contradictions and risks

- Historic README content still discusses MySQL; the new SQLite sections supersede it.
- Legacy MySQL files remain as retired artifacts because deletion was not available in this controlled workspace.
- Requested Stage 9 names `top_10_crime_categories.png` and `top_10_community_areas.png` do not match the verified existing filenames. Existing valid outputs were preserved.
