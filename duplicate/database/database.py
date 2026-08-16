"""SQLite-only persistence helpers. Loading is explicit, never Flask startup."""
import sqlite3
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR, DATABASE_DIR = BASE_DIR / "data", BASE_DIR / "database"
DB_PATH = DATABASE_DIR / "crime.db"
SCHEMA_PATH, VIEWS_PATH = DATABASE_DIR / "schema.sql", DATABASE_DIR / "views.sql"

def get_connection():
    DATABASE_DIR.mkdir(exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con

def create_database():
    """Create missing objects only; this never loads, resets, or replaces data."""
    with get_connection() as con:
        con.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        con.executescript(VIEWS_PATH.read_text(encoding="utf-8"))

def _insert(con, table, frame):
    cols = list(frame.columns)
    sql = f"INSERT OR IGNORE INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})"
    con.executemany(sql, [tuple(row[c] for c in cols) for row in frame.where(pd.notna(frame), None).to_dict("records")])

def load_reference_data(con):
    """Idempotent dimension loading; repeat runs cannot duplicate records."""
    iucr = pd.read_csv(DATA_DIR / "iucr_codes.csv", dtype={"IUCR_CODE": str}).rename(columns=str.lower)
    iucr["iucr_code"] = iucr["iucr_code"].str.zfill(4); _insert(con, "iucr_codes", iucr)
    _insert(con, "district", pd.read_csv(DATA_DIR / "chicago_district_ps_info.csv").rename(columns=str.lower))
    beat = pd.read_csv(DATA_DIR / "chicago_police_beat_info.csv").rename(columns=str.lower)
    _insert(con, "beat", beat[["beat_num", "district", "sector", "beat"]].rename(columns={"district": "district_code"}))
    for filename, provenance in (("chicago_ward_offices.csv", "MAIN"), ("chicago_ward_offices_dummy.csv", "SUPPLEMENTAL")):
        ward = pd.read_csv(DATA_DIR / filename).rename(columns=str.lower); ward["source_provenance"] = provenance; _insert(con, "ward", ward)
    _insert(con, "community", pd.read_csv(DATA_DIR / "chicago_city_community.csv").rename(columns=str.lower))

def load_initial_data():
    """Explicit bootstrap loader; refuses to overwrite or mix an existing crime table."""
    create_database()
    with get_connection() as con:
        load_reference_data(con)
        if con.execute("SELECT COUNT(*) FROM crime").fetchone()[0]:
            return {"loaded": False, "reason": "crime table already contains data"}
        crime = pd.read_csv(DATA_DIR / "chicago_crime_dataset.csv", dtype={"iucr_code": str, "fbi_code": str, "case_number": str})
        crime["iucr_code"] = crime["iucr_code"].str.zfill(4)
        for column in ("date", "date_of_update"):
            crime[column] = pd.to_datetime(crime[column], errors="raise").dt.strftime("%Y-%m-%d %H:%M:%S")
        crime["arrest"] = crime["arrest"].astype(int); crime["domestic"] = crime["domestic"].astype(int)
        _insert(con, "crime", crime)
        return {"loaded": True, "crime_rows": con.execute("SELECT COUNT(*) FROM crime").fetchone()[0]}

def initialize_database():
    """Flask compatibility entry point: schema only, no source-data mutation."""
    create_database()

if __name__ == "__main__":
    print(load_initial_data())
