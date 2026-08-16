-- Required Stage 7 MySQL reporting views. These are live views over crime.

CREATE OR REPLACE VIEW vw_crime_yearly AS
SELECT
    year AS crime_year,
    COUNT(*) AS crime_count,
    SUM(CASE WHEN arrest THEN 1 ELSE 0 END) AS arrest_count
FROM crime
GROUP BY year;

CREATE OR REPLACE VIEW vw_crime_by_category AS
SELECT
    primary_type,
    COUNT(*) AS crime_count,
    SUM(CASE WHEN arrest THEN 1 ELSE 0 END) AS arrest_count
FROM crime
GROUP BY primary_type;
