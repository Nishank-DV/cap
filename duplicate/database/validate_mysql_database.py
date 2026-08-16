"""Post-load MySQL validation, reporting-query checks, and non-destructive persistence test."""

from __future__ import annotations

import json
from uuid import uuid4

from mysql_connection import get_connection


EXPECTED_COUNTS = {"crime": 2000, "iucr_codes": 117, "beat": 198, "district": 22, "ward": 50, "community": 77}
FOREIGN_KEY_CHECKS = {
    "iucr": "SELECT COUNT(*) AS orphan_count FROM crime c LEFT JOIN iucr_codes p ON c.iucr_code = p.iucr_code WHERE p.iucr_code IS NULL",
    "beat": "SELECT COUNT(*) AS orphan_count FROM crime c LEFT JOIN beat p ON c.beat_num = p.beat_num WHERE p.beat_num IS NULL",
    "district": "SELECT COUNT(*) AS orphan_count FROM crime c LEFT JOIN district p ON c.district_code = p.district_code WHERE p.district_code IS NULL",
    "ward": "SELECT COUNT(*) AS orphan_count FROM crime c LEFT JOIN ward p ON c.ward_no = p.ward_no WHERE c.ward_no IS NOT NULL AND p.ward_no IS NULL",
    "community": "SELECT COUNT(*) AS orphan_count FROM crime c LEFT JOIN community p ON c.community_code = p.community_code WHERE c.community_code IS NOT NULL AND p.community_code IS NULL",
}


def validate_database() -> dict:
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        counts = {}
        for table, expected in EXPECTED_COUNTS.items():
            cursor.execute(f"SELECT COUNT(*) AS count FROM `{table}`")
            actual = cursor.fetchone()["count"]
            counts[table] = {"expected": expected, "actual": actual, "valid": actual == expected}
        cursor.execute("SELECT COUNT(DISTINCT id) AS ids, COUNT(DISTINCT case_number) AS cases FROM crime")
        unique_crime = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) AS count FROM crime WHERE ward_no IS NULL")
        ward_nulls = cursor.fetchone()["count"]
        cursor.execute("SELECT COUNT(*) AS count FROM crime WHERE community_code IS NULL")
        community_nulls = cursor.fetchone()["count"]
        foreign_keys = {}
        for name, query in FOREIGN_KEY_CHECKS.items():
            cursor.execute(query)
            foreign_keys[name] = cursor.fetchone()["orphan_count"]
        views = {}
        for view in ("vw_crime_yearly", "vw_crime_by_category"):
            cursor.execute(f"SELECT COUNT(*) AS count FROM `{view}`")
            views[view] = cursor.fetchone()["count"]
        reporting = {}
        for name, query in {
            "crime_count_per_year": "SELECT crime_year, crime_count FROM vw_crime_yearly ORDER BY crime_year",
            "top_five_categories": "SELECT primary_type, crime_count, ROUND(100.0 * crime_count / (SELECT COUNT(*) FROM crime), 2) AS percentage_of_all_crimes FROM vw_crime_by_category ORDER BY crime_count DESC, primary_type LIMIT 5",
            "arrest_count_per_year": "SELECT crime_year, arrest_count FROM vw_crime_yearly ORDER BY crime_year",
        }.items():
            cursor.execute(query)
            reporting[name] = cursor.fetchall()
        return {
            "counts": counts,
            "unique_crime_ids": unique_crime["ids"],
            "unique_case_numbers": unique_crime["cases"],
            "nullable_foreign_key_counts": {"ward_no": ward_nulls, "community_code": community_nulls},
            "foreign_key_orphans": foreign_keys,
            "views": views,
            "reporting": reporting,
        }
    finally:
        cursor.close()
        connection.close()


def persistence_test() -> dict:
    """Insert a copy of one crime, reconnect to verify it, then remove only that test row."""
    connection = get_connection()
    cursor = connection.cursor()
    test_id = None
    try:
        cursor.execute("SELECT MAX(id) + 1, CONCAT('T7', UPPER(SUBSTRING(REPLACE(UUID(), '-', ''), 1, 6))) FROM crime")
        test_id, test_case = cursor.fetchone()
        columns = "date, block, iucr_code, primary_type, description, location_desc, arrest, domestic, beat_num, district_code, ward_no, community_code, fbi_code, x_coordinate, y_coordinate, year, date_of_update, latitude, longitude, location"
        cursor.execute(f"INSERT INTO crime (id, case_number, {columns}) SELECT %s, %s, {columns} FROM crime ORDER BY id LIMIT 1", (test_id, test_case))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

    verify_connection = get_connection()
    verify_cursor = verify_connection.cursor()
    try:
        verify_cursor.execute("SELECT COUNT(*) FROM crime WHERE id = %s", (test_id,))
        persisted = verify_cursor.fetchone()[0] == 1
        verify_cursor.execute("DELETE FROM crime WHERE id = %s", (test_id,))
        verify_connection.commit()
        return {"test_id": test_id, "persisted_after_reconnect": persisted, "test_row_removed": True}
    except Exception:
        verify_connection.rollback()
        raise
    finally:
        verify_cursor.close()
        verify_connection.close()


if __name__ == "__main__":
    print(json.dumps(validate_database(), indent=2, default=str))
