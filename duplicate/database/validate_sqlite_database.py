"""Read-only database checks plus a controlled CRUD persistence test."""
from database import get_connection, initialize_database

def validate():
    initialize_database()
    with get_connection() as con:
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        required = {"crime", "iucr_codes", "beat", "district", "ward", "community"}
        missing = sorted(required - tables)
        counts = {table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in required if table in tables}
        duplicate_ids = con.execute("SELECT COUNT(*) - COUNT(DISTINCT id) FROM crime").fetchone()[0]
        duplicate_cases = con.execute("SELECT COUNT(*) - COUNT(DISTINCT case_number) FROM crime").fetchone()[0]
        fk_errors = con.execute("PRAGMA foreign_key_check").fetchall()
        return {"missing_tables": missing, "counts": counts, "duplicate_ids": duplicate_ids,
                "duplicate_case_numbers": duplicate_cases, "foreign_key_errors": len(fk_errors),
                "valid": not missing and counts.get("crime") == 2000 and not duplicate_ids and not duplicate_cases and not fk_errors}

def crud_persistence_test():
    """Insert, read, update, delete a temporary record; no production record is touched."""
    test_id, test_case = 987654321, "TEST0001"
    with get_connection() as con:
        con.execute("DELETE FROM crime WHERE id = ?", (test_id,))
        parent = con.execute("SELECT iucr_code, beat_num, district_code, ward_no, community_code FROM crime LIMIT 1").fetchone()
        con.execute("INSERT INTO crime (id,case_number,date,block,iucr_code,primary_type,description,location_desc,arrest,domestic,beat_num,district_code,ward_no,community_code,fbi_code,year,date_of_update) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (test_id,test_case,"2023-01-01 00:00:00","TEST BLOCK",parent[0],"TEST","Controlled persistence test",None,0,0,parent[1],parent[2],parent[3],parent[4],"00",2023,"2023-01-01 00:00:00"))
    with get_connection() as con:
        created = con.execute("SELECT primary_type FROM crime WHERE id = ?", (test_id,)).fetchone()[0] == "TEST"
        con.execute("UPDATE crime SET description = ? WHERE id = ?", ("Updated controlled test", test_id))
    with get_connection() as con:
        updated = con.execute("SELECT description FROM crime WHERE id = ?", (test_id,)).fetchone()[0] == "Updated controlled test"
        con.execute("DELETE FROM crime WHERE id = ?", (test_id,))
        deleted = con.execute("SELECT 1 FROM crime WHERE id = ?", (test_id,)).fetchone() is None
    return {"create_read": created, "update": updated, "delete": deleted, "persisted_across_reconnect": created and updated}

if __name__ == "__main__":
    print(validate())
    print(crud_persistence_test())
