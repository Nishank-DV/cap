# Stage 6.5 — Data Model & Data Quality Lock

## Scope and dataset confirmation

This is an audit and design artifact. No supplied CSV was edited, filtered, deleted, or normalised. The master file is `data/chicago_crime_dataset.csv`: **2,000 rows**, **22 columns**, date range **2015-01-03 23:10 to 2023-12-31 09:44**, and **16** primary crime categories. The supplied 24-row ward file and 26-row supplemental ward file were both retained as source data.

## Master profile and data dictionary

| Column | Pandas physical dtype | Logical type | Null? | Unique count | Potential key / referenced by | Inferred meaning and notes | Sample |
|---|---|---|---:|---:|---|---|---|
| id | int64 | crime-record identifier | No | 2,000 | Candidate PK | Unique in this supplied extract; no DB constraint yet | 10000000 |
| case_number | object | case identifier | No | 2,000 | Alternate candidate key | Unique in this extract | SS442871 |
| date | object | incident datetime | No | 2,000 | — | Parses without failure | 03/04/2022 07:47 |
| block | object | reported block/location text | No | 1,711 | — | Categorical location text | 78XX N PULASKI RD |
| iucr_code | int64 | crime classification code | No | 24 | FK candidate → `IUCR_CODE` | Numeric parsing must preserve supplied code representation | 740 |
| primary_type | object | primary crime category | No | 16 | — | Uppercase categorical value | THEFT |
| description | object | crime-description category | No | 23 | — | Uppercase categorical value | THEFT OVER $500 |
| location_desc | object | location category | Yes, 94 (4.70%) | 20 | — | No blanks; nulls require deliberate processing policy | RESTAURANT |
| arrest | bool | arrest indicator | No | 2 | — | Boolean `True`/`False` | False |
| domestic | bool | domestic-incident indicator | No | 2 | — | Boolean `True`/`False` | False |
| beat_num | int64 | police beat code | No | 40 | FK candidate → `BEAT_NUM` | All non-null values match reference | 212 |
| district_code | int64 | police district code | No | 22 | FK candidate → `DISTRICT_CODE` | All values match reference | 8 |
| ward_no | float64 | ward number | Yes, 37 (1.85%) | 50 | FK candidate → combined `WARD_NO` | Float is caused by nullability; non-null values are whole numbers | 15.0 |
| community_code | float64 | community-area code | Yes, 36 (1.80%) | 77 | FK candidate → `community_code` | Float is caused by nullability; non-null values are whole numbers | 18.0 |
| fbi_code | object | supplied FBI classification code | No | 23 | — | Code-like categorical string | 15 |
| x_coordinate | float64 | projected X coordinate | Yes, 67 (3.35%) | 1,884 | — | Non-null values are whole-number coordinates | 1151489.0 |
| y_coordinate | float64 | projected Y coordinate | Yes, 64 (3.20%) | 1,903 | — | Non-null values are whole-number coordinates | 1867491.0 |
| year | int64 | supplied incident year | No | 9 | Derived/source consistency field | Agrees with parsed `date` for all rows | 2022 |
| date_of_update | object | source-update datetime | No | 2,000 | — | Parses without failure; latest is 2024-01-30 | 03/13/2022 07:47 |
| latitude | float64 | geographic latitude | Yes, 73 (3.65%) | 1,927 | — | 41.69010299–41.98960338 | 41.71608165 |
| longitude | float64 | geographic longitude | Yes, 64 (3.20%) | 1,936 | — | -87.79980749–-87.50028118 | -87.67342345 |
| location | object | supplied coordinate-pair text | Yes, 74 (3.70%) | 1,926 | — | Often corresponds to latitude/longitude; retain source text | (41.71608165, -87.67342345) |

There are **0 duplicate full rows**, **0 duplicate IDs**, and **0 duplicate case numbers**. No column exceeded the **>50% missing-value threshold**.

## Date validation

`date` parsed successfully for all 2,000 rows: zero invalid dates and zero missing dates. The parsed date-year and supplied `year` agree in all 2,000 rows; there are **0 date/year mismatches**. Month values used in processing must be derived from `date`; no standalone source month field exists, so no source month consistency comparison applies. `date_of_update` also parses successfully for all rows (2015-01-18 to 2024-01-30).

## Categorical quality

`primary_type`, `description`, `location_desc`, `iucr_code`, and `fbi_code` have no leading/trailing whitespace, blank strings, capitalization variants, or duplicate categories after trim-and-uppercase comparison. `location_desc` is the only audited categorical field with nulls (94); it has no blank-string substitute. `arrest` and `domestic` have only valid boolean values (`True`, `False`) and no nulls. No unexpected values were found within these source-field domains.

Recommended processing-layer rule only: preserve raw source columns; create derived normalized categorical fields using trim + uppercase for text codes/categories, convert `ward_no` and `community_code` to nullable integers, and retain boolean fields as booleans. Do not overwrite source values.

## Numeric and location quality

| Field | Nulls | Range | Finding |
|---|---:|---|---|
| beat_num | 0 | 111–2511 | Integer; no zero/negative/non-whole values. |
| district_code | 0 | 1–25 | Integer; no zero/negative/non-whole values. |
| ward_no | 37 | 1–50 | All non-null values are whole numbers and match combined wards. |
| community_code | 36 | 1–77 | All non-null values are whole numbers and match communities. |
| x_coordinate | 67 | 1,150,010–1,199,992 | No zero/negative values. |
| y_coordinate | 64 | 1,850,019–1,929,976 | No zero/negative values. |
| latitude | 73 | 41.69010299–41.98960338 | No values outside a broad Chicago geographic envelope. |
| longitude | 64 | -87.79980749–-87.50028118 | Negative values are expected west longitudes; no values outside a broad Chicago envelope. |

Coordinate completeness is imperfect: 1,865 rows have both latitude and longitude, 62 have latitude only, 71 have longitude only, and 2 have neither. This is a source-quality observation, not a reason to delete records.

## Reference dataset profile

| File | Rows | Columns | Key candidate | Key duplicate/nulls | Full-row duplicates | Missing values |
|---|---:|---:|---|---|---:|---|
| `chicago_city_community.csv` | 77 | 7 | `community_code` | 0 / 0 | 0 | None |
| `chicago_district_ps_info.csv` | 22 | 15 | `DISTRICT_CODE` | 0 / 0 | 0 | None |
| `chicago_police_beat_info.csv` | 198 | 4 | `BEAT_NUM` | 0 / 0 | 0 | None |
| `chicago_ward_offices.csv` | 24 | 16 | `WARD_NO` | 0 / 0 | 0 | None |
| `chicago_ward_offices_dummy.csv` | 26 | 16 | `WARD_NO` | 0 / 0 | 0 | None |
| `iucr_codes.csv` | 117 | 4 | `IUCR_CODE` | 0 / 0 | 0 | None |

Each candidate key is non-null and unique in its own supplied file. The two ward datasets have the identical 16-column schema and every field is complete in both files.

### Reference dtypes and distinct-value counts

| File | Pandas dtypes (column: dtype) | Distinct non-null values by column |
|---|---|---|
| `chicago_city_community.csv` | `community_code:int64`, `community_name:object`, `population:int64`, `area_sqmile:float64`, `area_sqkm:float64`, `density_per_sqmi:float64`, `density_per_sqkm:float64` | 77, 77, 77, 72, 72, 77, 77 |
| `chicago_district_ps_info.csv` | `DISTRICT_CODE:int64`, `DISTRICT_NAME:object`, `ADDRESS:object`, `CITY:object`, `STATE:object`, `ZIP:int64`, `WEBSITE:object`, `PHONE:object`, `FAX:object`, `TTY:object`, `X_COORDINATE:float64`, `Y_COORDINATE:float64`, `LATITUDE:float64`, `LONGITUDE:float64`, `LOCATION:object` | 22, 22, 22, 1, 1, 20, 22, 21, 22, 21, 22, 22, 22, 22, 22 |
| `chicago_police_beat_info.csv` | `DISTRICT:int64`, `SECTOR:int64`, `BEAT:int64`, `BEAT_NUM:int64` | 22, 3, 3, 198 |
| `chicago_ward_offices.csv` | `WARD_NO:int64`, 13 office/contact fields as `object`, `ZIPCODE:int64`, `CITY_HALL_ZIPCODE:int64` | 24, 24, 23, 1, 1, 19, 22, 22, 24, 24, 23, 24, 1, 1, 1, 22 |
| `chicago_ward_offices_dummy.csv` | `WARD_NO:int64`, 13 office/contact fields as `object`, `ZIPCODE:int64`, `CITY_HALL_ZIPCODE:int64` | 26 for every column except `CITY`, `STATE`, `CITY_HALL_CITY`, `CITY_HALL_STATE`, and `CITY_HALL_ZIPCODE`, which each have 1 |
| `iucr_codes.csv` | `IUCR_CODE:int64`, `PRIMARY_TYPE:object`, `DESCRIPTION:object`, `INDEX_CODE:object` | 117, 17, 100, 2 |

The ward file column order is identical: `WARD_NO`, `ALDERMAN`, `ADDRESS`, `CITY`, `STATE`, `ZIPCODE`, `WARD_PHONE`, `WARD_FAX`, `EMAIL`, `WEBSITE`, `LOCATION`, `CITY_HALL_ADDRESS`, `CITY_HALL_CITY`, `CITY_HALL_STATE`, `CITY_HALL_ZIPCODE`, `CITY_HALL_PHONE`. In the main ward file the 16 distinct-counts respectively are 24, 24, 23, 1, 1, 19, 22, 22, 24, 24, 23, 24, 1, 1, 1, 22; in the supplemental file every field is complete.

## Ward-file investigation

**MAIN WARD FILE:** 24 distinct wards: 1–20, 24, 25, 28, 32.  
**SUPPLEMENTAL WARD FILE:** 26 distinct wards: 21, 22, 23, 26, 27, 29–31, 33–50.  
**OVERLAPPING KEYS:** none.  
**MISSING KEYS AFTER COMBINATION:** none; combined coverage is ward 1–50, exactly 50 unique wards.  
**MASTER DATA REFERENCES:** Crime rows reference every ward 1–50; 1,963 rows have a non-null ward and all 1,963 match the combined set. 37 rows have null ward values.

Safest database representation: retain both raw import tables with provenance (`source_file`) and load their non-overlapping union into a derived `ward` dimension keyed by `ward_no`. This preserves every supplied field and makes the resulting one-to-many crime-to-ward relationship enforceable without calling a supplied file invalid.

## Relationship and foreign-key candidate analysis

| Relationship | Child → parent | Distinct child / parent | Matching | Unmatched child | Unmatched parent | Type compatibility | Recommendation |
|---|---|---:|---:|---:|---:|---|---|
| IUCR | `crime.iucr_code` → `iucr_codes.IUCR_CODE` | 24 / 117 | 24 (100%) | 0 | 93 | int64 → int64 | Candidate nullable/no-delete FK after source staging. |
| Beat | `crime.beat_num` → `beat.BEAT_NUM` | 40 / 198 | 40 (100%) | 0 | 158 | int64 → int64 | Candidate FK. |
| District | `crime.district_code` → `district.DISTRICT_CODE` | 22 / 22 | 22 (100%) | 0 | 0 | int64 → int64 | Candidate FK. |
| Ward | `crime.ward_no` → combined `ward.WARD_NO` | 50 / 50 | 50 (100%) | 0 | 0 | float-with-null → nullable integer | Candidate nullable FK after explicit type conversion. |
| Community | `crime.community_code` → `community.community_code` | 77 / 77 | 77 (100%) | 0 | 0 | float-with-null → nullable integer | Candidate nullable FK after explicit type conversion. |

The community comparison is 100% only after compatible numeric typing; direct string comparison would incorrectly compare values such as `1.0` and `1` as different. No source values are to be changed.

## Primary-key analysis and proposed logical model

`crime.id` and `crime.case_number` are each non-null and unique in this extract. Use `crime.id` as the proposed business primary key because the existing application already addresses records by `id`; retain a unique constraint/index on `case_number` after official-data revalidation. Reference primary keys are `IUCR_CODE`, `BEAT_NUM`, `DISTRICT_CODE`, `community_code`, and the derived combined `WARD_NO`.

```text
iucr_codes (IUCR_CODE PK)     1 ──< crime (id PK, case_number UQ)
beat       (BEAT_NUM PK)      1 ──< crime
district   (DISTRICT_CODE PK) 1 ──< crime
ward       (WARD_NO PK)       1 ──< crime [ward_no nullable]
community  (community_code PK)1 ──< crime [community_code nullable]
```

Proposed indexes: `crime(date)`, `crime(primary_type)`, `crime(district_code)`, `crime(beat_num)`, `crime(ward_no)`, `crime(community_code)`, and the candidate-FK indexes. This is logical design only; no MySQL schema, view, migration, API, or frontend work was implemented.

## Retention policy, decisions, and risks

- Preserve original ZIP/reference copies and all supplied CSVs unchanged.
- Do not discard rows or columns automatically; no column breaches the >50% rule.
- Perform normalization, null handling, coordinate imputation, and derived `month`/`day_of_week` creation only in a processing/database layer, with raw provenance retained.
- Keep `year` as supplied and validate it against parsed `date`; do not silently overwrite mismatches if future data introduces them.
- Treat nullable ward/community and incomplete coordinate pairs as documented source conditions.

Decisions made: the supplied 2015–2023 dataset is the locked assessment dataset; reference relationships are valid candidates; both ward files are retained and form a complete derived ward dimension.  
Deliberately postponed: MySQL migration, physical schema/constraints, views, API repairs, frontend redesign, and final insights/PDFs.  
Risks: future official data can invalidate observed uniqueness or relationship coverage; numeric CSV parsing can obscure code formatting; existing application code currently mutates/rebuilds its SQLite database and must not be mistaken for the locked source layer.

## Status

**DATA MODEL STATUS: LOCKED** — logical keys, relationships, retention, and the ward representation have been verified against supplied files.  
**DATA QUALITY STATUS: LOCKED** — profiling identified no blocking invalid dates, duplicates, broken non-null reference keys, categorical variants, or >50% missing columns. Documented nulls and incomplete coordinate pairs remain retained source conditions.
