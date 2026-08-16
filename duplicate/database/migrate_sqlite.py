"""One-time, explicit migration of a legacy SQLite crime table to FK-enforced schema.

It never runs when Flask starts. The old table is retained as crime_legacy_backup.
"""
from database import get_connection, SCHEMA_PATH, VIEWS_PATH, load_reference_data

TARGET_COLUMNS = ("id, case_number, date, block, iucr_code, primary_type, description, "
                  "location_desc, arrest, domestic, beat_num, district_code, ward_no, "
                  "community_code, fbi_code, x_coordinate, y_coordinate, year, "
                  "date_of_update, latitude, longitude, location")

def migrate_legacy_schema():
    with get_connection() as con:
        backup_exists = con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='crime_legacy_backup'").fetchone()
        if backup_exists:
            load_reference_data(con)
            if con.execute("SELECT COUNT(*) FROM crime").fetchone()[0]:
                return {"migrated": False, "reason": "backup exists and constrained crime table is already populated"}
            con.execute(f"INSERT INTO crime ({TARGET_COLUMNS}) SELECT id, case_number, date, block, substr('0000' || iucr_code, -4), primary_type, description, location_desc, arrest, domestic, beat_num, district_code, ward_no, community_code, fbi_code, x_coordinate, y_coordinate, year, date_of_update, latitude, longitude, location FROM crime_legacy_backup")
            return {"migrated": True, "crime_rows": con.execute("SELECT COUNT(*) FROM crime").fetchone()[0], "backup_table": "crime_legacy_backup"}
        has_crime = con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='crime'").fetchone()
        if not has_crime:
            con.executescript(SCHEMA_PATH.read_text(encoding="utf-8")); con.executescript(VIEWS_PATH.read_text(encoding="utf-8")); load_reference_data(con)
            return {"migrated": False, "reason": "no legacy crime table"}
        foreign_keys = con.execute("PRAGMA foreign_key_list(crime)").fetchall()
        if foreign_keys:
            return {"migrated": False, "reason": "crime table already has foreign keys"}
        if con.execute("SELECT 1 FROM sqlite_master WHERE name='crime_legacy_backup'").fetchone():
            raise RuntimeError("crime_legacy_backup already exists; review it before retrying migration.")
        con.execute("PRAGMA foreign_keys = OFF")
        con.execute("ALTER TABLE crime RENAME TO crime_legacy_backup")
        con.execute("DROP VIEW IF EXISTS vw_crime_yearly")
        con.execute("DROP VIEW IF EXISTS vw_crime_by_category")
        con.execute("PRAGMA foreign_keys = ON")
        con.executescript(SCHEMA_PATH.read_text(encoding="utf-8")); con.executescript(VIEWS_PATH.read_text(encoding="utf-8")); load_reference_data(con)
        con.execute(f"INSERT INTO crime ({TARGET_COLUMNS}) SELECT id, case_number, date, block, substr('0000' || iucr_code, -4), primary_type, description, location_desc, arrest, domestic, beat_num, district_code, ward_no, community_code, fbi_code, x_coordinate, y_coordinate, year, date_of_update, latitude, longitude, location FROM crime_legacy_backup")
        count = con.execute("SELECT COUNT(*) FROM crime").fetchone()[0]
        return {"migrated": True, "crime_rows": count, "backup_table": "crime_legacy_backup"}

if __name__ == "__main__":
    print(migrate_legacy_schema())
