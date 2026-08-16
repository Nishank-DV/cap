-- SQLite reporting views. Safe creation is part of explicit initialization.

CREATE VIEW IF NOT EXISTS vw_crime_yearly AS
SELECT
    year AS crime_year,
    COUNT(*) AS crime_count,
    SUM(CASE WHEN arrest = 1 THEN 1 ELSE 0 END) AS arrest_count
FROM crime
GROUP BY year;

CREATE VIEW IF NOT EXISTS vw_crime_by_category AS
SELECT
    primary_type,
    COUNT(*) AS crime_count,
    SUM(CASE WHEN arrest = 1 THEN 1 ELSE 0 END) AS arrest_count
FROM crime
GROUP BY primary_type;
