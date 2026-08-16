-- Stage 7 reporting queries. Results are calculated from MySQL tables/views.

-- 1. Crime count per year
SELECT crime_year, crime_count
FROM vw_crime_yearly
ORDER BY crime_year;

-- 2. Top five primary crime types with share of all crimes
SELECT
    primary_type,
    crime_count,
    ROUND(100.0 * crime_count / SUM(crime_count) OVER (), 2) AS percentage_of_all_crimes
FROM vw_crime_by_category
ORDER BY crime_count DESC, primary_type
LIMIT 5;

-- 3. Arrest count per year
SELECT crime_year, arrest_count
FROM vw_crime_yearly
ORDER BY crime_year;
